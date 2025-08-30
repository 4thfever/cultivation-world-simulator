#!/usr/bin/env python3
"""
测试call_llm函数
"""

from src.utils.llm import call_llm

def main():
    """测试call_llm函数"""
    print("正在测试call_llm函数...")
    
    # 简单的测试提示词
    prompt = "你好，请简单回复一句话证明你能正常工作。"
    
    print(f"输入提示词: {prompt}")
    
    # 调用LLM
    response = call_llm(prompt)
    
    print(f"LLM响应: {response}")
    print("测试完成！")

if __name__ == "__main__":
    main()
