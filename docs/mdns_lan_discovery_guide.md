# DinoRoar 局域网服务发现技术指南（单端口 mDNS + Avahi 组播反射规范）

本指南详细记录了 DinoRoar 项目在局域网零配置自动服务发现方面的演进历程、架构拓扑、服务端实现、宿主机 Docker 组播反射配置、Android 客户端标准化对接规范以及核心踩坑排障经验，作为双端协同开发的标准化参考基线。

---

## 1. 架构演进与方案选型

### 1.1 历史方案演进

| 演进阶段 | 发现机制 | 网络拓扑与端口 | 优势 | 缺陷与痛点 |
| :--- | :--- | :--- | :--- | :--- |
| **阶段一（旧方案）** | **私有 UDP Socket 广播** | Web 业务端口 `8080` + UDP 发现端口 `8090` | 实现简单直观，无特殊依赖 | 1. 占用双端口，暴露额外安全面；<br>2. Android 端需申请 `MulticastLock`，易被手机省电策略杀死；<br>3. Docker 容器必须显式开放 `8090:8090/udp`；<br>4. 私有明文字符串协议，非业界标准。 |
| **阶段二（现行标准）** | **标准 mDNS (DNS-SD) + Avahi 组播反射** | **单端口**：仅对外暴露 Web 业务端口（如 `8080`），无额外 UDP 端口 | 1. 符合 RFC 6762 / 6763 行业标准；<br>2. Android 原生 `NsdManager` 零权限平滑集成；<br>3. 宿主机 Avahi 跨网桥反射，容器与物理局域网无缝打通；<br>4. 统一单端口部署与管理。 | - |

---

## 2. 整体架构与网络拓扑

在 Docker 容器化部署场景中，mDNS 组播包（`224.0.0.251:5353`）默认无法跨越 Docker 默认网桥与物理网络。本项目通过**固定网桥名 + Avahi Reflector 组播反射器**实现无缝打通：

```
┌────────────────────────────────────────────────────────────────────────┐
│                         Android 客户端 (App)                            │
│  • 使用 Android 原生 android.net.nsd.NsdManager                         │
│  • 发现服务类型: "_dinoroar._tcp"                                      │
│  • 解析 TXT 记录与 A 记录，获取宿主机通告 IP (如 192.168.1.100) 与端口 (8080) │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                  mDNS 组播查询 / 响应 (224.0.0.251:5353)
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ 宿主机 (Linux / Debian / Ubuntu / CentOS)                              │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ 宿主机服务: avahi-daemon (开启 enable-reflector=yes)               │  │
│  │ allow-interfaces = <物理上行网卡(如 eth0)>, br-dinoroar          │  │
│  │ 作用: 自动在物理局域网与 Docker 容器网桥间双向反射 mDNS 报文          │  │
│  └────────────────────────────────▲─────────────────────────────────┘  │
│                                   │                                    │
│  ┌────────────────────────────────▼─────────────────────────────────┐  │
│  │ Docker 专属网桥: br-dinoroar (dinoroar_mdns 网络)                │  │
│  └────────────────────────────────▲─────────────────────────────────┘  │
│                                   │                                    │
│  ┌────────────────────────────────┴─────────────────────────────────┐  │
│  │ Docker 业务容器: dinoroar-app                                    │  │
│  │  • Python zeroconf 广播 ServiceInfo ("_dinoroar._tcp.local.")    │  │
│  │  • 仅暴露单一 Web HTTP 端口: 0.0.0.0:8080 -> 8080                │  │
│  │  • 携带 TXT 属性: host, mappedPort, url, version, path           │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 服务端实现规范

### 3.1 广播器核心代码结构

服务端通过 [`backend/app/services/mdns.py`](file:///e:/code/DinoRoar/backend/app/services/mdns.py) 中的 `ServiceDiscoveryBroadcaster` 统一管理生命周期：

- **服务类型（Service Type）**：`_dinoroar._tcp.local.`
- **服务实例名（Instance Name）**：`DinoRoar-Server._dinoroar._tcp.local.`
- **TXT 扩展属性（Properties）**：
  ```python
  properties = {
      b"host": host_ip.encode("utf-8"),
      b"mappedPort": str(port).encode("utf-8"),
      b"url": f"http://{host_ip}:{port}".encode("utf-8"),
      b"version": b"1.0",
      b"path": b"/api",
  }
  ```
- **主机别名（Server Domain）**：`dinoroar-server.local.`

### 3.2 动态重新通告机制

当管理员在系统设置中调整了服务器 IP 或对外映射端口时，必须支持热重载广播，避免产生脏数据：

```python
# 重新注册流程：先优雅解绑旧服务，再用新参数注册
broadcaster.start(new_host, new_port)
```

---

## 4. 宿主机部署与 Avahi 配置规范

### 4.1 Docker Compose 网络与端口定义

在 [`docker-compose.yml`](file:///e:/code/DinoRoar/docker-compose.yml) 中，业务容器仅需映射 Web 端口，并挂载到专用 mDNS 网桥网络：

```yaml
version: '3.8'

