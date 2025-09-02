from litellm import completion
from langchain.prompts import PromptTemplate
from pathlib import Path
import json
import asyncio

from src.utils.config import CONFIG
from src.utils.io import read_txt

def get_prompt(template: str, infos: dict) -> str:
    """
    根据模板，获取提示词
    """
    prompt_template = PromptTemplate(template=template)
    return prompt_template.format(**infos)


def call_llm(prompt: str) -> str:
    """
    调用LLM
    
    Args:
        prompt: 输入的提示词
    Returns:
        str: LLM返回的结果
    """
    # 从配置中获取模型信息
    model_name = CONFIG.llm.model_name
    api_key = CONFIG.llm.key
    # 调用litellm的completion函数
    response = completion(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        api_key=api_key,
    )
    
    # 返回生成的内容
    return response.choices[0].message.content

async def call_llm_async(prompt: str) -> str:
    """
    异步调用LLM
    
    Args:
        prompt: 输入的提示词
    Returns:
        str: LLM返回的结果
    """
    # 使用asyncio.to_thread包装同步调用
    return await asyncio.to_thread(call_llm, prompt)

def get_prompt_and_call_llm(template_path: Path, infos: dict) -> str:
    """
    根据模板，获取提示词，并调用LLM
    """
    template = read_txt(template_path)
    prompt = get_prompt(template, infos)
    res = call_llm(prompt)
    json_res = json.loads(res)
    # print(f"prompt = {prompt}")
    # print(f"res = {res}")
    return json_res

async def get_prompt_and_call_llm_async(template_path: Path, infos: dict) -> str:
    """
    异步版本：根据模板，获取提示词，并调用LLM
    """
    template = read_txt(template_path)
    prompt = get_prompt(template, infos)
    res = await call_llm_async(prompt)
    json_res = json.loads(res)
    print(f"prompt = {prompt}")
    print(f"res = {res}")
    return json_res

def get_ai_prompt_and_call_llm(infos: dict) -> dict:
    """
    根据模板，获取提示词，并调用LLM
    """
    template_path = CONFIG.paths.templates / "ai.txt"
    return get_prompt_and_call_llm(template_path, infos)

async def get_ai_prompt_and_call_llm_async(infos: dict) -> dict:
    """
    异步版本：根据模板，获取提示词，并调用LLM
    """
    template_path = CONFIG.paths.templates / "ai.txt"
    return await get_prompt_and_call_llm_async(template_path, infos)