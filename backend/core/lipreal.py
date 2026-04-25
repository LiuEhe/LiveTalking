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
Wav2Lip 数字人实现。

这个文件是项目里最关键的核心之一，负责把：
- 音频 mel 特征
- 人脸素材帧
- Wav2Lip 模型

串成一条真正可运行的“说话数字人”渲染链路。
"""

import math
import torch
import numpy as np

#from .utils import *
import os
import time
import cv2
import glob
import pickle
import copy

import queue
from queue import Queue
from threading import Thread, Event
import torch.multiprocessing as mp


from core.lipasr import LipASR
import asyncio
from av import AudioFrame, VideoFrame
from wav2lip.models import Wav2Lip
from core.basereal import BaseReal

#from imgcache import ImgCache

from tqdm import tqdm
from utils.logger import logger

device = (
    "cuda"
    if torch.cuda.is_available()
    else (
        "mps"
        if (hasattr(torch.backends, "mps") and torch.backends.mps.is_available())
        else "cpu"
    )
)
print("Using {} for inference.".format(device))


def _load(checkpoint_path):
    """按当前设备加载模型权重文件。"""
    if device == "cuda":
        checkpoint = torch.load(checkpoint_path)
    else:
        checkpoint = torch.load(
            checkpoint_path, map_location=lambda storage, loc: storage
        )
    return checkpoint


def load_model(path):
    """加载 Wav2Lip 权重，并切到推理模式。"""
    model = Wav2Lip()
    logger.info("Load checkpoint from: {}".format(path))
    checkpoint = _load(path)
    s = checkpoint["state_dict"]
    new_s = {}
    for k, v in s.items():
        new_s[k.replace("module.", "")] = v
    model.load_state_dict(new_s)

    model = model.to(device)
    return model.eval()


def load_avatar(avatar_id):
    """
    读取某个 avatar 的全部静态素材。

    返回三组关键数据：
    - `frame_list_cycle`：完整原图序列
    - `face_list_cycle`：裁好的人脸序列
    - `coord_list_cycle`：每一帧人脸在原图中的坐标
    """
    avatar_path = f"./data/avatars/{avatar_id}"
    full_imgs_path = f"{avatar_path}/full_imgs"
    face_imgs_path = f"{avatar_path}/face_imgs"
    coords_path = f"{avatar_path}/coords.pkl"

    with open(coords_path, "rb") as f:
        coord_list_cycle = pickle.load(f)
    input_img_list = glob.glob(os.path.join(full_imgs_path, "*.[jpJP][pnPN]*[gG]"))
    input_img_list = sorted(
        input_img_list, key=lambda x: int(os.path.splitext(os.path.basename(x))[0])
    )
    frame_list_cycle = read_imgs(input_img_list)
    input_face_list = glob.glob(os.path.join(face_imgs_path, "*.[jpJP][pnPN]*[gG]"))
    input_face_list = sorted(
        input_face_list, key=lambda x: int(os.path.splitext(os.path.basename(x))[0])
    )
    face_list_cycle = read_imgs(input_face_list)

    return frame_list_cycle, face_list_cycle, coord_list_cycle


@torch.no_grad()
def warm_up(batch_size, model, modelres):
    """用假数据跑一次前向，降低首个真实请求的冷启动延迟。"""
    logger.info("warmup model...")
    img_batch = torch.ones(batch_size, 6, modelres, modelres).to(device)
    mel_batch = torch.ones(batch_size, 1, 80, 16).to(device)
    model(mel_batch, img_batch)


def read_imgs(img_list):
    """批量读取图片到内存。"""
    frames = []
    logger.info("reading images...")
    for img_path in tqdm(img_list):
        frame = cv2.imread(img_path)
        frames.append(frame)
    return frames


def __mirror_index(size, index):
    """生成来回摆动的循环索引，用于更自然地轮播头像帧。"""
    turn = index // size
    res = index % size
    if turn % 2 == 0:
        return res
    else:
        return size - res - 1


def inference(
    quit_event,
    batch_size,
    face_list_cycle,
    audio_feat_queue,
    audio_out_queue,
    res_frame_queue,
    model,
):
    """
    后台推理线程。

    它的输入是：
    - 音频特征队列 `audio_feat_queue`
    - 音频原始输出队列 `audio_out_queue`

    它的输出是：
    - `res_frame_queue`，其中每项都包含
      “预测嘴型帧 / 对应头像索引 / 对应音频帧”
    """
    length = len(face_list_cycle)
    index = 0
    count = 0
    counttime = 0
    logger.info("start inference")
    while not quit_event.is_set():
        starttime = time.perf_counter()
        mel_batch = []
        try:
            mel_batch = audio_feat_queue.get(block=True, timeout=1)
        except queue.Empty:
            continue

        # 这里要同时拿到“模型特征”和“最终音频帧”，这样视频和音频才能对齐输出。
        is_all_silence = True
        audio_frames = []
        for _ in range(batch_size * 2):
            frame, type, eventpoint = audio_out_queue.get()
            audio_frames.append((frame, type, eventpoint))
            if type == 0:
                is_all_silence = False

        if is_all_silence:
            # 如果整批都是静音，就不跑模型，直接通知后续链路使用原头像帧/待机帧。
            for i in range(batch_size):
                res_frame_queue.put(
                    (None, __mirror_index(length, index), audio_frames[i * 2 : i * 2 + 2])
                )
                index = index + 1
        else:
            # 非静音才真正执行 Wav2Lip 推理。
            t = time.perf_counter()
            img_batch = []
            for i in range(batch_size):
                idx = __mirror_index(length, index + i)
                face = face_list_cycle[idx]
                img_batch.append(face)
            img_batch, mel_batch = np.asarray(img_batch), np.asarray(mel_batch)

            # Wav2Lip 经典做法：把嘴部以下区域 mask 掉，再和原图拼接作为输入。
            img_masked = img_batch.copy()
            img_masked[:, face.shape[0] // 2 :] = 0

            img_batch = np.concatenate((img_masked, img_batch), axis=3) / 255.0
            mel_batch = np.reshape(
                mel_batch, [len(mel_batch), mel_batch.shape[1], mel_batch.shape[2], 1]
            )

            img_batch = torch.FloatTensor(np.transpose(img_batch, (0, 3, 1, 2))).to(device)
            mel_batch = torch.FloatTensor(np.transpose(mel_batch, (0, 3, 1, 2))).to(device)

            with torch.no_grad():
                pred = model(mel_batch, img_batch)
            pred = pred.cpu().numpy().transpose(0, 2, 3, 1) * 255.0

            counttime += time.perf_counter() - t
            count += batch_size
            if count >= 100:
                logger.info(f"------actual avg infer fps:{count / counttime:.4f}")
                count = 0
                counttime = 0
            for i, res_frame in enumerate(pred):
                res_frame_queue.put(
                    (
                        res_frame,
                        __mirror_index(length, index),
                        audio_frames[i * 2 : i * 2 + 2],
                    )
                )
                index = index + 1
    logger.info("lipreal inference processor stop")


class LipReal(BaseReal):
    """基于 Wav2Lip 的具体数字人实现。"""

    @torch.no_grad()
    def __init__(self, opt, model, avatar):
        super().__init__(opt)

        self.fps = opt.fps

        self.batch_size = opt.batch_size
        self.idx = 0
        # 推理线程会把“嘴型帧 + 音频帧”写到这里，渲染线程再继续消费。
        self.res_frame_queue = Queue(self.batch_size * 2)
        self.model = model
        self.frame_list_cycle, self.face_list_cycle, self.coord_list_cycle = avatar

        # `LipASR` 负责把音频切块并提取 mel 特征。
        self.asr = LipASR(opt, self)
        self.asr.warm_up()

        self.render_event = mp.Event()

    def paste_back_frame(self, pred_frame, idx: int):
        """
        把模型预测的人脸结果贴回原始头像帧。

        `coord_list_cycle[idx]` 记录了这一帧脸在原图中的位置，
        所以这里只需要 resize 后覆盖回去。
        """
        bbox = self.coord_list_cycle[idx]
        combine_frame = copy.deepcopy(self.frame_list_cycle[idx])
        y1, y2, x1, x2 = bbox
        res_frame = cv2.resize(pred_frame.astype(np.uint8), (x2 - x1, y2 - y1))
        combine_frame[y1:y2, x1:x2] = res_frame
        return combine_frame

    def render(self, quit_event, loop=None, audio_track=None, video_track=None):
        """
        整体渲染主循环。

        这个方法会同时拉起两个后台线程：
        - `inference`：负责根据音频特征跑嘴型推理
        - `process_frames`：负责把推理结果和音频封装成最终输出

        而当前线程自己则持续执行 `self.asr.run_step()`，
        负责不断把新的音频送进特征提取链路。
        """
        self.init_customindex()
        self.tts.render(quit_event)

        infer_quit_event = Event()
        infer_thread = Thread(
            target=inference,
            args=(
                infer_quit_event,
                self.batch_size,
                self.face_list_cycle,
                self.asr.feat_queue,
                self.asr.output_queue,
                self.res_frame_queue,
                self.model,
            ),
        )
        infer_thread.start()

        process_quit_event = Event()
        process_thread = Thread(
            target=self.process_frames,
            args=(process_quit_event, loop, audio_track, video_track),
        )
        process_thread.start()

        count = 0
        totaltime = 0
        _starttime = time.perf_counter()
        while not quit_event.is_set():
            # 每次循环都推进一次音频特征提取，相当于渲染链路的“节拍器”。
            t = time.perf_counter()
            self.asr.run_step()

            if video_track and video_track._queue.qsize() >= 5:
                # 当发送队列堆积过多时稍微休眠，避免下游消费跟不上导致内存增长。
                logger.debug("sleep qsize=%d", video_track._queue.qsize())
                time.sleep(0.04 * video_track._queue.qsize() * 0.8)

        logger.info("lipreal thread stop")

        infer_quit_event.set()
        infer_thread.join()

        process_quit_event.set()
        process_thread.join()
