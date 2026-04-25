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
Wav2Lip 使用的音频特征提取器。

这个类继承自 `BaseASR`，核心工作是把一段连续音频转换成 mel 频谱块，
后面的口型模型会根据这些 mel 特征来预测嘴部区域应该长什么样。
"""

import time
import torch
import numpy as np

import queue
from queue import Queue
#import multiprocessing as mp

from core.baseasr import BaseASR
from wav2lip import audio

class LipASR(BaseASR):
    """为 Wav2Lip 模型准备 mel 特征的具体实现。"""

    def run_step(self):
        """
        执行一次特征提取。

        流程可以简化理解成：
        1. 取出一批音频帧
        2. 拼成连续波形
        3. 计算 mel 频谱
        4. 切成和视频帧对齐的小块，送入特征队列
        """
        ############################################## extract audio feature ##############################################
        # 一次取 `batch_size * 2` 个音频帧，是因为视频 25fps、音频通常按 50fps 切块。
        for _ in range(self.batch_size*2):
            frame,type,eventpoint = self.get_audio_frame()
            self.frames.append(frame)
            # 输出队列给后续最终音频播放/推流使用，和特征提取并行存在。
            self.output_queue.put((frame,type,eventpoint))
        # 上下文不足时，先不做特征提取，继续攒窗口。
        if len(self.frames) <= self.stride_left_size + self.stride_right_size:
            return
        
        inputs = np.concatenate(self.frames) # [N * chunk]
        mel = audio.melspectrogram(inputs)
        # 左右 stride 是上下文区，不应该直接当作当前时刻的预测主内容。
        left = max(0, self.stride_left_size*80/50)
        right = min(len(mel[0]), len(mel[0]) - self.stride_right_size*80/50)
        mel_idx_multiplier = 80.*2/self.fps 
        mel_step_size = 16
        i = 0
        mel_chunks = []
        while i < (len(self.frames)-self.stride_left_size-self.stride_right_size)/2:
            start_idx = int(left + i * mel_idx_multiplier)
            #print(start_idx)
            if start_idx + mel_step_size > len(mel[0]):
                mel_chunks.append(mel[:, len(mel[0]) - mel_step_size:])
            else:
                mel_chunks.append(mel[:, start_idx : start_idx + mel_step_size])
            i += 1
        self.feat_queue.put(mel_chunks)
        
        # 只保留下一轮还会用到的上下文窗口，避免 frames 无限增长。
        self.frames = self.frames[-(self.stride_left_size + self.stride_right_size):]
