from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils.logger import logger
from servers.webrtc_server import process_offer

router = APIRouter()

class OfferRequest(BaseModel):
    sdp: str
    type: str
    sessionid: int = 0

@router.post("/offer")
async def offer_endpoint(req: OfferRequest):
    try:
        response_data = await process_offer(req.sdp, req.type, req.sessionid)
        return response_data
    except Exception as e:
        logger.exception('Exception in offer:')
        raise HTTPException(status_code=500, detail=str(e))
