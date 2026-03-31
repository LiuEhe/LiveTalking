# LiveTalking 后端重构计划 (FastAPI 架构)

## 1. 重构目标
将现有的 `LiveTalking` 后端（混合了 aiohttp 与 Flask 的实现）重构为统一、现代化的 `FastAPI` 架构。在重构过程中，将后端逻辑解耦为结构清晰的**三层架构**（`api`、`servers`、`core`），以提高代码的可读性、可维护性和可扩展性。前端关联目录（`web`）保持原样不变。

---

## 2. 目录结构设计
重构后的 `backend` 目录结构主要调整如下：

```text
backend/
├── api/                  # 接口层 (路由定义、参数校验)
│   ├── __init__.py
│   ├── webrtc_api.py     # WebRTC 相关接口 (如：/offer)
│   ├── human_api.py      # 数字人控制相关接口 (如：/human, /humanaudio, /set_audiotype)
│   └── record_api.py     # 录制相关接口 (如：/record)
├── servers/              # 服务层 (业务逻辑实现)
│   ├── __init__.py
│   ├── webrtc_server.py  # WebRTC 逻辑处理实体对应
│   ├── human_server.py   # 数字人状态处理与 LLM 交互逻辑
│   └── record_server.py  # 录制逻辑控制实体对应
├── core/                 # 核心基础层 (配置、数据库抽象、JWT等)
│   ├── __init__.py
│   ├── config.py         # 配置读取 (config.json 解析) 与全局配置类
│   ├── database.py       # 数据库读取抽象操作基类
│   ├── security.py       # JWT Token 的生成与验证
│   └── dependencies.py   # FastAPI 依赖项注入 (如获取会话，验证 Token)
├── main.py               # 全新的 FastAPI 启动入口 (替换现有的 app.py)
├── requirements.txt      # 依赖调整 (增加 fastapi, uvicorn, pydantic, pyjwt 等)
└── ... (其余底层通讯组件、模型组件如 basereal.py 等视情况保留)
```

---

## 3. 分层职责详细拆解

### 3.1 API 层 (`api/`)
**核心职责**：负责接收对外的 HTTP/WebSocket 请求，参数校验以及统一结果响应。不包含具体的业务逻辑。
- 采用 FastAPI 的 `APIRouter` 进行路由分组，自动生成 Swagger 文档。
- 参数校验通过 Pydantic Models 严格约束（对应原先手工获取 `await request.json()` 并判断参数的机制）。
- 本层仅负责调用 `servers/` 层的对应功能模块。
- 通过注入 `core/dependencies.py` 来实现权限和 Token 拦截校验。

### 3.2 Servers 层 (`servers/`)
**核心职责**：实现具体的业务逻辑流转。该层内包名为 `xxx_server.py`，需与 `api/` 层下的 `xxx_api.py` 文件相对应。
- `api/webrtc_api.py` 的具体功能（如建立 `RTCPeerConnection` 会话处理）在此层的 `webrtc_server.py` 实现。
- 接管原先 `app.py` 中零散的逻辑，如全局 `nerfreals` 字典的管理、`llm_response` 的异步调用等。
- 与底层的算法和媒体层（如 `basereal`, `lipreal` 等）进行隔离与调度，保持上层接口干净。

### 3.3 Core 层 (`core/`)
**核心职责**：系统级别的基础设施与系统级配置。
- **配置管理 (`config.py`)**：通过 Pydantic 的 Settings 模块或直接解析 `config.json` 处理环境变量以及启动时的参数覆盖机制（如 argparse 参数替换为结构化配置）。
- **数据库 (`database.py`)**：封装基础操作基类，用于控制数据库读写映射，管理连接池或者ORM基础配置。
- **权限与认证 (`security.py`)**：实现对 JWT 令牌的生成、签发及验证机制。（如后续系统需要用户登录/管理台功能，强依赖此模块）。

---

## 4. 重构实施步骤

1. **第一阶段：环境准备与基础搭建 (Core)**
   - 修改 `requirements.txt`：加入 `fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`, `PyJWT` (或 `python-jose`) 等必要依赖。
   - 构建 `core` 层：编写并测试 `config.py` 处理 `config.json`；编写 `security.py` 完成 JWT 打通机制；编写空壳 `database.py` 打底。

2. **第二阶段：业务逻辑抽离 (Servers)**
   - 提取原 `app.py` 中的流媒体创建逻辑 (aiortc相关事务) 与 `nerfreals` 会话管理，将其迁移至 `servers/webrtc_server.py` 中。
   - 提取数字人状态操控（打断、文字通讯、语音流等模块）与后台协同功能，归入 `servers/human_server.py` 与 `servers/record_server.py` 中。

3. **第三阶段：路由暴露与集成 (API & Main)**
   - 编写各个子模块的 `APIRouter`，并使用 Pydantic 创建请求参数模型以替换散乱的 JSON 取值。
   - 编写新的 `main.py` 作为程序入口并使用 `uvicorn` 承载：
     - 注册所有 `routers`
     - 配置由于前后端分离产生的 `CORS` 跨域设置
     - 挂载生命周期钩子事件（如释放 `RTCPeerConnection` 连接逻辑，替换原有的 `on_shutdown` 事件）
     - 按照既定目录提供静态文件托管给 `web` 目录

4. **第四阶段：测试与联调验证**
   - 通过 Swagger UI 验证每一个 REST API 输入和输出。
   - 验证替换了框架后的 WebRTC 本地推流以及消息交互是否保持 0 降级运行。
