###############################################################################
#  Copyright (C) 2024 LiveTalking@lipku https://github.com/lipku/LiveTalking
#  email: lipku@foxmail.com
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################

"""
数字人渲染基类。

可以把这个类理解成“数字人运行时总控”：
- 上游接文字或音频
- 中间协调 TTS、ASR、推理结果和自定义动作
- 下游输出视频帧、音频帧，以及可选录制结果

`LipReal` 等具体实现会继承它，并补齐“如何生成嘴型帧”的细节。
"""

import math
import torch
import numpy as np

import subprocess
import os
import time
import cv2
import glob
import resampy

import queue
from queue import Queue
from threading import Thread, Event
from io import BytesIO
import soundfile as sf
import asyncio
from av import AudioFrame, VideoFrame
import av
from fractions import Fraction
from core.ttsreal import (
    EdgeTTS,
    SovitsTTS,
    XTTS,
    CosyVoiceTTS,
    FishTTS,
    TencentTTS,
    DoubaoTTS,
    IndexTTS2,
    AzureTTS,
)
from utils.logger import logger
# import pyaudio
# import pyvirtualcam


from tqdm import tqdm


def read_imgs(img_list):
    """把一组图片路径批量读进内存。"""
    frames = []
    logger.info("reading images...")
    for img_path in tqdm(img_list):
        frame = cv2.imread(img_path)
        frames.append(frame)
    return frames


def play_audio(quit_event, queue):
    """虚拟摄像头模式下，把 PCM 音频直接播放到本地声卡。"""
    if pyaudio is None:
        logger.error("pyaudio not installed")
        return
    p = pyaudio.PyAudio()
    stream = p.open(
        rate=16000,
        channels=1,
        format=8,
        output=True,
        output_device_index=1,
    )
    stream.start_stream()
    while not quit_event.is_set():
        stream.write(queue.get(block=True))
    stream.close()


