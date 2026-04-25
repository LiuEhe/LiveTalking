"""
大模型对话相关接口。

这个接口和 `/human` 的 `type=chat` 有些相似，
区别在于这里更偏“直接触发 LLM 回复”，而不是完整的人机交互流程入口。
"""

from fastapi import APIRouter
from pydantic import BaseModel
import asyncio
from servers.ai_server import llm_chat_stream
from servers import state
from core import Success

router = APIRouter(route_class=Success)


class ChatRequest(BaseModel):
    """`/chat` 接口的请求体。"""

    sessionid: int = 0
    text: str


@router.post("/chat")
async def chat_endpoint(req: ChatRequest):
    """
    调用 LLM 流式生成文本，并把结果送入当前会话的数字人口播队列。

    注意这里没有直接把完整结果返回给前端，而是把任务扔到线程池里异步执行。
    这样前端请求会很快返回，真正的语音播报由后台继续推进。
    """
    if req.sessionid not in state.nerfreals:
        return {"code": -1, "msg": f"Invalid sessionid: {req.sessionid}"}

    # llm_chat_stream 里会一边拿到 LLM token，一边按句子切分并投喂到 TTS。
    asyncio.get_event_loop().run_in_executor(
        None, llm_chat_stream, req.text, state.nerfreals[req.sessionid]
    )
    return {"code": 0, "msg": "ok"}
