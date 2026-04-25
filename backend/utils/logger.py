"""
项目级日志配置。

当前配置比较简单：
- 记录器级别：DEBUG
- 文件输出级别：INFO
- 输出文件：`livetalking.log`

如果你后面要做线上服务，通常会继续扩展：
- 控制台输出
- 按天切分日志
- JSON 结构化日志
- 不同模块的独立 logger
"""

import logging

# 获取当前模块对应的 logger；`__name__` 会变成导入这个文件时的模块名。
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# 当前默认写到项目根目录下的日志文件中。
fhandler = logging.FileHandler("livetalking.log")
fhandler.setFormatter(formatter)
fhandler.setLevel(logging.INFO)
logger.addHandler(fhandler)

# handler = logging.StreamHandler()
# handler.setLevel(logging.DEBUG)
# sformatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
# handler.setFormatter(sformatter)
# logger.addHandler(handler)
