"""
运行时全局状态。

这里保存的是“整个进程共享”的对象，而不是某个单独请求自己的局部变量。
典型内容包括：
- 已经建立的数字人会话对象
- 已建立的 WebRTC 连接
- 启动时加载好的模型、头像素材和配置

初学者可以把它类比成一个简单的内存注册表。
"""

from typing import Dict, Set
from aiortc import RTCPeerConnection

# 会话 id -> 数字人渲染对象。
nerfreals: Dict[int, "BaseReal"] = {}
# 当前进程中所有仍然活跃的 PeerConnection。
pcs: Set[RTCPeerConnection] = set()

# 启动时加载一次，然后被所有会话复用。
opt = None
model = None
avatar = None
