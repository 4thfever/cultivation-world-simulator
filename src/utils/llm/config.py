"""LLM 配置管理"""

from enum import Enum
from dataclasses import dataclass
import os


class LLMMode(str, Enum):
    """LLM 调用模式"""
    NORMAL = "normal"
    FAST = "fast"


@dataclass(frozen=True)
class LLMConfig:
    """LLM 配置数据类"""
    model_name: str
    api_key: str
    base_url: str
    
    @classmethod
    def from_mode(cls, mode: LLMMode) -> 'LLMConfig':
        """
        根据模式创建配置
        
        Args:
            mode: LLM 调用模式
            
        Returns:
            LLMConfig: 配置对象
        """
        from src.utils.config import CONFIG
        
        # 根据模式选择模型
        model_name = (
            CONFIG.llm.model_name if mode == LLMMode.NORMAL
            else CONFIG.llm.fast_model_name
        )
        
        # API Key 优先从环境变量读取
        api_key = os.getenv("QWEN_API_KEY") or CONFIG.llm.key
        
        return cls(
            model_name=model_name,
            api_key=api_key,
            base_url=CONFIG.llm.base_url
        )


def get_task_mode(task_name: str) -> LLMMode:
    """
    获取指定任务的 LLM 调用模式
    
    Args:
        task_name: 任务名称 (配置在 llm.default_modes 下的 key)
        
    Returns:
        LLMMode: 对应的模式，如果未配置则默认返回 NORMAL
    """
    from src.utils.config import CONFIG
    
    # 获取配置的模式字符串，默认 normal
    mode_str = getattr(CONFIG.llm.default_modes, task_name, "normal")
    return LLMMode(mode_str)
