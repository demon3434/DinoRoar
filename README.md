<p align="center">
  <img src="backend/app/static/images/default_stickers/sticker_3d_triceratops.png" width="128" height="128" alt="DinoRoar Icon">
</p>

# 🦖 DinoRoar - 恐龙手账全栈工程 (Fullstack Monorepo)

DinoRoar 是专为亲子与手账爱好者打造的**全栈情绪日记与手账贴纸系统**。项目采用工业级单体大仓库（Monorepo）架构，统筹维护 **Android 客户端**、**FastAPI 后端**、**Vue 3 Web 管理平台**与**自托管语音识别微服务（STT）**，实现跨端数据强一致性与全链路开发无缝协同。

---

## ✨ 核心全栈架构与特性

### 📱 Android 移动端 (Mobile App)
- **原生现代体验**：基于 100% Kotlin + Jetpack Compose 响应式 UI 开发。
- **离线优先设计**：Room 本地数据库持久化缓存，断网也能畅快写日记；连网后基于 LWW 乐观并发策略与增量版本原子同步。
- **趣味恐龙锁屏**：内置恐龙伪装跑酷小游戏与九宫格恐龙时序解锁，双重 BackHandler 深度拦截，严密防护隐私。
- **手账排版与能量商城**：每篇日记支持自由摆放手账贴纸与背景画布，支持每日签到与银行风格蛋能量账本流水结算。

### 💻 Web 管理控制台 (Admin Web)
- **现代化技术栈**：Vue 3 + Vite + TypeScript 纯前端工程架构。
- **全要素资产管家**：手账贴纸商城、背景画布大屏、节日促销统一调价管理与数据可视化统计。
- **零原生弹窗规范**：全站统一自定义精美弹窗与防拖拽误触交互守卫。

### 🚀 后端与业务引擎 (Backend & APIs)
- **异步高性能**：基于 Python 3.11+ 与 FastAPI 构建，统一 RESTful API 契约与 Pydantic 强类型校验。
- **零转换直传设计**：移动端实体、网络 API Payload 与云端数据库字段 1:1 绝对对齐，从源头斩断命名与时序 BUG。
- **局域网自动发现**：内置 mDNS Zeroconf 广播协议，手机与服务端在同一 Wi-Fi 下无需手动配 IP 即可秒级自连。

### 🎙️ 语音转文字服务 (STT Microservice)
- **自托管离线转写**：基于 SenseVoice-Small ONNX 引擎，完全独立于 Docker 容器中运行，保障家庭隐私。

---

## 🛠️ 全栈技术栈

| 模块 | 技术选型 | 说明 |
| :--- | :--- | :--- |
| **移动端 (Android)** | Kotlin, Jetpack Compose, Material3, Room, Retrofit2, Hilt | 原生 Android 客户端 |
| **管理端 (Web)** | Vue 3, Vite, TypeScript, Pinia, Vue Router | 独立现代化 SPA 管理后台 |
| **服务端 (Backend)** | Python 3.11+, FastAPI, SQLAlchemy, Pydantic v2, Zeroconf | 核心 API 路由与业务中枢 |
| **语音引擎 (STT)** | SenseVoice-Small, ONNX Runtime, Python | 容器化语音识别微服务 |
| **容器编排 (DevOps)** | Docker, Docker Compose | 跨平台环境与持久化存储隔离 |

---

## 📁 Monorepo 目录结构

```text
DinoRoar/
├── android/                         # Android 移动客户端工程 (Kotlin / Compose)
│   ├── app/                         # App 源码、资源文件与 Room 数据库
│   ├── gradle/                      # Gradle Wrapper 与依赖版本目录
│   ├── build.gradle.kts             # 模块构建配置
│   ├── settings.gradle.kts          # 工程设置
│   └── local.properties             # 本地 Android SDK 路径配置
│
├── backend/                         # FastAPI 后端服务
│   ├── app/                         # 业务路由、数据模型、服务层与静态资源
│   ├── Dockerfile                   # 后端 Docker 镜像定义
│   └── requirements.txt             # Python 依赖清单
│
├── frontend/                        # Web 管理端工程 (Vue 3 + Vite + TypeScript)
│   ├── src/                         # Vue 组件、视图路由与 API 服务
│   ├── package.json                 # 前端依赖配置
│   └── vite.config.ts               # Vite 打包配置
│
├── stt/                             # 语音转文字独立微服务 (SenseVoice ONNX)
│   ├── main.py                      # 独立转写 API 接口
│   └── Dockerfile                   # STT 容器构建定义
│
├── docs/                            # 统一全栈文档中心
│   ├── android/                     # Android 权威设计与接口对接文档
│   ├── adr/                         # 关键架构决策记录 (ADR)
│   └── ...                          # 部署与开发指南
│
├── openspec/                        # 统一 OpenSpec 规格说明与变更归档
│   ├── specs/                       # 核心业务能力规格 (全端统筹)
│   └── changes/                     # 历史变更记录与演进任务
│
├── scripts/                         # 快捷运维与辅助脚本
│   └── build_apk.bat                # Android 免 Studio 一键编译打包工具
│
├── docker-compose.yml               # 开箱即用多容器服务编排模板
├── .env.example                     # 环境变量配置参考示例
└── .gitignore                       # 全栈工业级 Git 忽略防护规范
```

---

## 🚀 快速上手与运行指南

### 1. 服务端与 Web 管理端启动 (Docker Compose)

```bash
# 复制环境变量模板
cp .env.example .env

# 启动容器编排服务 (后端 + Web + STT 语音识别)
docker compose up -d
```
启动成功后，浏览器访问 `http://<服务器IP>:8080` 即可进入 Web 管理控制台。

### 2. Android 移动端本地打包 (无需 Android Studio)

本项目支持在终端中一键自动调用 Gradle 构建，无需打开沉重的 Android Studio：

```cmd
:: 构建正式签名 Release 版 APK
scripts\build_apk.bat release

:: 构建测试 Debug 版 APK
scripts\build_apk.bat debug
```

构建成功后，生成的 APK 将自动保存在：
- **Release 版**：`android/app/build/outputs/apk/release/app-release.apk`
- **Debug 版**：`android/app/build/outputs/apk/debug/app-debug.apk`