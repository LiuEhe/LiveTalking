from fastapi import APIRouter

from .webrtc_api import router as webrtc_router
from .human_api import router as human_router
from .record_api import router as record_router
from .ai_api import router as ai_router
from .avatar_api import router as avatar_router
from .upload_api import router as upload_router

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(webrtc_router, tags=["WebRTC"])
v1_router.include_router(human_router, tags=["Human Control"])
v1_router.include_router(record_router, tags=["Record Control"])
v1_router.include_router(ai_router, tags=["AI"])
v1_router.include_router(avatar_router, tags=["Avatar"])
v1_router.include_router(upload_router, tags=["Upload"])

__all__ = ["v1_router"]
