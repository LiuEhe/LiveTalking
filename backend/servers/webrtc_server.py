import asyncio
import json
import random
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceServer, RTCConfiguration
from aiortc.rtcrtpsender import RTCRtpSender
from webrtc import HumanPlayer
from logger import logger
from servers import state

def randN(N) -> int:
    min_val = pow(10, N - 1)
    max_val = pow(10, N)
    return random.randint(min_val, max_val - 1)

def build_nerfreal(sessionid: int):
    state.opt.sessionid = sessionid
    from lipreal import LipReal
    nerfreal = LipReal(state.opt, state.model, state.avatar)
    return nerfreal

async def process_offer(sdp: str, offer_type: str, sessionid: int = 0) -> dict:
    offer = RTCSessionDescription(sdp=sdp, type=offer_type)
    if not sessionid:
        sessionid = randN(6)
    state.nerfreals[sessionid] = None
    logger.info('sessionid=%d, session num=%d', sessionid, len(state.nerfreals))
    
    nerfreal = await asyncio.get_event_loop().run_in_executor(None, build_nerfreal, sessionid)
    state.nerfreals[sessionid] = nerfreal
    
    ice_server = RTCIceServer(urls='stun:stun.freeswitch.org:3478')
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

    player = HumanPlayer(state.nerfreals[sessionid])
    pc.addTrack(player.audio)
    pc.addTrack(player.video)
    
    capabilities = RTCRtpSender.getCapabilities("video")
    preferences = list(filter(lambda x: x.name == "H264", capabilities.codecs))
    preferences += list(filter(lambda x: x.name == "VP8", capabilities.codecs))
    preferences += list(filter(lambda x: x.name == "rtx", capabilities.codecs))
    transceiver = pc.getTransceivers()[1]
    transceiver.setCodecPreferences(preferences)

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type, "sessionid": sessionid}

async def close_all_connections():
    coros = [pc.close() for pc in state.pcs]
    await asyncio.gather(*coros)
    state.pcs.clear()
