"""
大模型流式回复服务。

这个文件做的事情不是“直接把完整答案一次性算完”，
而是边从 LLM 拿 token，边做两件事：
1. 把原始文本增量推给前端，形成流式显示效果。
2. 按标点把文本切成适合口播的小句子，送到 TTS 队列。
"""

import time
from core.basereal import BaseReal
from utils.logger import logger
from servers import state
from openai import OpenAI

import asyncio


def llm_chat_stream(message: str, nerfreal, loop=None, output_queue=None):
    """
    发起一次流式聊天请求，并把结果同步给前端和数字人口播链路。

    参数说明：
    - `message`：用户输入文本
    - `nerfreal`：当前会话对应的数字人对象，用于继续投喂 TTS
    - `loop/output_queue`：可选，用于把流式文本回推给前端
    """
    start = time.perf_counter()

    # 这里默认按 OpenAI 兼容接口去调本地/远程 LLM 服务，例如 Ollama。
    llm_url = getattr(state.opt, "llm_url", "http://127.0.0.1:11434/v1")
    llm_model = getattr(state.opt, "llm_model", "qwen3.5:0.8b")

    client = OpenAI(
        api_key="ollama",  # 本地 Ollama 只需要占位 key。
        base_url=llm_url,
    )
    end = time.perf_counter()
    logger.info(f"llm Time init: {end-start}s")

    try:
        completion = client.chat.completions.create(
            model=llm_model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": message},
            ],
            stream=True,
        )

        result = ""
        first = True
        for chunk in completion:
            if len(chunk.choices) > 0 and chunk.choices[0].delta.content:
                if first:
                    end = time.perf_counter()
                    logger.info(f"llm Time to first chunk: {end-start}s")
                    first = False

                msg = chunk.choices[0].delta.content

                # 前端展示层需要“原始 token 流”，所以这里直接按增量回推。
                if loop and output_queue:
                    asyncio.run_coroutine_threadsafe(output_queue.put(msg), loop)

                lastpos = 0
                for i, char in enumerate(msg):
                    # 按标点粗粒度切句，避免把太长一段话一次性交给 TTS，
                    # 这样可以更快开始说话，也更接近实时对话体验。
                    if char in ",.!;:，。！？：；\n":
                        result = result + msg[lastpos : i + 1]
                        lastpos = i + 1
                        if len(result) > 10:
                            logger.info(f"LLM Chunk: {result}")
                            if nerfreal:
                                nerfreal.put_msg_txt(result)
                            result = ""
                result = result + msg[lastpos:]

        end = time.perf_counter()
        logger.info(f"llm Time to last chunk: {end-start}s")
        if result.strip():
            logger.info(f"LLM Chunk: {result}")
            if nerfreal:
                nerfreal.put_msg_txt(result)

    except Exception as e:
        logger.error(f"Error calling LLM stream: {e}")
    finally:
        # 用 `None` 作为结束标记，告诉前端的流式响应可以收尾了。
        if loop and output_queue:
            asyncio.run_coroutine_threadsafe(output_queue.put(None), loop)
