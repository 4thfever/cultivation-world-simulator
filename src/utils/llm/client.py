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
        "Authorization": f"Bearer {config.api_key}",
        "User-Agent": "CultivationWorldSimulator/1.0"
    }
    model_name = config.model_name
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
        # 设置超时时间为 120 秒，避免无限等待
        with urllib.request.urlopen(req, timeout=120) as response:
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
    使用 urllib 直接调用 OpenAI 兼容接口
    """
    config = LLMConfig.from_mode(mode)
    semaphore = _get_semaphore()
    
    async with semaphore:
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
    
    last_error: ParseError | None = None
    for attempt in range(max_retries + 1):
        response = await call_llm(prompt, mode)
        try:
            return parse_json(response)
        except ParseError as e:
            last_error = e
            if attempt < max_retries:
                continue
            raise LLMError(f"解析失败（重试 {max_retries} 次后）", cause=last_error) from last_error
    
    # This should never be reached, but satisfies type checker.
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


def test_connectivity(mode: LLMMode = LLMMode.NORMAL, config: Optional[LLMConfig] = None) -> tuple[bool, str]:
    """
    测试 LLM 服务连通性 (同步版本)
    
    Args:
        mode: 测试使用的模式 (NORMAL/FAST)，如果传入 config 则忽略此参数
        config: 直接使用该配置进行测试
        
    Returns:
        tuple[bool, str]: (是否成功, 错误信息)，成功时错误信息为空字符串
    """
    try:
        if config is None:
            config = LLMConfig.from_mode(mode)
            
        _call_with_requests(config, "test")
        return True, ""
    except Exception as e:
        error_msg = str(e)
        print(f"Connectivity test failed: {error_msg}")
        
        # 解析常见错误并提供友好提示
        if "401" in error_msg or "invalid_api_key" in error_msg or "Incorrect API key" in error_msg:
            return False, "API Key 无效，请检查您的密钥是否正确"
        elif "403" in error_msg or "Forbidden" in error_msg:
            return False, "访问被拒绝，请检查您的权限或配额"
        elif "404" in error_msg:
            return False, "服务地址不存在，请检查 Base URL 是否正确"
        elif "timeout" in error_msg.lower():
            return False, "连接超时，请检查网络连接或服务地址"
        elif "Connection" in error_msg or "connect" in error_msg.lower():
            return False, "无法连接到服务器，请检查 Base URL 和网络"
        else:
            # 返回原始错误信息
            return False, error_msg
