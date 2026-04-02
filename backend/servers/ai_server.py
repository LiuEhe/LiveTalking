import time
from basereal import BaseReal
from logger import logger
from servers import state

def llm_chat_stream(message: str, nerfreal: BaseReal):
    start = time.perf_counter()
    from openai import OpenAI
    
    # Use settings from state.opt to configure ollama
    llm_url = getattr(state.opt, "llm_url", "http://127.0.0.1:11434/v1")
    llm_model = getattr(state.opt, "llm_model", "qwen3.5:0.8b")
    
    client = OpenAI(
        api_key="ollama", # dummy key for local ollama
        base_url=llm_url,
    )
    end = time.perf_counter()
    logger.info(f"llm Time init: {end-start}s")
    
    try:
        completion = client.chat.completions.create(
            model=llm_model,
            messages=[{'role': 'system', 'content': 'You are a helpful assistant.'},
                      {'role': 'user', 'content': message}],
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
                lastpos = 0
                for i, char in enumerate(msg):
                    if char in ",.!;:，。！？：；\n":
                        result = result + msg[lastpos:i+1]
                        lastpos = i + 1
                        if len(result) > 10:
                            logger.info(result)
                            nerfreal.put_msg_txt(result)
                            result = ""
                result = result + msg[lastpos:]
                
        end = time.perf_counter()
        logger.info(f"llm Time to last chunk: {end-start}s")
        if result.strip():
            logger.info(result)
            nerfreal.put_msg_txt(result)
            
    except Exception as e:
        logger.error(f"Error calling LLM stream: {e}")
