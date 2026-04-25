"""
录制服务层。

真正的录制动作由 `BaseReal` 及其子类负责，
这里主要做会话查找和动作分发。
"""

from servers import state


async def handle_record_action(sessionid: int, record_type: str):
    """根据 `record_type` 决定开始录制还是停止录制。"""
    if sessionid not in state.nerfreals:
        raise ValueError(f"Invalid sessionid: {sessionid}")

    if record_type == "start_record":
        state.nerfreals[sessionid].start_recording()
    elif record_type == "end_record":
        state.nerfreals[sessionid].stop_recording()

    return {"code": 0, "msg": "ok"}
