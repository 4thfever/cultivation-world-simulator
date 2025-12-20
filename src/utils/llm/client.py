"""LLM 客户端核心调用逻辑"""

import json
import urllib.request
import urllib.error
import asyncio
from pathlib import Path
from typing import Optional

from src.run.log import log_llm_call
from src.utils.config import CONFIG
from .config import LLMMode, LLMConfig
from .parser import parse_json
from .prompt import build_prompt, load_template
from .exceptions import LLMError, ParseError

try:
    import litellm
    HAS_LITELLM = True
except ImportError:
    HAS_LITELLM = False

# 模块级信号量，懒加载
_SEMAPHORE: Optional[asyncio.Semaphore] = None


def _get_semaphore() -> asyncio.Semaphore:
    global _SEMAPHORE
    if _SEMAPHORE is None:
        limit = getattr(CONFIG.ai, "max_concurrent_requests", 10)
        _SEMAPHORE = asyncio.Semaphore(limit)
    return _SEMAPHORE


def _call_with_requests(config: LLMConfig, prompt: str) -> str:
    """使用原生 requests 调用 (OpenAI 兼容接口)"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.api_key}"
    }
    
    # 兼容 litellm 的 openai/ 前缀处理
    model_name = config.model_name.replace("openai/", "")
    
    data = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    url = config.base_url
    if not url:
        raise ValueError("Base URL is required for requests mode")
        
    if "chat/completions" not in url:
        url = url.rstrip("/")
        if not url.endswith("/v1"):
            # 简单启发式：如果不是显式 v1 结尾，也加上
             pass
        url = f"{url}/chat/completions"

    req = urllib.request.Request(
        url, 
        data=json.dumps(data).encode('utf-8'), 
        headers=headers,
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result['choices'][0]['message']['content']
    except urllib.error.HTTPError as e:
        raise Exception(f"LLM Request failed {e.code}: {e.read().decode('utf-8')}")
    except Exception as e:
        raise Exception(f"LLM Request failed: {str(e)}")


async def call_llm(prompt: str, mode: LLMMode = LLMMode.NORMAL) -> str:
    """
    基础 LLM 调用，自动控制并发
    """
    config = LLMConfig.from_mode(mode)
    semaphore = _get_semaphore()
    
    async with semaphore:
        if HAS_LITELLM:
            try:
                # 使用 litellm 原生异步接口
                response = await litellm.acompletion(
                    model=config.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    api_key=config.api_key,
                    base_url=config.base_url,
                )
                result = response.choices[0].message.content
            except Exception as e:
                # 再次抛出以便上层处理，或者记录日志
                raise Exception(f"LiteLLM call failed: {str(e)}") from e
        else:
            # 降级到 requests (在线程池中运行)
            result = await asyncio.to_thread(_call_with_requests, config, prompt)
    
    log_llm_call(config.model_name, prompt, result)
    return result


async def call_llm_json(
    prompt: str,
    mode: LLMMode = LLMMode.NORMAL,
    max_retries: int | None = None
) -> dict:
    """调用 LLM 并解析为 JSON，带重试"""
    if max_retries is None:
        max_retries = int(getattr(CONFIG.ai, "max_parse_retries", 0))
    
    last_error = None
    for attempt in range(max_retries + 1):
        response = await call_llm(prompt, mode)
        try:
            return parse_json(response)
        except ParseError as e:
            last_error = e
            if attempt < max_retries:
                continue
            raise LLMError(f"解析失败（重试 {max_retries} 次后）", cause=last_error) from last_error
            
    raise LLMError("未知错误")


async def call_llm_with_template(
    template_path: Path | str,
    infos: dict,
    mode: LLMMode = LLMMode.NORMAL,
    max_retries: int | None = None
) -> dict:
    """使用模板调用 LLM"""
    template = load_template(template_path)
    prompt = build_prompt(template, infos)
    return await call_llm_json(prompt, mode, max_retries)


async def call_ai_action(infos: dict, mode: LLMMode = LLMMode.NORMAL) -> dict:
    """AI 行动决策专用接口"""
    template_path = CONFIG.paths.templates / "ai.txt"
    return await call_llm_with_template(template_path, infos, mode)
