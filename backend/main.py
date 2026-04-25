"""
后端 FastAPI 启动入口。

阅读这个文件时，可以把它理解成后端的“总装配厂”：
1. 读取 `config.json`，把运行参数收集成 `settings`。
2. 在应用启动阶段加载口型模型、数字人素材，并做一次预热。
3. 注册 API 路由。
4. 在程序退出时，统一关闭 WebRTC 连接。

如果你后面想把项目从 B 站直播场景改造成快手场景，这个文件通常不是
业务改造的主要战场，但它非常适合理解“系统是怎么被拉起来的”。
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn
import json
import os
from types import SimpleNamespace

from core import load_model, load_avatar, warm_up
from api import v1_router
from servers import close_all_connections, state
from utils.logger import logger


def load_settings():
    """
    从 `config.json` 读取运行配置，并转换成支持点号访问的对象。

    例如：
    - 原始字典访问方式：`config["livetalking"]["listen_host"]`
    - 这里返回后可写成：`settings.listen_host`

    这样做的好处是后续各模块读取配置时更直观，也更接近“配置对象”的概念。
    """
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config_data = json.load(f)
            lt_cfg = config_data.get("livetalking", {})
            s = SimpleNamespace(**lt_cfg)

            # 单独把大模型配置补充到同一个 settings 对象里，方便服务层统一读取。
            ollama_cfg = config_data.get("ollama", {})
            s.llm_url = ollama_cfg.get("url", "")
            s.llm_model = ollama_cfg.get("model", "")

            # 这里不是“拍脑袋补默认业务值”，而是防止缺字段时报 AttributeError。
            # 真正的参数含义和最终值，仍然以 config.json 为准。
            if not hasattr(s, "model_path"):
                s.model_path = ""
            if not hasattr(s, "static_dir"):
                s.static_dir = ""
            if not hasattr(s, "listen_host"):
                s.listen_host = ""
            if not hasattr(s, "warmup_res"):
                s.warmup_res = 0

            # 自定义动作视频配置是可选项，用于“非说话状态”播放固定动作或待机素材。
            if getattr(s, "customvideo_config", None):
                try:
                    with open(s.customvideo_config, "r") as file:
                        s.customopt = json.load(file)
                except Exception as e:
                    logger.error(f"Failed to load customvideo_config: {e}")
            return s
    except Exception as e:
        logger.error(f"Failed to load config.json: {e}")
        return SimpleNamespace()


settings = load_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 生命周期钩子。

    `yield` 之前执行“启动逻辑”，`yield` 之后执行“关闭逻辑”。
    这和很多框架里的 `startup/shutdown` 钩子是同一个概念。
    """
    # 应用启动时，把模型和头像素材提前放到全局状态，避免首个请求才临时加载。
    logger.info("Initializing LiveTalking Backend (FastAPI)")

    # state 模块相当于一个共享运行时仓库，后面的 WebRTC 会话会直接从这里取资源。
    state.opt = settings
    state.model = load_model(settings.model_path)
    state.avatar = load_avatar(settings.avatar_id)
    # 预热的目的，是让首帧推理时少一次“冷启动”延迟。
    warm_up(settings.batch_size, state.model, settings.warmup_res)

    yield

    # 服务关闭时，统一断开所有 PeerConnection，避免残留会话和线程。
    logger.info("Shutting down properly")
    await close_all_connections()


app = FastAPI(title="LiveTalking API", lifespan=lifespan)

# 这里允许所有来源跨域，适合开发和局域网调试；
# 如果后面要正式上线，通常需要把来源收紧到你自己的前端域名。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 把所有 `/api/v1/...` 路由挂到主应用上。
app.include_router(v1_router)

# 如果你希望后端同时托管前端静态页面，可以打开这行挂载配置。
# app.mount("/", StaticFiles(directory=settings.static_dir, html=True), name="web")

if __name__ == "__main__":
    logger.info(
        f"Start HTTP server: http://{settings.listen_host}:{settings.listenport}/webrtcapi.html"
    )
    uvicorn.run("main:app", host=settings.listen_host, port=settings.listenport, reload=False)
