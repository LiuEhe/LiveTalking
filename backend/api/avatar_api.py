"""
数字人素材生成接口。

这里的核心用途是：
1. 接收前端传来的 avatar 标识。
2. 找到对应上传的视频文件。
3. 触发后台的人脸裁剪、素材抽帧和坐标生成流程。
"""

import os
from fastapi import APIRouter
from pydantic import BaseModel
from servers.avatar_server import generate_avatar
from core import Success

router = APIRouter(route_class=Success)


class AvatarGenRequest(BaseModel):
    """生成数字人素材所需的参数。"""

    avatar_id: str
    video_path: str = ""
    filename: str = ""
    img_size: int = 256


@router.post("/avatar/gen")
async def avatar_gen_endpoint(req: AvatarGenRequest):
    """
    启动头像素材生成任务。

    常见调用方式有两种：
    - 前端先上传文件，再只传 `filename`
    - 你在本地脚本或运维工具里直接传绝对路径 `video_path`
    """
    video_path = req.video_path

    # 当前端只传文件名时，默认从 `backend/data/uploads/` 里寻找上传素材。
    if not video_path and req.filename:
        backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        video_path = os.path.join(backend_root, "data", "uploads", req.filename)

    if not video_path or not os.path.exists(video_path):
        return {
            "code": -1,
            "msg": "Source file not found. Please upload first or provide correct video_path/filename.",
        }

    res = await generate_avatar(
        avatar_id=req.avatar_id, video_path=video_path, img_size=req.img_size
    )
    return res
