"""LLM 客户端核心调用逻辑"""

import json
import urllib.request
import urllib.error
import asyncio
from pathlib import Path
from typing import Optional

from src.run.log import log_llm_call
from src.utils.config import CONFIG
from .config import LLMMode, LLMConfig, get_task_mode
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
    """使用原生 urllib 调用 (OpenAI 兼容接口)"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.api_key}"
    }
    
    # 兼容 litellm 的 openai/ 前缀处理，以及其他常见前缀清理
    model_name = config.model_name
    for prefix in ["openai/", "azure/", "bedrock/"]:
        if model_name.startswith(prefix):
            model_name = model_name[len(prefix):]
            break
    
    data = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    url = config.base_url
    if not url:
        raise ValueError("Base URL is required for requests mode (OpenAI Compatible)")
        
    # URL 规范化处理：确保指向 chat/completions
    if "chat/completions" not in url:
        url = url.rstrip("/")
        url = f"{url}/chat/completions"

    req = urllib.request.Request(
        url, 
        data=json.dumps(data).encode('utf-8'), 
        headers=headers,
        method="POST"
    )
    
    try:
        # 设置超时时间为 60 秒，避免无限等待
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result['choices'][0]['message']['content']
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        raise Exception(f"LLM Request failed {e.code}: {error_body}")
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
            # 降级到 requests (在线程池中运行)，实现 OpenAI 兼容接口
            # 这样即使没有 litellm，只要模型服务提供商支持 OpenAI 格式（如 Qwen, DeepSeek, LocalAI 等）均可工作
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


async def call_llm_with_task_name(
    task_name: str,
    template_path: Path | str,
    infos: dict,
    max_retries: int | None = None
) -> dict:
    """
    根据任务名称自动选择 LLM 模式并调用
    
    Args:
        task_name: 任务名称，用于在 config.yml 中查找对应的模式
        template_path: 模板路径
        infos: 模板参数
        max_retries: 最大重试次数
        
    Returns:
        dict: LLM 返回的 JSON 数据
    """
    mode = get_task_mode(task_name)
    
    # 全局强制模式检查
    # 如果 llm.mode 被设置为 normal 或 fast，则强制覆盖
    global_mode = getattr(CONFIG.llm, "mode", "default")
    if global_mode in ["normal", "fast"]:
        mode = LLMMode(global_mode)
            
    return await call_llm_with_template(template_path, infos, mode, max_retries)


def test_connectivity(mode: LLMMode = LLMMode.NORMAL) -> bool:
    """
    测试 LLM 服务连通性 (同步版本)
    
    Args:
        mode: 测试使用的模式 (NORMAL/FAST)
        
    Returns:
        bool: 连接成功返回 True，失败返回 False
    """
    try:
        config = LLMConfig.from_mode(mode)
        if HAS_LITELLM:
            # 使用 litellm 同步接口
            litellm.completion(
                model=config.model_name,
                messages=[{"role": "user", "content": "你好"}],
                api_key=config.api_key,
                base_url=config.base_url,
            )
        else:
            # 直接调用 requests 实现
            _call_with_requests(config, "test")
        return True
    except Exception:
        return False