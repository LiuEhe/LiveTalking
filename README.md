# LiveTalking 二次开发项目

这是开源项目 [LiveTalking](https://github.com/lipku/LiveTalking) 的二次开发版本。

## 项目简介
本项目在原 [LiveTalking](https://github.com/lipku/LiveTalking) 基础上进行了深度重构，旨在提供更清晰的代码结构、更高的可维护性和更强的扩展能力。目前已将原有的混合架构（Flask/aiohttp）完全重构为标准的 **FastAPI 三层架构**。

## 核心架构
项目遵循严格的解耦原则，分为以下层次：

1.  **API 层 (`backend/api/`)**:
    *   负责定义 FastAPI 路由，通过 `v1_router` 统一提供带有版本前缀的接口（如 `/api/v1`）。
    *   **全局异常捕获**：集成自定义 `Success` APIRoute 机制，自动处理业务异常并返回标准格式 JSON，从而实现 API 函数内部无需手写 `try...except`。
    *   处理 HTTP/WebSocket 请求及参数验证（使用 Pydantic 模型）。
    *   **不包含**任何业务逻辑，仅作为接口网关。

2.  **Server 层 (`backend/servers/`)**:
    *   负责处理具体的业务逻辑。
    *   管理全局状态（如 `state.py` 中的会话和连接管理）。
    *   调用 Core 层的功能完成具体任务。

3.  **Core 层 (`backend/core/`)**:
    *   系统的底层核心逻辑，包含配置加载与各层级模块的统一导出管理。
    *   **工程化基座**：提供全局 `Success` 响应处理器，规范后端返回结构。
    *   包含数字人推理的核心类（如 `LipReal`, `BaseReal`）。
    *   处理 ASR (`BaseASR`, `LipASR`) 和 TTS (`BaseTTS` 及其派生类) 的核心逻辑。
    *   管理 WebRTC 核心组件 (`webrtc.py`)。

4.  **Utils 层 (`backend/utils/`)**:
    *   存放通用的工具类，如日志系统 (`logger.py`)。

## 前端架构
前端基于 **Vue 3 (Composition API) + TypeScript + Vite**，并使用最新的 **Tailwind CSS v4** 进行样式构建，核心目录结构如下：

1.  **Views 层 (`frontend/src/views/`)**:
    *   负责页面视图组件的展示。
2.  **Router 层 (`frontend/src/router/`)**:
    *   使用 `vue-router` 管控页面的路由与跳转。
3.  **Utils & Types 层 (`frontend/src/utils/` & `frontend/src/types/`)**:
    *   `utils` 存放通用的逻辑与请求工具。
    *   `types` 统一管理 TypeScript 类型声明。

## 目录结构
```text
frontend/                # Vue 3 前端应用
├── src/                 # 前端源码
│   ├── views/           # 页面级视图组件
│   ├── router/          # 路由管控
│   ├── utils/           # 通用 TS 工具函数
│   ├── types/           # TypeScript 类型定义
│   └── main.ts          # 挂载路由及应用的入口
backend/
├── main.py              # FastAPI 应用入口，负责生命周期管理与模块化导入
├── config.json          # 唯一配置文件，禁止在代码中硬编码配置项
├── api/                 # 接口层：实现 /api/v1 路由转发与 Success 全局异常捕获
├── servers/             # 服务层：处理核心业务逻辑与会话状态管理
├── core/                # 核心层：包含 AI 推理、音频处理驱动及 Success 处理基类
├── utils/                # 工具层：日志管理等
├── wav2lip/             # 特定模型的代码实现
├── data/                # 存放头像数据 (avatars)
└── models/              # 存放模型权重文件 (.pth)
```

## 运行与开发
*   **启动服务**: 进入 `backend` 目录，执行 `python main.py`。
*   **开发规范**: 必须遵守 `skills/code_standards/SKILL.md` 中的规范，严禁硬编码，严格执行三层调用关系。
*   **更多细节**: 请参考 [backend/README.md](file:///d:/Project/LiveTalking/backend/README.md) 获取原始项目的详细安装说明。

---
*注：本项目致力于打造一个结构清晰、高性能的高仿真数字人交互平台。*
