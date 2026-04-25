"""
WebRTC 协商接口。

前端页面创建本地 offer 后，会把 SDP 发到这里。
后端在这里创建数字人会话、绑定音视频轨道，并返回 answer。
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from servers.webrtc_server import process_offer
from core import Success

router = APIRouter(route_class=Success)


class OfferRequest(BaseModel):
    """WebRTC offer 请求体。"""

    sdp: str
    type: str
    sessionid: int = 0


@router.post("/offer")
async def offer_endpoint(req: OfferRequest):
    """处理前端发来的 WebRTC offer，并返回 answer。"""
    response_data = await process_offer(req.sdp, req.type, req.sessionid)
    return response_data
