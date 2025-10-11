from litellm import completion
from langchain.prompts import PromptTemplate
from pathlib import Path
import asyncio
import re
import json5

from src.utils.config import CONFIG
from src.utils.io import read_txt
from src.run.log import log_llm_call
from src.utils.strings import intentify_prompt_infos

def get_prompt(template: str, infos: dict) -> str:
    """
    根据模板，获取提示词
    """
    prompt_template = PromptTemplate(template=template)
    # 将 dict/list 等结构化对象转为 JSON 字符串
    # 策略：
    # - avatar_infos: 不包装 intent（模板里已经说明是 dict[Name, info]）
    # - general_action_infos: 强制包装 intent 以凸显语义
    # - 其他容器类型：默认包装 intent
    processed_infos = intentify_prompt_infos(infos)
    return prompt_template.format(**processed_infos)


def call_llm(prompt: str, mode="normal") -> str:
    """
    调用LLM
    
    Args:
        prompt: 输入的提示词
    Returns:
        str: LLM返回的结果
    """
    # 从配置中获取模型信息
    if mode == "normal":
        model_name = CONFIG.llm.model_name
    elif mode == "fast":
        model_name = CONFIG.llm.fast_model_name
    else:
        raise ValueError(f"Invalid mode: {mode}")
    api_key = CONFIG.llm.key
    base_url = CONFIG.llm.base_url
    # 调用litellm的completion函数
    response = completion(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        api_key=api_key,
        base_url=base_url,
    )
    
    # 返回生成的内容
    result = response.choices[0].message.content
    log_llm_call(model_name, prompt, result)  # 记录日志
    return result

async def call_llm_async(prompt: str, mode="normal") -> str:
    """
    异步调用LLM
    
    Args:
        prompt: 输入的提示词
    Returns:
        str: LLM返回的结果
    """
    # 使用asyncio.to_thread包装同步调用
    result = await asyncio.to_thread(call_llm, prompt, mode)
    return result

def _extract_code_blocks(text: str):
    """
    提取所有markdown代码块，返回 (lang, content) 列表。
    """
    pattern = re.compile(r"```([^\n`]*)\n([\s\S]*?)```", re.DOTALL)
    blocks = []
    for lang, content in pattern.findall(text):
        blocks.append((lang.strip().lower(), content.strip()))
    return blocks


def _find_first_balanced_json_object(text: str):
    """
    在整段文本中扫描并返回首个平衡的花括号 {...} 片段（忽略字符串中的括号）。
    找到则返回子串，否则返回None。
    """
    depth = 0
    start_index = None
    in_string = False
    string_char = ''
    escape = False
    for idx, ch in enumerate(text):
        if in_string:
            if escape:
                escape = False
                continue
            if ch == '\\':
                escape = True
                continue
            if ch == string_char:
                in_string = False
            continue
        if ch in ('"', "'"):
            in_string = True
            string_char = ch
            continue
        if ch == '{':
            if depth == 0:
                start_index = idx
            depth += 1
            continue
        if ch == '}':
            if depth > 0:
                depth -= 1
                if depth == 0 and start_index is not None:
                    return text[start_index:idx + 1]
    return None


def parse_llm_response(res: str) -> dict:
    """
    仅针对 JSON 的稳健解析：
    1) 优先解析 ```json/json5``` 或未标注语言的代码块
    2) 自由文本中定位首个平衡的 {...}
    3) 整体 json5 兜底
    最终返回字典；否则抛错。
    """
    res = (res or '').strip()
    if not res:
        return {}

    # 1) 优先解析代码块（仅 json/json5/未标注语言）
    for lang, block in _extract_code_blocks(res):
        if lang and lang not in ("json", "json5"):
            continue
        # 先在块内找平衡对象
        span = _find_first_balanced_json_object(block)
        candidates = [span] if span else [block]
        for cand in candidates:
            if not cand:
                continue
            try:
                obj = json5.loads(cand)
                if isinstance(obj, dict):
                    return obj
            except Exception:
                continue

    # 2) 扫描全文首个平衡的JSON对象
    json_span = _find_first_balanced_json_object(res)
    if json_span:
        try:
            obj = json5.loads(json_span)
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass

    # 3) 整体 json5 兜底
    obj = json5.loads(res)
    return obj


def get_prompt_and_call_llm(template_path: Path, infos: dict, mode="normal") -> str:
    """
    根据模板，获取提示词，并调用LLM
    """
    template = read_txt(template_path)
    prompt = get_prompt(template, infos)
    res = call_llm(prompt, mode)
    json_res = parse_llm_response(res)
    return json_res

async def get_prompt_and_call_llm_async(template_path: Path, infos: dict, mode="normal") -> str:
    """
    异步版本：根据模板，获取提示词，并调用LLM
    """
    template = read_txt(template_path)
    prompt = get_prompt(template, infos)
    res = await call_llm_async(prompt, mode)
    json_res = parse_llm_response(res)
    return json_res

def get_ai_prompt_and_call_llm(infos: dict, mode="normal") -> dict:
    """
    根据模板，获取提示词，并调用LLM
    """
    template_path = CONFIG.paths.templates / "ai.txt"
    return get_prompt_and_call_llm(template_path, infos, mode)

async def get_ai_prompt_and_call_llm_async(infos: dict, mode="normal") -> dict:
    """
    异步版本：根据模板，获取提示词，并调用LLM
    """
    template_path = CONFIG.paths.templates / "ai.txt"
    return await get_prompt_and_call_llm_async(template_path, infos, mode)