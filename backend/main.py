from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn
import json
import os
from types import SimpleNamespace

from core.lipreal import load_model, load_avatar, warm_up
from api import webrtc_api, human_api, record_api, ai_api
from servers.webrtc_server import close_all_connections
import servers.state as state
from utils.logger import logger

# Configuration loading (Strictly following rule: no hardcoded defaults)
def load_settings():
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config_data = json.load(f)
            lt_cfg = config_data.get("livetalking", {})
            s = SimpleNamespace(**lt_cfg)
            
            # LLM Settings
            ollama_cfg = config_data.get("ollama", {})
            s.llm_url = ollama_cfg.get("url", "")
            s.llm_model = ollama_cfg.get("model", "")
            
            # Ensure attributes exist from config.json (added previously) or empty defaults
            if not hasattr(s, "model_path"): s.model_path = ""
            if not hasattr(s, "static_dir"): s.static_dir = ""
            if not hasattr(s, "listen_host"): s.listen_host = ""
            if not hasattr(s, "warmup_res"): s.warmup_res = 0
            
            if getattr(s, "customvideo_config", None):
                try:
                    with open(s.customvideo_config, 'r') as file:
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
    # Startup logic
    logger.info("Initializing LiveTalking Backend (FastAPI)")
    
    # Push opt to state for build_nerfreal
    state.opt = settings
    state.model = load_model(settings.model_path)
    state.avatar = load_avatar(settings.avatar_id)
    warm_up(settings.batch_size, state.model, settings.warmup_res)
    
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
# app.mount("/", StaticFiles(directory=settings.static_dir, html=True), name="web")

if __name__ == "__main__":
    logger.info(f"Start HTTP server: http://{settings.listen_host}:{settings.listenport}/webrtcapi.html")
    uvicorn.run("main:app", host=settings.listen_host, port=settings.listenport, reload=False)
