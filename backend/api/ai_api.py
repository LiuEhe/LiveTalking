from fastapi import APIRouter
from pydantic import BaseModel
import asyncio
from servers.ai_server import llm_chat_stream
from servers import state
from core import Success

router = APIRouter(route_class=Success)

class ChatRequest(BaseModel):
    sessionid: int = 0
    text: str

@router.post("/chat")
async def chat_endpoint(req: ChatRequest):
    if req.sessionid not in state.nerfreals:
        return {"code": -1, "msg": f"Invalid sessionid: {req.sessionid}"}
    # Run sync function in thread pool so it can stream via put_msg_txt
    asyncio.get_event_loop().run_in_executor(None, llm_chat_stream, req.text, state.nerfreals[req.sessionid])
    return {"code": 0, "msg": "ok"}
