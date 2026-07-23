# 🦖 DinoRoar - 恐龙手账后端与 Web 管理平台

DinoRoar 是专为亲子与手账爱好者打造的心情日记与手账贴纸系统后端。项目基于 FastAPI 开发，内置 SenseVoice 语音识别引擎（STT）代理与 mDNS 局域网设备自动发现功能。

---

## ✨ 核心特性

- **日记与心情管理**：支持多用户心情日记、关联人物、声音转文本（STT）及附件存储。
- **手账贴纸系统**：提供贴纸分类、动态贴纸包导入导出及自定义防重约束。
- **离线优先与同步**：支持客户端增量同步、离线数据合并与冲突判定。
- **局域网自动发现**：内置 mDNS Zeroconf 局域网广播，手机无需手动配置 IP 即可自动连接。
- **Web 管理控制台**：提供可视化仪表盘、贴纸仓库管理、系统设置及用户账号控制。

---

## 🛠️ 技术栈

- **后端框架**：Python 3.11 / FastAPI / Pydantic v2
- **数据库**：SQLite 3 / SQLAlchemy ORM
- **语音识别 (STT)**：SenseVoice ONNX / Sherpa-ONNX / FastAPI 代理
- **网络与服务发现**：mDNS Zeroconf / HTTP RESTful API
- **部署方式**：Docker / Docker Compose / 阿里云容器镜像服务 (CR)

---

## 🚀 快捷部署指南 (Docker Compose)

### 1. 复制配置文件

```bash
cp .env.example .env
```
*(可按需编辑 `.env` 中的端口与持久化挂载路径)*

### 2. 使用阿里云镜像一键部署

```bash
docker compose --env-file .env -f docker-compose.aliyun.yml up -d
```

部署完成后，访问 `http://<服务器IP>:8080` 即可进入 Web 管理控制台（默认管理员：`admin` / `admin_123`）。

> 详细的部署说明与运维指南请参阅：[阿里云镜像快捷部署指南](docs/aliyun_docker_deploy_guide.md)

---

## 📁 目录结构

```text
DinoRoar/
├── backend/                  # FastAPI 后端源码与 Web 静态资源
│   ├── app/                  # 业务路由、模型、服务层与 HTML 模板
│   ├── Dockerfile            # 后端容器构建文件
│   └── requirements.txt      # Python 依赖包
├── stt/                      # SenseVoice 语音识别服务
│   ├── main.py               # STT API 服务入口
│   └── Dockerfile            # STT 容器构建文件
├── docs/                     # 部署与系统设计规范文档
├── docker-compose.aliyun.yml # 阿里云镜像开箱即用编排文件
└── docker-compose.yml        # 本地源码构建编排文件
```

---

## 📄 开源协议与约定

本项目遵循团队内部协同开发规范，接口与 Android 端数据一致性约束参见 [AGENTS.md](AGENTS.md)。
