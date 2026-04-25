"""
录制控制接口。

这里控制的是“把当前数字人的音视频输出录下来”，
常见用法是调试口型、回放直播片段，或者生成本地演示视频。
"""

from fastapi import APIRouter
from pydantic import BaseModel
from servers.record_server import handle_record_action
from core import Success

router = APIRouter(route_class=Success)


class RecordRequest(BaseModel):
    """录制控制请求体。"""

    sessionid: int = 0
    type: str  # 'start_record' 开始录制；'end_record' 结束录制。


@router.post("/record")
async def record_endpoint(req: RecordRequest):
    """开始或结束当前会话的录制。"""
    res = await handle_record_action(req.sessionid, req.type)
    return res
