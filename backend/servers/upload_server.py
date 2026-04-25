"""
上传文件服务。

这里故意做得很轻，只负责“把前端传来的二进制文件落盘”，
并不负责理解文件内容本身。后续由别的服务决定它是视频、图片还是别的素材。
"""

import os
import shutil
from fastapi import UploadFile
from utils.logger import logger


def get_upload_base_dir():
    """返回上传目录，不存在则自动创建。"""
    backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    upload_dir = os.path.join(backend_root, "data", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


async def save_upload_file(file: UploadFile):
    """把上传文件原样保存到 `data/uploads/` 目录。"""
    try:
        upload_dir = get_upload_base_dir()
        file_path = os.path.join(upload_dir, file.filename)

        # 使用流复制而不是一次性全部读入内存，适合更大的上传文件。
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"File saved to {file_path}")
        return {"code": 0, "msg": "Upload successful", "data": {"filename": file.filename}}
    except Exception as e:
        logger.error(f"Failed to save upload: {str(e)}")
        return {"code": -1, "msg": str(e)}
