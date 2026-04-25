"""
统一组装 API 路由。

这个文件的职责很简单：
- 把不同业务域的路由拆分到独立文件。
- 再统一挂载到 `/api/v1` 这个版本前缀下。

这样做的好处是，后面你要继续扩展“快手相关接口”时，可以继续按业务拆文件，
而不是把所有接口都堆在一个大文件里。
"""

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
