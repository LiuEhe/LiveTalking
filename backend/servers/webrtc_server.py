"""
WebRTC 会话服务。

这是“前端看到数字人视频”的真正关键入口：
1. 接收浏览器发来的 SDP offer
2. 为本次连接创建一个新的数字人会话对象
3. 把数字人产生的音轨、视频轨绑定到 aiortc 的连接里
4. 返回 answer，完成协商
"""

import asyncio
import json
import random
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceServer, RTCConfiguration
from aiortc.rtcrtpsender import RTCRtpSender
from core.webrtc import HumanPlayer
from utils.logger import logger
from core.lipreal import LipReal
from servers import state


def randN(N) -> int:
    """生成一个 N 位随机整数，常用于创建 sessionid。"""
    min_val = pow(10, N - 1)
    max_val = pow(10, N)
    return random.randint(min_val, max_val - 1)


def build_nerfreal(sessionid: int):
    """
    为某个会话实例化数字人对象。

    注意这里不是重新加载模型，而是复用启动时已经加载好的全局模型和头像素材。
    所以它创建的是“会话级对象”，不是“模型级对象”。
    """
    state.opt.sessionid = sessionid
    nerfreal = LipReal(state.opt, state.model, state.avatar)
    return nerfreal


async def process_offer(sdp: str, offer_type: str, sessionid: int = 0) -> dict:
    """
    处理浏览器发来的 offer，并返回 answer。

    返回值里除了标准 SDP 信息，还会附带一个 `sessionid`，
    前端后续调用 `/human`、`/record` 等接口时都要带上它。
    """
    offer = RTCSessionDescription(sdp=sdp, type=offer_type)
    if not sessionid:
        sessionid = randN(6)
    state.nerfreals[sessionid] = None
    logger.info("sessionid=%d, session num=%d", sessionid, len(state.nerfreals))

    # 创建数字人对象可能涉及线程、队列和较重初始化，因此放进线程池。
    nerfreal = await asyncio.get_event_loop().run_in_executor(None, build_nerfreal, sessionid)
    state.nerfreals[sessionid] = nerfreal

    ice_server = RTCIceServer(urls="stun:stun.freeswitch.org:3478")
    pc = RTCPeerConnection(configuration=RTCConfiguration(iceServers=[ice_server]))
    state.pcs.add(pc)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        logger.info("Connection state is %s" % pc.connectionState)
        if pc.connectionState == "failed":
            await pc.close()
            state.pcs.discard(pc)
            if sessionid in state.nerfreals:
                del state.nerfreals[sessionid]
        if pc.connectionState == "closed":
            state.pcs.discard(pc)
            if sessionid in state.nerfreals:
                del state.nerfreals[sessionid]

    # HumanPlayer 会把数字人渲染对象包装成 WebRTC 可消费的音轨和视频轨。
    player = HumanPlayer(state.nerfreals[sessionid])
    pc.addTrack(player.audio)
    pc.addTrack(player.video)

    # 优先使用 H264 / VP8 这类浏览器常见编码器，提高兼容性。
    capabilities = RTCRtpSender.getCapabilities("video")
    preferences = list(filter(lambda x: x.name == "H264", capabilities.codecs))
    preferences += list(filter(lambda x: x.name == "VP8", capabilities.codecs))
    preferences += list(filter(lambda x: x.name == "rtx", capabilities.codecs))
    transceiver = pc.getTransceivers()[1]
    transceiver.setCodecPreferences(preferences)

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return {
        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type,
        "sessionid": sessionid,
    }


async def close_all_connections():
    """在应用关闭时，统一断开当前所有 WebRTC 连接。"""
    coros = [pc.close() for pc in state.pcs]
    await asyncio.gather(*coros)
    state.pcs.clear()
