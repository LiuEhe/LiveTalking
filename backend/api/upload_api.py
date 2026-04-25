"""
通用文件上传接口。

当前主要给素材上传使用，例如上传一段视频，再交给 `/avatar/gen`
继续生成数字人头像数据。
"""

from fastapi import APIRouter, UploadFile, File
from servers.upload_server import save_upload_file
from core import Success

router = APIRouter(route_class=Success)


@router.post("/upload")
async def generic_upload_endpoint(file: UploadFile = File(...)):
    """保存上传文件到后端固定目录。"""
    res = await save_upload_file(file)
    return res