services:
  app:
    image: dinoroar-app:latest
    container_name: dinoroar-app
    restart: unless-stopped
    ports:
      - "${WEB_PORT:-8080}:8080" # 仅暴露单一业务端口
    networks:
      - dinoroar_net
      - dinoroar_mdns

networks:
  dinoroar_net:
    name: dinoroar_net
    driver: bridge
  dinoroar_mdns:
    name: dinoroar_mdns
    driver: bridge
    driver_opts:
      com.docker.network.bridge.name: br-dinoroar # 固定网桥名称为 br-dinoroar
```

### 4.2 宿主机自动化配置脚本

项目提供自动化配置脚本 [`scripts/setup_avahi_dinoroar.sh`](file:///e:/code/DinoRoar/scripts/setup_avahi_dinoroar.sh)。在宿主机上以 `root` 权限执行：

```bash
sudo bash scripts/setup_avahi_dinoroar.sh
```

**该脚本的核心动作**：
1. 安装 `avahi-daemon` 与 `avahi-utils`；
2. 预创建 Docker 网络 `dinoroar_mdns` 并绑定物理网桥 `br-dinoroar`；
3. 自动探测宿主机的默认上行物理网卡（如 `eth0`、`enp3s0`）；
4. 配置 `/etc/avahi/avahi-daemon.conf`：
   ```ini
   [server]
   use-ipv4=yes
   use-ipv6=no
   allow-interfaces=eth0,br-dinoroar

   [reflector]
   enable-reflector=yes
   ```
5. 重启并启用 `avahi-daemon` 守护进程。

---

## 5. Android 客户端标准化对接规范

Android 客户端无需申请任何底层 Socket 权限，使用 Android 官方提供的 `android.net.nsd.NsdManager` 进行零配置服务发现。

### 5.1 基础配置与权限

在 `AndroidManifest.xml` 中声明基本网络权限：
```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
<uses-permission android:name="android.permission.ACCESS_WIFI_STATE" />
```

### 5.2 Kotlin 实现示例 (`NsdDiscoveryHelper.kt`)

```kotlin
package com.dinoroar.app.network

import android.content.Context
import android.net.nsd.NsdManager
import android.net.nsd.NsdServiceInfo
import android.util.Log

class NsdDiscoveryHelper(context: Context) {
    private val TAG = "NsdDiscoveryHelper"
    private val SERVICE_TYPE = "_dinoroar._tcp."
    private val nsdManager = context.getSystemService(Context.NSD_SERVICE) as NsdManager
    private var discoveryListener: NsdManager.DiscoveryListener? = null
    private var isDiscovering = false

    data class DiscoveredServer(
        val name: String,
        val host: String,
        val port: Int,
        val baseUrl: String
    )

