from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import types
from servers.human_server import (
    process_human_interaction,
    process_human_audio,
    set_audio_type,
    interrupt_human_talk,
    check_is_speaking
)
from core import Success

router = APIRouter(route_class=Success)

class HumanRequest(BaseModel):
    sessionid: int = 0
    type: str # 'echo' or 'chat'
    text: str
    interrupt: bool = False

class AudioTypeRequest(BaseModel):
    sessionid: int = 0
    audiotype: str
    reinit: bool = False

class SessionRequest(BaseModel):
    sessionid: int = 0

@router.post("/human")
async def human_endpoint(req: HumanRequest):
    res = await process_human_interaction(
        sessionid=req.sessionid,
        interaction_type=req.type,
        text=req.text,
        interrupt=req.interrupt
    )
    if isinstance(res, types.AsyncGeneratorType):
        return StreamingResponse(res, media_type="text/plain")
    return res

@router.post("/humanaudio")
async def human_audio_endpoint(sessionid: int = Form(0), file: UploadFile = File(...)):
    filebytes = await file.read()
    res = await process_human_audio(sessionid, filebytes)
    return res

@router.post("/set_audiotype")
async def set_audiotype_endpoint(req: AudioTypeRequest):
    res = await set_audio_type(req.sessionid, req.audiotype, req.reinit)
    return res

@router.post("/interrupt_talk")
async def interrupt_talk_endpoint(req: SessionRequest):
    res = await interrupt_human_talk(req.sessionid)
    return res

@router.post("/is_speaking")
async def is_speaking_endpoint(req: SessionRequest):
    res = await check_is_speaking(req.sessionid)
    return res
