import os
from fastapi import APIRouter
from pydantic import BaseModel
from servers.avatar_server import generate_avatar
from core import Success

router = APIRouter(route_class=Success)

class AvatarGenRequest(BaseModel):
    avatar_id: str
    video_path: str = ""
    filename: str = ""
    img_size: int = 256

@router.post("/avatar/gen")
async def avatar_gen_endpoint(req: AvatarGenRequest):
    video_path = req.video_path
    
    # If video_path is not provided but filename is, look in data/uploads/
    if not video_path and req.filename:
        backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        video_path = os.path.join(backend_root, "data", "uploads", req.filename)
        
    if not video_path or not os.path.exists(video_path):
        return {"code": -1, "msg": "Source file not found. Please upload first or provide correct video_path/filename."}

    res = await generate_avatar(
        avatar_id=req.avatar_id,
        video_path=video_path,
        img_size=req.img_size
    )
    return res
