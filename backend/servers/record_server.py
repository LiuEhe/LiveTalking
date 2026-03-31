from servers import state

async def handle_record_action(sessionid: int, record_type: str):
    if sessionid not in state.nerfreals:
        raise ValueError(f"Invalid sessionid: {sessionid}")
        
    if record_type == 'start_record':
        state.nerfreals[sessionid].start_recording()
    elif record_type == 'end_record':
        state.nerfreals[sessionid].stop_recording()
        
    return {"code": 0, "msg": "ok"}
