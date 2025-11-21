"""LLM 客户端核心调用逻辑"""

from pathlib import Path
import json
import urllib.request
import urllib.error

from .config import LLMMode, LLMConfig
from .parser import parse_json
from .prompt import build_prompt, load_template
from .exceptions import LLMError, ParseError
from src.run.log import log_llm_call

try:
    # 使用动态导入，避免 PyInstaller 静态分析将其作为依赖打包
    import importlib
    importlib.import_module("litellm")
    has_litellm = True
except ImportError:
    has_litellm = False 

def _call_with_litellm(config: LLMConfig, prompt: str) -> str:
    """使用 litellm 调用"""
    import importlib
    litellm = importlib.import_module("litellm")
    response = litellm.completion(
        model=config.model_name,
        messages=[{"role": "user", "content": prompt}],
        api_key=config.api_key,
        base_url=config.base_url,
    )
    return response.choices[0].message.content


def _call_with_requests(config: LLMConfig, prompt: str) -> str:
    """使用原生 requests 调用 (OpenAI 兼容接口)"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.api_key}"
    }
    data = {
        "model": config.model_name,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    # 处理 URL
    url = config.base_url
    if not url:
        raise ValueError("Base URL is required for requests mode")
        
    if "chat/completions" not in url:
        url = url.rstrip("/")
        if not url.endswith("/v1"):
            # 尝试智能追加 v1，如果用户没写
            # 但有些服务可能不需要 v1，这里保守起见，如果没 v1 且没 chat/completions，直接加 /chat/completions
            # 假设用户配置的是类似 https://api.openai.com/v1
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
        error_content = e.read().decode('utf-8')
        raise Exception(f"LLM Request failed {e.code}: {error_content}")
    except Exception as e:
        raise Exception(f"LLM Request failed: {str(e)}")


async def call_llm(prompt: str, mode: LLMMode = LLMMode.NORMAL) -> str:
    """
    最基础的 LLM 调用，返回原始文本
    
    Args:
        prompt: 输入提示词
        mode: 调用模式
        
    Returns:
        str: LLM 返回的原始文本
    """
    import asyncio
    
    # 获取配置
    config = LLMConfig.from_mode(mode)
    
    # 调用逻辑
    def _call():
        # try:
        #     return _call_with_litellm(config, prompt)
        # except ImportError:
        #     # 如果没有 litellm，降级使用 requests
        #     return _call_with_requests(config, prompt)
        try:
            if has_litellm:
                return _call_with_litellm(config, prompt)
            else:
                return _call_with_requests(config, prompt)
        except Exception as e:
            # litellm 可能抛出其他错误，如果仅仅是导入错误我们降级
            # 如果是 litellm 内部错误（如 api key 错误），应该抛出
            # 但为了稳健，如果 litellm 失败，是否尝试 request? 
            # 用户只说了 "没有的话(if no litellm)"，通常指安装。
            # 所以 catch ImportError 是对的。
            raise e
    
    result = await asyncio.to_thread(_call)
    
    # 记录日志
    log_llm_call(config.model_name, prompt, result)
    
    return result


async def call_llm_json(
    prompt: str,
    mode: LLMMode = LLMMode.NORMAL,
    max_retries: int | None = None
) -> dict:
    """
    调用 LLM 并解析为 JSON，内置重试机制
    
    Args:
        prompt: 输入提示词
        mode: 调用模式
        max_retries: 最大重试次数，None 则从配置读取
        
    Returns:
        dict: 解析后的 JSON 对象
        
    Raises:
        LLMError: 解析失败且重试次数用尽时抛出
    """
    if max_retries is None:
        from src.utils.config import CONFIG
        max_retries = int(getattr(CONFIG.ai, "max_parse_retries", 0))
    
    last_error = None
    for attempt in range(max_retries + 1):
        response = await call_llm(prompt, mode)
        try:
            return parse_json(response)
        except ParseError as e:
            last_error = e
            if attempt < max_retries:
                continue  # 继续重试
            # 最后一次失败，抛出详细错误
            raise LLMError(
                f"解析失败（重试 {max_retries} 次后）",
                cause=last_error
            ) from last_error
    
    # 不应该到这里，但为了类型检查
    raise LLMError("未知错误")


async def call_llm_with_template(
    template_path: Path | str,
    infos: dict,
    mode: LLMMode = LLMMode.NORMAL,
    max_retries: int | None = None
) -> dict:
    """
    使用模板调用 LLM（最常用的高级接口）
    
    Args:
        template_path: 模板文件路径
        infos: 要填充的信息字典
        mode: 调用模式
        max_retries: 最大重试次数，None 则从配置读取
        
    Returns:
        dict: 解析后的 JSON 对象
    """
    template = load_template(template_path)
    prompt = build_prompt(template, infos)
    return await call_llm_json(prompt, mode, max_retries)


async def call_ai_action(
    infos: dict,
    mode: LLMMode = LLMMode.NORMAL
) -> dict:
    """
    AI 行动决策专用接口
    
    Args:
        infos: 行动决策所需信息
        mode: 调用模式
        
    Returns:
        dict: AI 行动决策结果
    """
    from src.utils.config import CONFIG
    template_path = CONFIG.paths.templates / "ai.txt"
    return await call_llm_with_template(template_path, infos, mode)
