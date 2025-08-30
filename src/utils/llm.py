from litellm import completion
from src.utils.config import CONFIG
print(CONFIG)

def call_llm(prompt: str) -> str:
    """
    调用LLM
    
    Args:
        prompt: 输入的提示词
        custom_llm_provider: 自定义的LLM提供者
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