from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from servers.webrtc_server import process_offer
from core import Success

router = APIRouter(route_class=Success)

class OfferRequest(BaseModel):
    sdp: str
    type: str
    sessionid: int = 0

@router.post("/offer")
async def offer_endpoint(req: OfferRequest):
    response_data = await process_offer(req.sdp, req.type, req.sessionid)
    return response_data