    fun startDiscovery(onServerFound: (DiscoveredServer) -> Unit) {
        if (isDiscovering) return

        discoveryListener = object : NsdManager.DiscoveryListener {
            override fun onDiscoveryStarted(regType: String) {
                Log.d(TAG, "mDNS 发现服务已启动: $regType")
                isDiscovering = true
            }

            override fun onServiceFound(serviceInfo: NsdServiceInfo) {
                Log.d(TAG, "发现 mDNS 服务: ${serviceInfo.serviceName}, 类型: ${serviceInfo.serviceType}")
                if (serviceInfo.serviceType.contains("_dinoroar._tcp")) {
                    resolveService(serviceInfo, onServerFound)
                }
            }

            override fun onServiceLost(serviceInfo: NsdServiceInfo) {
                Log.w(TAG, "mDNS 服务丢失: ${serviceInfo.serviceName}")
            }

            override fun onDiscoveryStopped(serviceType: String) {
                Log.d(TAG, "mDNS 发现已停止: $serviceType")
                isDiscovering = false
            }

            override fun onStartDiscoveryFailed(serviceType: String, errorCode: Int) {
                Log.e(TAG, "启动 mDNS 发现失败: 错误码 $errorCode")
                stopDiscovery()
            }

            override fun onStopDiscoveryFailed(serviceType: String, errorCode: Int) {
                Log.e(TAG, "停止 mDNS 发现失败: 错误码 $errorCode")
                isDiscovering = false
            }
        }

        try {
            nsdManager.discoverServices(SERVICE_TYPE, NsdManager.PROTOCOL_DNS_SD, discoveryListener)
        } catch (e: Exception) {
            Log.e(TAG, "调用 discoverServices 异常", e)
        }
    }

    private fun resolveService(
        serviceInfo: NsdServiceInfo,
        onServerFound: (DiscoveredServer) -> Unit
    ) {
        nsdManager.resolveService(serviceInfo, object : NsdManager.ResolveListener {
            override fun onResolveFailed(serviceInfo: NsdServiceInfo, errorCode: Int) {
                Log.e(TAG, "解析 mDNS 服务失败: 错误码 $errorCode")
            }

            override fun onServiceResolved(resolvedInfo: NsdServiceInfo) {
                val host = resolvedInfo.host?.hostAddress ?: return
                var port = resolvedInfo.port

                // 优先从 TXT 记录读取服务端自定义映射端口与 IP
                val attributes = resolvedInfo.attributes
                val txtPort = attributes["mappedPort"]?.let { String(it) }?.toIntOrNull()
                val txtHost = attributes["host"]?.let { String(it) }

                val finalHost = txtHost ?: host
                val finalPort = txtPort ?: port
                val baseUrl = "http://$finalHost:$finalPort"

                Log.i(TAG, "成功解析 DinoRoar 服务端: $baseUrl")
                onServerFound(
                    DiscoveredServer(
                        name = resolvedInfo.serviceName,
                        host = finalHost,
                        port = finalPort,
                        baseUrl = baseUrl
                    )
                )
            }
        })
    }

