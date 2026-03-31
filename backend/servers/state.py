from typing import Dict, Set
from aiortc import RTCPeerConnection

# Global state
nerfreals: Dict[int, 'BaseReal'] = {} # sessionid: BaseReal
pcs: Set[RTCPeerConnection] = set()

opt = None
model = None
avatar = None
