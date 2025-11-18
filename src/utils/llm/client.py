"""LLM 客户端核心调用逻辑"""

from pathlib import Path
from litellm import completion

from .config import LLMMode, LLMConfig
from .parser import parse_json
from .prompt import build_prompt, load_template
from .exceptions import LLMError, ParseError
from src.run.log import log_llm_call


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
    
    # 调用 litellm（包装为异步）
    def _call():
        response = completion(
            model=config.model_name,
            messages=[{"role": "user", "content": prompt}],
            api_key=config.api_key,
            base_url=config.base_url,
        )
        return response.choices[0].message.content
    
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

