from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional
from utils.logger import logger
from servers.human_server import (
    process_human_interaction,
    process_human_audio,
    set_audio_type,
    interrupt_human_talk,
    check_is_speaking
)

router = APIRouter()

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
    try:
        res = await process_human_interaction(
            sessionid=req.sessionid,
            interaction_type=req.type,
            text=req.text,
            interrupt=req.interrupt
        )
        return res
    except Exception as e:
        logger.exception("exception in /human:")
        return {"code": -1, "msg": str(e)}

@router.post("/humanaudio")
async def human_audio_endpoint(sessionid: int = Form(0), file: UploadFile = File(...)):
    try:
        filebytes = await file.read()
        res = await process_human_audio(sessionid, filebytes)
        return res
    except Exception as e:
        logger.exception("exception in /humanaudio:")
        return {"code": -1, "msg": str(e)}

@router.post("/set_audiotype")
async def set_audiotype_endpoint(req: AudioTypeRequest):
    try:
        res = await set_audio_type(req.sessionid, req.audiotype, req.reinit)
        return res
    except Exception as e:
        logger.exception("exception in /set_audiotype:")
        return {"code": -1, "msg": str(e)}

@router.post("/interrupt_talk")
async def interrupt_talk_endpoint(req: SessionRequest):
    try:
        res = await interrupt_human_talk(req.sessionid)
        return res
    except Exception as e:
        logger.exception("exception in /interrupt_talk:")
        return {"code": -1, "msg": str(e)}

@router.post("/is_speaking")
async def is_speaking_endpoint(req: SessionRequest):
    try:
        res = await check_is_speaking(req.sessionid)
        return res
    except Exception as e:
        logger.exception("exception in /is_speaking:")
        return {"code": -1, "msg": str(e)}
