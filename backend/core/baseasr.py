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
ASR/音频特征抽取基类。

虽然这里文件名叫 `ASR`，但它在这个项目里的职责更接近：
- 接收外部送进来的音频帧
- 维护左右上下文窗口
- 产出后续口型模型需要的音频特征

可以把它理解成“音频进入口型模型前的中转站”。
"""

import time
import numpy as np

import queue
from queue import Queue
import torch.multiprocessing as mp

from core.basereal import BaseReal


class BaseASR:
    """
    音频处理基类。

    子类一般只需要重点实现 `run_step()`：
    - 从输入队列取音频
    - 计算特征
    - 把结果放进 `feat_queue`
    """

    def __init__(self, opt, parent:BaseReal = None):
        self.opt = opt
        self.parent = parent

        self.fps = opt.fps # 一秒被切成多少个音频帧，例如 50 表示每帧 20ms。
        self.sample_rate = 16000
        self.chunk = self.sample_rate // self.fps # 每个音频块包含多少个采样点。
        self.queue = Queue()
        self.output_queue = mp.Queue()

        self.batch_size = opt.batch_size

        # `frames` 保存最近一段滑动窗口音频，供特征提取时拼接上下文。
        self.frames = []
        self.stride_left_size = opt.l
        self.stride_right_size = opt.r
        #self.context_size = 10
        self.feat_queue = mp.Queue(2)

        #self.warm_up()

    def flush_talk(self):
        """清空尚未消费的输入音频，常用于“打断讲话”。"""
        self.queue.queue.clear()

    def put_audio_frame(self,audio_chunk,datainfo:dict): #16khz 20ms pcm
        """往输入队列塞一帧音频。"""
        self.queue.put((audio_chunk,datainfo))

    #return frame:audio pcm; type: 0-normal speak, 1-silence; eventpoint:custom event sync with audio
    def get_audio_frame(self):        
        """
        取出一帧音频。

        如果当前没有真实语音输入：
        - 且父对象处于自定义动作状态，则返回自定义音频
        - 否则返回一帧静音
        """
        try:
            frame,eventpoint = self.queue.get(block=True,timeout=0.01)
            type = 0
            #print(f'[INFO] get frame {frame.shape}')
        except queue.Empty:
            if self.parent and self.parent.curr_state>1: #播放自定义音频
                frame = self.parent.get_audio_stream(self.parent.curr_state)
                type = self.parent.curr_state
            else:
                frame = np.zeros(self.chunk, dtype=np.float32)
                type = 1
            eventpoint = None

        return frame,type,eventpoint 

    #return frame:audio pcm; type: 0-normal speak, 1-silence; eventpoint:custom event sync with audio
    def get_audio_out(self): 
        """获取已经准备好发往最终渲染链路的音频帧。"""
        return self.output_queue.get()
    
    def warm_up(self):
        """
        用静音/已有输入把左右上下文窗口先填满。

        这样第一次真正跑特征提取时，窗口长度就是完整的，不会一开始就缺上下文。
        """
        for _ in range(self.stride_left_size + self.stride_right_size):
            audio_frame,type,eventpoint=self.get_audio_frame()
            self.frames.append(audio_frame)
            self.output_queue.put((audio_frame,type,eventpoint))
        for _ in range(self.stride_left_size):
            self.output_queue.get()

    def run_step(self):
        """子类实现：执行一次“取音频 -> 产特征”的处理循环。"""
        pass

    def get_next_feat(self,block,timeout):        
        """从特征队列里取出下一个特征块。"""
        return self.feat_queue.get(block,timeout)
