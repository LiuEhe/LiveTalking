"""
数字人互动服务层。

这一层负责做三件事：
- 校验 session 是否存在
- 根据接口语义调用对应底层能力
- 把返回值整理成前端能直接消费的结构
"""

import asyncio
from utils.logger import logger
from servers.ai_server import llm_chat_stream
from servers import state


async def process_human_interaction(
    sessionid: int,
    interaction_type: str,
    text: str = None,
    interrupt: bool = False,
):
    """
    处理文本互动请求。

    `interaction_type` 常见值：
    - `echo`：直接播报输入文本
    - `chat`：调用 LLM 生成文本后再播报
    """
    if sessionid not in state.nerfreals:
        raise ValueError(f"Invalid sessionid: {sessionid}")

    if interrupt:
        # 先清空旧的 TTS / ASR 队列，避免新消息和旧消息串在一起。
        state.nerfreals[sessionid].flush_talk()

    if interaction_type == "echo":
        state.nerfreals[sessionid].put_msg_txt(text)
        return {"code": 0, "msg": "ok"}
    elif interaction_type == "chat":
        loop = asyncio.get_event_loop()
        output_queue = asyncio.Queue()

        # LLM 客户端是同步迭代流，因此这里放进线程池，不阻塞主事件循环。
        loop.run_in_executor(
            None, llm_chat_stream, text, state.nerfreals[sessionid], loop, output_queue
        )

        async def event_stream():
            """把后台线程产出的增量文本持续转成可流式返回的响应体。"""
            while True:
                msg = await output_queue.get()
                if msg is None:
                    break
                yield msg

        return event_stream()


async def process_human_audio(sessionid: int, filebytes: bytes):
    """把一整个音频文件塞进当前数字人的音频输入链路。"""
    if sessionid not in state.nerfreals:
        raise ValueError(f"Invalid sessionid: {sessionid}")
    state.nerfreals[sessionid].put_audio_file(filebytes)
    return {"code": 0, "msg": "ok"}


async def set_audio_type(sessionid: int, audiotype: str, reinit: bool):
    """切换到某个自定义音频/动作状态。"""
    if sessionid not in state.nerfreals:
        raise ValueError(f"Invalid sessionid: {sessionid}")
    state.nerfreals[sessionid].set_custom_state(audiotype, reinit)
    return {"code": 0, "msg": "ok"}


async def interrupt_human_talk(sessionid: int):
    """中断当前会话的讲话。"""
    if sessionid not in state.nerfreals:
        raise ValueError(f"Invalid sessionid: {sessionid}")
    state.nerfreals[sessionid].flush_talk()
    return {"code": 0, "msg": "ok"}


async def check_is_speaking(sessionid: int):
    """查询当前会话是否正在输出讲话帧。"""
    if sessionid not in state.nerfreals:
        raise ValueError(f"Invalid sessionid: {sessionid}")
    is_speaking = state.nerfreals[sessionid].is_speaking()
    return {"code": 0, "data": is_speaking}
