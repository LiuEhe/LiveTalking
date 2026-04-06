from fastapi import APIRouter
from pydantic import BaseModel
from utils.logger import logger
from servers.record_server import handle_record_action

router = APIRouter()

class RecordRequest(BaseModel):
    sessionid: int = 0
    type: str # 'start_record' or 'end_record'

@router.post("/record")
async def record_endpoint(req: RecordRequest):
    try:
        res = await handle_record_action(req.sessionid, req.type)
        return res
    except Exception as e:
        logger.exception("exception in /record:")
        return {"code": -1, "msg": str(e)}
