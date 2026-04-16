import os
import shutil
from fastapi import UploadFile
from utils.logger import logger

def get_upload_base_dir():
    backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    upload_dir = os.path.join(backend_root, "data", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir

async def save_upload_file(file: UploadFile):
    try:
        upload_dir = get_upload_base_dir()
        file_path = os.path.join(upload_dir, file.filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        logger.info(f"File saved to {file_path}")
        return {"code": 0, "msg": "Upload successful", "data": {"filename": file.filename}}
    except Exception as e:
        logger.error(f"Failed to save upload: {str(e)}")
        return {"code": -1, "msg": str(e)}
