"""
数字人互动控制接口。

这一组接口是业务最常用的一层，负责把“用户想让数字人做什么”翻译成
后端动作，例如：
- 让数字人直接复读一段文字
- 让数字人调用 LLM 回答
- 上传一段音频让数字人播报
- 中断当前说话
- 查询当前是否正在说话
"""

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
    check_is_speaking,
)
from core import Success

router = APIRouter(route_class=Success)


class HumanRequest(BaseModel):
    """文本交互请求体。"""

    sessionid: int = 0
    type: str  # 'echo' 表示直接播报文本；'chat' 表示走大模型回复。
    text: str
    interrupt: bool = False


class AudioTypeRequest(BaseModel):
    """切换自定义音频/动作状态的请求体。"""

    sessionid: int = 0
    audiotype: str
    reinit: bool = False


class SessionRequest(BaseModel):
    """只需要 sessionid 的轻量请求体。"""

    sessionid: int = 0


@router.post("/human")
async def human_endpoint(req: HumanRequest):
    """
    文本驱动的人机交互入口。

    当 `type=chat` 时，返回值可能是异步生成器，
    前端可以边收流式文本，边等待数字人口播。
    """
    res = await process_human_interaction(
        sessionid=req.sessionid,
        interaction_type=req.type,
        text=req.text,
        interrupt=req.interrupt,
    )
    if isinstance(res, types.AsyncGeneratorType):
        return StreamingResponse(res, media_type="text/plain")
    return res


@router.post("/humanaudio")
async def human_audio_endpoint(
    sessionid: int = Form(0), file: UploadFile = File(...)
):
    """上传一段音频，直接塞进当前会话的音频处理队列。"""
    filebytes = await file.read()
    res = await process_human_audio(sessionid, filebytes)
    return res


@router.post("/set_audiotype")
async def set_audiotype_endpoint(req: AudioTypeRequest):
    """切换当前会话的自定义待机音频/动作状态。"""
    res = await set_audio_type(req.sessionid, req.audiotype, req.reinit)
    return res


@router.post("/interrupt_talk")
async def interrupt_talk_endpoint(req: SessionRequest):
    """强制中断当前数字人的播报。"""
    res = await interrupt_human_talk(req.sessionid)
    return res


@router.post("/is_speaking")
async def is_speaking_endpoint(req: SessionRequest):
    """查询当前数字人是否处于“正在说话”状态。"""
    res = await check_is_speaking(req.sessionid)
    return res
