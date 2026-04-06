from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from contextlib import asynccontextmanager

import json
from types import SimpleNamespace
from utils.logger import logger

try:
    with open("config.json", "r", encoding="utf-8") as f:
        config_data = json.load(f)
        settings = SimpleNamespace(**config_data.get("livetalking", {}))
        
        # Merge ollama config
        ollama_cfg = config_data.get("ollama", {})
        settings.llm_url = ollama_cfg.get("url", "http://127.0.0.1:11434/v1")
        settings.llm_model = ollama_cfg.get("model", "qwen3.5:0.8b")
except Exception as e:
    logger.error(f"Failed to load config.json: {e}")
    settings = SimpleNamespace()

if settings.customvideo_config:
    try:
        with open(settings.customvideo_config, 'r') as file:
            settings.customopt = json.load(file)
    except Exception as e:
        logger.error(f"Failed to load customvideo_config: {e}")

from api import webrtc_api, human_api, record_api, ai_api
from servers.webrtc_server import close_all_connections
import servers.state as state

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("Initializing LiveTalking Backend (FastAPI)")
    from core.lipreal import load_model, load_avatar, warm_up
    
    # Push opt to state for build_nerfreal
    state.opt = settings
    state.model = load_model("./models/wav2lip.pth")
    state.avatar = load_avatar(settings.avatar_id)
    warm_up(settings.batch_size, state.model, 256)
    
    yield
    
    # Shutdown logic
    logger.info("Shutting down properly")
    await close_all_connections()


app = FastAPI(title="LiveTalking API", lifespan=lifespan)

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include APIs
app.include_router(webrtc_api.router, tags=["WebRTC"])
app.include_router(human_api.router, tags=["Human Control"])
app.include_router(record_api.router, tags=["Record Control"])
app.include_router(ai_api.router, tags=["AI"])

# Mount static files
app.mount("/", StaticFiles(directory="web", html=True), name="web")

if __name__ == "__main__":
    logger.info(f"Start HTTP server: http://0.0.0.0:{settings.listenport}/webrtcapi.html")
    uvicorn.run("main:app", host="0.0.0.0", port=settings.listenport, reload=False)
