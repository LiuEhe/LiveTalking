"""
服务层统一导出。

`servers/` 可以理解为“业务编排层”：
- `api/` 负责接收请求
- `servers/` 负责调度具体业务流程
- `core/` 负责底层音视频 / 推理能力
"""

from .webrtc_server import close_all_connections
from .avatar_server import generate_avatar
from . import state

__all__ = ["close_all_connections", "generate_avatar", "state"]
