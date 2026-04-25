"""
人脸检测子模块入口。

这一整套 `face_detection/` 更偏底层算法代码，
业务开发时通常把它当作“黑盒人脸检测器”来用就可以。
"""

# -*- coding: utf-8 -*-

__author__ = """Adrian Bulat"""
__email__ = 'adrian.bulat@nottingham.ac.uk'
__version__ = '1.0.1'

from .api import FaceAlignment, LandmarksType, NetworkSize
