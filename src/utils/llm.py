from litellm import completion
from langchain.prompts import PromptTemplate

from src.utils.config import CONFIG

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