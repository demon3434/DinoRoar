# DinoRoar 阿里云镜像快捷部署指南

本指南用于指导运维及开发人员通过阿里云容器镜像服务（CR）在全新服务器上快速部署 DinoRoar 后端服务与 STT 语音识别服务。

---

## 一、部署准备与环境要求

1. **操作系统**：Linux (Ubuntu 20.04+ / Debian 11+ / CentOS 7+)
2. **Docker 环境**：Docker Engine 20.10.0+ 及 Docker Compose v2.0.0+
3. **网络要求**：能够正常访问外网及阿里云上海镜像仓库。

---

## 二、登录阿里云容器镜像仓库

执行以下命令登录私有镜像仓库（仅需执行一次）：

```bash
docker login --username=<your-aliyun-account> crpi-your-instance.cn-shanghai.personal.cr.aliyuncs.com
```
*提示：按终端提示输入镜像仓库密码。*

---

## 三、创建部署目录与环境配置文件

建议在服务器上新建部署专用目录（如 `/opt/docker/dinoroar`）：

```bash
mkdir -p /opt/docker/dinoroar
cd /opt/docker/dinoroar
```

在该目录下创建环境变量配置文件 **`.env`**：

```ini
# ===================================================================
# DinoRoar 部署环境变量配置文件 (.env)
# ===================================================================

# 1. 容器时区设置
TZ=Asia/Shanghai

# 2. 宿主机对外端口映射 (宿主机端口:容器端口)
APP_HTTP_PORT=8080
APP_UDP_PORT=8090
STT_PORT=18000

# 3. 宿主机数据与文件持久化目录路径
HOST_DATA_DIR=/opt/docker/dinoroar/data
HOST_UPLOADS_DIR=/opt/docker/dinoroar/uploads
HOST_STT_MODELS_DIR=/opt/docker/dinoroar/stt_models
```

创建持久化存储目录并设置读写权限：

```bash
mkdir -p ${HOST_DATA_DIR:-/opt/docker/dinoroar/data}
mkdir -p ${HOST_UPLOADS_DIR:-/opt/docker/dinoroar/uploads}
mkdir -p ${HOST_STT_MODELS_DIR:-/opt/docker/dinoroar/stt_models}

chmod -R 777 /opt/docker/dinoroar
```

---

## 四、配置 Compose 文件 (`docker-compose.yml`)

在同一目录下创建 **`docker-compose.yml`**（该文件硬编码锁定镜像版本，并通过 `${变量名}` 自动读取 `.env` 中的宿主机环境配置，无需频繁修改此文件）：

```yaml
version: '3.8'

services:
  # DinoRoar 主后端服务
  app:
    image: crpi-tyyqcg8a2rpatesk.cn-shanghai.personal.cr.aliyuncs.com/zixidaxian/dinoroar-app:0.1
    container_name: dinoroar-app
    restart: unless-stopped
    ports:
      - "${APP_HTTP_PORT:-8080}:8080"
      - "${APP_UDP_PORT:-8090}:8090/udp"
    environment:
      - TZ=${TZ:-Asia/Shanghai}
      - WEB_PORT=8080
      - DATABASE_URL=sqlite:////workspace/data/dinoroar.db
      - STT_API_URL=http://stt:18000/api/transcribe
      - UPLOAD_DIR=/workspace/uploads
      - DATA_DIR=/workspace/data
    volumes:
      # 数据库与图片挂载
      - ${HOST_DATA_DIR:-/opt/docker/dinoroar/data}:/workspace/data
      - ${HOST_UPLOADS_DIR:-/opt/docker/dinoroar/uploads}:/workspace/uploads
      # 挂载宿主机时区文件，确保系统时间与本地上海时间一致
      - /etc/localtime:/etc/localtime:ro
    networks:
      - dinoroar_net

  # DinoRoar STT 语音识别服务
  stt:
    image: crpi-tyyqcg8a2rpatesk.cn-shanghai.personal.cr.aliyuncs.com/zixidaxian/dinoroar-stt:0.1
    container_name: dinoroar-stt
    restart: unless-stopped
    ports:
      - "${STT_PORT:-18000}:18000"
    environment:
      - TZ=${TZ:-Asia/Shanghai}
    volumes:
      # 语音识别 ONNX 模型缓存挂载
      - ${HOST_STT_MODELS_DIR:-/opt/docker/dinoroar/stt_models}:/app/models
      # 挂载宿主机时区文件
      - /etc/localtime:/etc/localtime:ro
    networks:
      - dinoroar_net

networks:
  dinoroar_net:
    name: dinoroar_net
    driver: bridge
```

---

## 五、启动与验证

### 1. 默认一键启动
在包含 `.env` 与 `docker-compose.yml` 的目录下直接执行：
```bash
docker compose up -d
```

### 2. 显式指定配置文件与环境变量启动（推荐最佳实践）
若目录下存在多个配置文件，或欲精确指定环境变量文件与 compose 文件，可执行以下命令：
```bash
docker compose --env-file .env -f docker-compose.yml up -d
```

### 3. 检查时区与运行状态
```bash
# 查看容器状态
docker compose -f docker-compose.yml ps

# 验证 app 容器内部系统时间（应显示 CST 上海时间）
docker exec -it dinoroar-app date
```

---

## 六、维护与常用操作

- **查看实时日志**：
  ```bash
  docker compose -f docker-compose.yml logs -f
  ```
- **修改配置后重载服务**：
  修改 `.env` 配置文件后，执行以下命令重新加载并运行：
  ```bash
  docker compose --env-file .env -f docker-compose.yml up -d
  ```
- **停止并销毁容器**：
  ```bash
  docker compose -f docker-compose.yml down
  ```

---

## 七、常见问题排查

1. **写权限问题 (Permission Denied)**：
   运行 `chmod -R 777 /opt/docker/dinoroar` 确保宿主机挂载目录具备可写权限。
2. **多 Compose 文件优先级混淆**：
   如果同级目录下同时存在 `.yaml` 和 `.yml` 文件，`docker compose` 默认会优先运行 `.yaml` 文件。建议统一使用 `-f docker-compose.yml` 显式指定文件运行。
