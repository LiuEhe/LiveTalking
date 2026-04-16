from fastapi import APIRouter, UploadFile, File
from servers.upload_server import save_upload_file
from core import Success

router = APIRouter(route_class=Success)

@router.post("/upload")
async def generic_upload_endpoint(file: UploadFile = File(...)):
    res = await save_upload_file(file)
    return res
