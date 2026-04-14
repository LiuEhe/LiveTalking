from fastapi import APIRouter
from pydantic import BaseModel
from servers.record_server import handle_record_action
from core import Success

router = APIRouter(route_class=Success)

class RecordRequest(BaseModel):
    sessionid: int = 0
    type: str # 'start_record' or 'end_record'

@router.post("/record")
async def record_endpoint(req: RecordRequest):
    res = await handle_record_action(req.sessionid, req.type)
    return res