    fun stopDiscovery() {
        if (!isDiscovering || discoveryListener == null) return
        try {
            nsdManager.stopServiceDiscovery(discoveryListener)
        } catch (e: Exception) {
            Log.e(TAG, "停止 mDNS 发现失败", e)
        } finally {
            discoveryListener = null
            isDiscovering = false
        }
    }
}
```

---

## 6. 踩坑记录与排障最佳实践（避坑指南）

在多平台、不同网络拓扑及硬件环境下，mDNS 服务发现容易遇到以下典型问题：

### 踩坑 1：mDNS 服务类型后缀格式不合规导致无法发现
- **现象**：服务端明明启动了广播，但 Android 端的 `onServiceFound` 从不被调用。
- **原因**：mDNS / DNS-SD 规范要求完全限定域名（FQDN）必须以点 `.` 结尾（如 `_dinoroar._tcp.local.`）。部分平台传 `_dinoroar._tcp` 或未补齐 `.local.` 时，Zeroconf 注册的服务名会被自动截断或拼错域名。
- **解决方案**：在注册 `ServiceInfo` 前，严格校验并格式化 `service_type`，确保末尾包含 `.local.`。

### 踩坑 2：Docker 容器默认网桥过滤组播报文
- **现象**：在宿主机用 `avahi-browse` 能搜到服务，但在同一局域网的手机客户端却搜不到。
- **原因**：Docker 默认的 `bridge` 网络与物理网卡隔离，不会自动路由组播地址 `224.0.0.251`。
- **解决方案**：
  1. 创建显式命名的专属网桥 `br-dinoroar`；
  2. 宿主机安装 `avahi-daemon`，并在 `avahi-daemon.conf` 中配置 `enable-reflector=yes` 和 `allow-interfaces=<物理网卡>,br-dinoroar`。

### 踩坑 3：Android `NsdManager.resolveService()` 并发冲突 (`FAILURE_ALREADY_ACTIVE`)
- **现象**：如果局域网内存在多个服务实例或短时间触发多次 `onServiceFound`，调用 `resolveService()` 会直接回调 `onResolveFailed` 且错误码为 `3`（`FAILURE_ALREADY_ACTIVE`）。
- **原因**：Android 12 之前的 `NsdManager` 底层解析器是单任务状态机，不支持并发 resolve。
- **解决方案**：在客户端维护一个待解析队列（Queue），按序串行执行 resolve，或在首个服务解析成功后立即取消后续排队。

### 踩坑 4：容器内获取的 IP 为容器私有网段（172.x.x.x）
- **现象**：Android 端解析出的 IP 是 `172.18.0.2`，客户端无法在宿主机局域网直连访问。
- **原因**：服务端运行在容器内部，默认读取网卡 IP 只能读到容器分配的私有虚拟 IP。
- **解决方案**：
  1. 服务端 `_detect_local_ip()` 在探测时过滤掉 `127.` 与 `172.` 开头的虚拟网段；
  2. 提供环境变量 `SERVICE_ADVERTISE_HOST` 与 Web 后台【系统设置】修改 IP 的能力，并将真实 IP 写入 mDNS TXT 记录中的 `host` 属性，Android 端优先读取 TXT 属性。

### 踩坑 5：宿主机防火墙（UFW / iptables）拦截 5353 组播端口
- **现象**：Avahi 组播反射已配置，但外部客户端依然收不到。
- **排查命令**：
  ```bash
  # 检查宿主机 UDP 5353 端口是否放行
  sudo ufw status
  # 若未放行，执行放行规则
  sudo ufw allow in on eth0 to any port 5353 proto udp
  sudo ufw allow in on br-dinoroar to any port 5353 proto udp
  ```

---

## 7. 联调测试与验证工具链

在日常开发与部署维护中，推荐使用以下命令和工具进行链路分段排查：

### 7.1 Linux 宿主机测试命令

```bash
# 1. 查看当前网络上所有 mDNS 服务通告（需安装 avahi-utils）
avahi-browse -atr | grep -i dinoroar

# 2. 解析特定 DinoRoar 服务的详细 TXT 记录与 IP:端口
avahi-browse -r _dinoroar._tcp

# 3. 抓取网桥上的 mDNS 组播包，验证容器是否发出了通告
sudo tcpdump -i br-dinoroar port 5353 -vv

# 4. 抓取物理网卡上的 mDNS 组播包，验证 Avahi 是否成功反射到了外网
sudo tcpdump -i eth0 port 5353 -vv
```

### 7.2 Android 客户端辅助调试工具

1. **Service Browser / Discovery App**：在手机应用商店下载开源 mDNS 测试工具（如 *Bonjour Search* 或 *Service Browser*），进入后查看局域网内是否存在 `_dinoroar._tcp` 服务。
2. **Logcat 过滤标签**：
   ```bash
   adb logcat -s NsdDiscoveryHelper NsdManager
   ```
