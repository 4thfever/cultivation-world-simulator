from litellm import completion
from langchain.prompts import PromptTemplate
from pathlib import Path
import asyncio
import re
import json5

from src.utils.config import CONFIG
from src.utils.io import read_txt
from src.run.log import log_llm_call

def get_prompt(template: str, infos: dict) -> str:
    """
    根据模板，获取提示词
    """
    prompt_template = PromptTemplate(template=template)
    return prompt_template.format(**infos)


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

def parse_llm_response(res: str) -> dict:
    """
    解析LLM返回的结果，支持多种格式
    """
    res = res.strip()
    
    # 提取markdown代码块中的JSON
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', res, re.DOTALL)
    if json_match:
        res = json_match.group(1)
    
    return json5.loads(res)

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