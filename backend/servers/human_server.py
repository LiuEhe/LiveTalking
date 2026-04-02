import asyncio
from logger import logger
from servers.ai_server import llm_chat_stream
from servers import state

async def process_human_interaction(sessionid: int, interaction_type: str, text: str = None, interrupt: bool = False):
    if sessionid not in state.nerfreals:
        raise ValueError(f"Invalid sessionid: {sessionid}")

    if interrupt:
        state.nerfreals[sessionid].flush_talk()

    if interaction_type == 'echo':
        state.nerfreals[sessionid].put_msg_txt(text)
    elif interaction_type == 'chat':
        asyncio.get_event_loop().run_in_executor(None, llm_chat_stream, text, state.nerfreals[sessionid])
        
    return {"code": 0, "msg": "ok"}

async def process_human_audio(sessionid: int, filebytes: bytes):
    if sessionid not in state.nerfreals:
        raise ValueError(f"Invalid sessionid: {sessionid}")
    state.nerfreals[sessionid].put_audio_file(filebytes)
    return {"code": 0, "msg": "ok"}

async def set_audio_type(sessionid: int, audiotype: str, reinit: bool):
    if sessionid not in state.nerfreals:
        raise ValueError(f"Invalid sessionid: {sessionid}")
    state.nerfreals[sessionid].set_custom_state(audiotype, reinit)
    return {"code": 0, "msg": "ok"}

async def interrupt_human_talk(sessionid: int):
    if sessionid not in state.nerfreals:
        raise ValueError(f"Invalid sessionid: {sessionid}")
    state.nerfreals[sessionid].flush_talk()
    return {"code": 0, "msg": "ok"}

async def check_is_speaking(sessionid: int):
    if sessionid not in state.nerfreals:
        raise ValueError(f"Invalid sessionid: {sessionid}")
    is_speaking = state.nerfreals[sessionid].is_speaking()
    return {"code": 0, "data": is_speaking}