class BaseReal:
    """
    数字人运行时基类。

    这个类本身并不负责“推理嘴型”，而是负责把整条链路粘起来：
    - 选择 TTS 后端
    - 接收外部文本/音频输入
    - 管理录制
    - 在静音和说话之间切换显示帧
    """

    def __init__(self, opt):
        self.opt = opt
        self.sample_rate = 16000
        self.chunk = self.sample_rate // opt.fps  # 20ms 音频块对应的采样点数。
        self.sessionid = self.opt.sessionid

        # 根据配置选择具体的 TTS 实现。
        if opt.tts == "edgetts":
            self.tts = EdgeTTS(opt, self)
        elif opt.tts == "gpt-sovits":
            self.tts = SovitsTTS(opt, self)
        elif opt.tts == "xtts":
            self.tts = XTTS(opt, self)
        elif opt.tts == "cosyvoice":
            self.tts = CosyVoiceTTS(opt, self)
        elif opt.tts == "fishtts":
            self.tts = FishTTS(opt, self)
        elif opt.tts == "tencent":
            self.tts = TencentTTS(opt, self)
        elif opt.tts == "doubao":
            self.tts = DoubaoTTS(opt, self)
        elif opt.tts == "indextts2":
            self.tts = IndexTTS2(opt, self)
        elif opt.tts == "azuretts":
            self.tts = AzureTTS(opt, self)

        # 这个标记会被前端 `/is_speaking` 等接口拿去判断当前数字人状态。
        self.speaking = False

        # 录制相关句柄。
        self.recording = False
        self._record_video_pipe = None
        self._record_audio_pipe = None
        self.width = self.height = 0

        # 自定义动作状态相关字段：
        # - 0 通常表示正常推理态
        # - 其他值通常对应某种自定义待机音频/动作
        self.curr_state = 0
        self.custom_img_cycle = {}
        self.custom_audio_cycle = {}
        self.custom_audio_index = {}
        self.custom_index = {}
        self.custom_opt = {}
        self.__loadcustom()

    def put_msg_txt(self, msg, datainfo: dict = {}):
        """把文本交给 TTS 模块，由它继续转成音频帧。"""
        self.tts.put_msg_txt(msg, datainfo)

    def put_audio_frame(self, audio_chunk, datainfo: dict = {}):  # 16khz 20ms pcm
        """直接往音频处理链路推入一帧 16k PCM。"""
        self.asr.put_audio_frame(audio_chunk, datainfo)

    def put_audio_file(self, filebyte, datainfo: dict = {}):
        """
        把整段音频文件拆成固定 chunk，再逐帧送入 ASR/特征提取链路。

        初学者可以把它理解成：
        “把一整个 wav 文件切成很多 20ms 小片段，再像流式音频一样喂进去”。
        """
        input_stream = BytesIO(filebyte)
        stream = self.__create_bytes_stream(input_stream)
        streamlen = stream.shape[0]
        idx = 0
        while streamlen >= self.chunk:
            self.put_audio_frame(stream[idx : idx + self.chunk], datainfo)
            streamlen -= self.chunk
            idx += self.chunk

    def __create_bytes_stream(self, byte_stream):
        """把字节流解析成单声道、16kHz 的 float32 音频数组。"""
        stream, sample_rate = sf.read(byte_stream)
        logger.info(f"[INFO]put audio stream {sample_rate}: {stream.shape}")
        stream = stream.astype(np.float32)

        if stream.ndim > 1:
            logger.info(f"[WARN] audio has {stream.shape[1]} channels, only use the first.")
            stream = stream[:, 0]

        if sample_rate != self.sample_rate and stream.shape[0] > 0:
            logger.info(
                f"[WARN] audio sample rate is {sample_rate}, resampling into {self.sample_rate}."
            )
            stream = resampy.resample(
                x=stream, sr_orig=sample_rate, sr_new=self.sample_rate
            )

        return stream

    def flush_talk(self):
        """同时清空 TTS 和 ASR 队列，常用于打断当前对话。"""
        self.tts.flush_talk()
        self.asr.flush_talk()

    def is_speaking(self) -> bool:
        """返回当前数字人是否正在输出讲话内容。"""
        return self.speaking

    def __loadcustom(self):
        """
        加载自定义动作素材。

        每个动作通常包含：
        - 一组循环播放的图片
        - 一段对应音频
        - 一个 `audiotype` 作为动作编号
        """
        for item in self.opt.customopt:
            logger.info(item)
            input_img_list = glob.glob(os.path.join(item["imgpath"], "*.[jpJP][pnPN]*[gG]"))
            input_img_list = sorted(
                input_img_list, key=lambda x: int(os.path.splitext(os.path.basename(x))[0])
            )
            self.custom_img_cycle[item["audiotype"]] = read_imgs(input_img_list)
            self.custom_audio_cycle[item["audiotype"]], sample_rate = sf.read(
                item["audiopath"], dtype="float32"
            )
            self.custom_audio_index[item["audiotype"]] = 0
            self.custom_index[item["audiotype"]] = 0
            self.custom_opt[item["audiotype"]] = item

    def init_customindex(self):
        """重置所有自定义动作的播放游标。"""
        self.curr_state = 0
        for key in self.custom_audio_index:
            self.custom_audio_index[key] = 0
        for key in self.custom_index:
            self.custom_index[key] = 0

    def notify(self, eventpoint):
        """接收音频事件点回调，例如句子开始/结束。"""
        logger.info("notify:%s", eventpoint)

    def start_recording(self):
        """启动录制，把视频和音频分别送进两个 ffmpeg 进程。"""
        if self.recording:
            return

        command = [
            "ffmpeg",
            "-y",
            "-an",
            "-f",
            "rawvideo",
            "-vcodec",
            "rawvideo",
            "-pix_fmt",
            "bgr24",
            "-s",
            "{}x{}".format(self.width, self.height),
            "-r",
            str(25),
            "-i",
            "-",
            "-pix_fmt",
            "yuv420p",
            "-vcodec",
            "h264",
            f"temp{self.opt.sessionid}.mp4",
        ]
        self._record_video_pipe = subprocess.Popen(
            command, shell=False, stdin=subprocess.PIPE
        )

        acommand = [
            "ffmpeg",
            "-y",
            "-vn",
            "-f",
            "s16le",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-i",
            "-",
            "-acodec",
            "aac",
            f"temp{self.opt.sessionid}.aac",
        ]
        self._record_audio_pipe = subprocess.Popen(
            acommand, shell=False, stdin=subprocess.PIPE
        )

        self.recording = True

    def record_video_data(self, image):
        """向录制中的视频管道写入一帧原始图像。"""
        if self.width == 0:
            print("image.shape:", image.shape)
            self.height, self.width, _ = image.shape
        if self.recording:
            self._record_video_pipe.stdin.write(image.tostring())

    def record_audio_data(self, frame):
        """向录制中的音频管道写入一帧 PCM 数据。"""
        if self.recording:
            self._record_audio_pipe.stdin.write(frame.tostring())

    # def record_frame(self):
    #     videostream = self.container.add_stream("libx264", rate=25)
    #     videostream.codec_context.time_base = Fraction(1, 25)
    #     audiostream = self.container.add_stream("aac")
    #     audiostream.codec_context.time_base = Fraction(1, 16000)
    #     init = True
    #     framenum = 0
    #     while self.recording:
    #         try:
    #             videoframe = self.recordq_video.get(block=True, timeout=1)
    #             videoframe.pts = framenum
    #             videoframe.dts = videoframe.pts
    #             if init:
    #                 videostream.width = videoframe.width
    #                 videostream.height = videoframe.height
    #                 init = False
    #             for packet in videostream.encode(videoframe):
    #                 self.container.mux(packet)
    #             for k in range(2):
    #                 audioframe = self.recordq_audio.get(block=True, timeout=1)
    #                 audioframe.pts = int(round((framenum * 2 + k) * 0.02 / audiostream.codec_context.time_base))
    #                 audioframe.dts = audioframe.pts
    #                 for packet in audiostream.encode(audioframe):
    #                     self.container.mux(packet)
    #             framenum += 1
    #         except queue.Empty:
    #             print('record queue empty,')
    #             continue
    #         except Exception as e:
    #             print(e)
    #     for packet in videostream.encode(None):
    #         self.container.mux(packet)
    #     for packet in audiostream.encode(None):
    #         self.container.mux(packet)
    #     self.container.close()
    #     self.recordq_video.queue.clear()
    #     self.recordq_audio.queue.clear()

    def stop_recording(self):
        """停止录制，并把临时音频/视频文件合成为最终 mp4。"""
        if not self.recording:
            return
        self.recording = False
        self._record_video_pipe.stdin.close()
        self._record_video_pipe.wait()
        self._record_audio_pipe.stdin.close()
        self._record_audio_pipe.wait()
        cmd_combine_audio = (
            f"ffmpeg -y -i temp{self.opt.sessionid}.aac -i temp{self.opt.sessionid}.mp4 "
            "-c:v copy -c:a copy data/record.mp4"
        )
        os.system(cmd_combine_audio)

    def mirror_index(self, size, index):
        """
        生成“来回摆动”的索引。

        例子：
        - 原始序列 `0,1,2,3`
        - 镜像循环后变成 `0,1,2,3,2,1,0,1...`

        这样播放头像帧时，比单纯从头循环更自然。
        """
        turn = index // size
        res = index % size
        if turn % 2 == 0:
            return res
        else:
            return size - res - 1

    def get_audio_stream(self, audiotype):
        """从某个自定义动作里取下一段音频。"""
        idx = self.custom_audio_index[audiotype]
        stream = self.custom_audio_cycle[audiotype][idx : idx + self.chunk]
        self.custom_audio_index[audiotype] += self.chunk
        if self.custom_audio_index[audiotype] >= self.custom_audio_cycle[audiotype].shape[0]:
            self.curr_state = 1
        return stream

    def set_custom_state(self, audiotype, reinit=True):
        """切换到指定自定义动作状态。"""
        print("set_custom_state:", audiotype)
        if self.custom_audio_index.get(audiotype) is None:
            return
        self.curr_state = audiotype
        if reinit:
            self.custom_audio_index[audiotype] = 0
            self.custom_index[audiotype] = 0

    def process_frames(self, quit_event, loop=None, audio_track=None, video_track=None):
        """
        把推理结果和音频帧真正组装成最终输出。

        这是本文件最关键的方法之一：
        - 从 `res_frame_queue` 取出一批“嘴型结果 + 对应音频”
        - 如果是静音，就显示待机帧或自定义动作帧
        - 如果是说话，就把嘴型区域贴回原始头像帧
        - 最后输出到 WebRTC 或虚拟摄像头
        """
        enable_transition = False

        if enable_transition:
            _last_speaking = False
            _transition_start = time.time()
            _transition_duration = 0.1
            _last_silent_frame = None
            _last_speaking_frame = None

        if self.opt.transport == "virtualcam":
            if pyvirtualcam is None:
                logger.error("pyvirtualcam not installed")
                return
            vircam = None

            audio_tmp = queue.Queue(maxsize=3000)
            audio_thread = Thread(
                target=play_audio,
                args=(quit_event, audio_tmp),
                daemon=True,
                name="pyaudio_stream",
            )
            audio_thread.start()

        while not quit_event.is_set():
            try:
                res_frame, idx, audio_frames = self.res_frame_queue.get(block=True, timeout=1)
            except queue.Empty:
                continue

            if enable_transition:
                current_speaking = not (audio_frames[0][1] != 0 and audio_frames[1][1] != 0)
                if current_speaking != _last_speaking:
                    logger.info(
                        f"状态切换：{'说话' if _last_speaking else '静音'} → {'说话' if current_speaking else '静音'}"
                    )
                    _transition_start = time.time()
                _last_speaking = current_speaking

            # 两个音频子帧都不是正常语音时，认为当前处于静音/待机状态。
            if audio_frames[0][1] != 0 and audio_frames[1][1] != 0:
                self.speaking = False
                audiotype = audio_frames[0][1]
                if self.custom_index.get(audiotype) is not None:
                    # 如果配置了自定义待机视频，就走自定义动作帧。
                    mirindex = self.mirror_index(
                        len(self.custom_img_cycle[audiotype]),
                        self.custom_index[audiotype],
                    )
                    target_frame = self.custom_img_cycle[audiotype][mirindex]
                    self.custom_index[audiotype] += 1
                else:
                    # 否则直接用原始头像帧循环播放。
                    target_frame = self.frame_list_cycle[idx]

                if enable_transition:
                    if (
                        time.time() - _transition_start < _transition_duration
                        and _last_speaking_frame is not None
                    ):
                        alpha = min(
                            1.0, (time.time() - _transition_start) / _transition_duration
                        )
                        combine_frame = cv2.addWeighted(
                            _last_speaking_frame, 1 - alpha, target_frame, alpha, 0
                        )
                    else:
                        combine_frame = target_frame
                    _last_silent_frame = combine_frame.copy()
                else:
                    combine_frame = target_frame
            else:
                self.speaking = True
                try:
                    # 说话状态下，把模型预测出来的嘴型区域贴回原图。
                    current_frame = self.paste_back_frame(res_frame, idx)
                except Exception as e:
                    logger.warning(f"paste_back_frame error: {e}")
                    continue
                if enable_transition:
                    if (
                        time.time() - _transition_start < _transition_duration
                        and _last_silent_frame is not None
                    ):
                        alpha = min(
                            1.0, (time.time() - _transition_start) / _transition_duration
                        )
                        combine_frame = cv2.addWeighted(
                            _last_silent_frame, 1 - alpha, current_frame, alpha, 0
                        )
                    else:
                        combine_frame = current_frame
                    _last_speaking_frame = combine_frame.copy()
                else:
                    combine_frame = current_frame

            cv2.putText(
                combine_frame,
                "LiveTalking",
                (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.3,
                (128, 128, 128),
                1,
            )
            if self.opt.transport == "virtualcam":
                if vircam == None:
                    height, width, _ = combine_frame.shape
                    vircam = pyvirtualcam.Camera(
                        width=width,
                        height=height,
                        fps=25,
                        fmt=pyvirtualcam.PixelFormat.BGR,
                        print_fps=True,
                    )
                vircam.send(combine_frame)
            else:
                image = combine_frame
                new_frame = VideoFrame.from_ndarray(image, format="bgr24")
                asyncio.run_coroutine_threadsafe(video_track._queue.put((new_frame, None)), loop)
            self.record_video_data(combine_frame)

            for audio_frame in audio_frames:
                frame, type, eventpoint = audio_frame
                frame = (frame * 32767).astype(np.int16)

                if self.opt.transport == "virtualcam":
                    audio_tmp.put(frame.tobytes())
                else:
                    # WebRTC 需要的是 `AudioFrame` 对象，而不是原始 numpy 数组。
                    new_frame = AudioFrame(
                        format="s16", layout="mono", samples=frame.shape[0]
                    )
                    new_frame.planes[0].update(frame.tobytes())
                    new_frame.sample_rate = 16000
                    asyncio.run_coroutine_threadsafe(
                        audio_track._queue.put((new_frame, eventpoint)), loop
                    )
                self.record_audio_data(frame)
            if self.opt.transport == "virtualcam":
                vircam.sleep_until_next_frame()
        if self.opt.transport == "virtualcam":
            audio_thread.join()
            vircam.close()
        logger.info("basereal process_frames thread stop")
