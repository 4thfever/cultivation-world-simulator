"""LLM 配置管理"""

from enum import Enum
from dataclasses import dataclass
from src.utils.config import CONFIG

class LLMMode(str, Enum):
    """LLM 调用模式"""
    NORMAL = "normal"
    FAST = "fast"
    DEFAULT = "default"


@dataclass(frozen=True)
class LLMConfig:
    """LLM 配置数据类"""
    model_name: str
    api_key: str
    base_url: str
    
    @classmethod
    def from_mode(cls, mode: LLMMode) -> 'LLMConfig':
        """
        根据模式创建配置，从 CONFIG 读取
        
        Args:
            mode: LLM 调用模式
            
        Returns:
            LLMConfig: 配置对象
        """
        # 从 CONFIG 读取配置
        api_key = getattr(CONFIG.llm, "key", "")
        base_url = getattr(CONFIG.llm, "base_url", "")
        
        # 根据模式选择模型
        model_name = ""
        if mode == LLMMode.FAST:
            model_name = getattr(CONFIG.llm, "fast_model_name", "")
        else:
            # NORMAL or DEFAULT fallback
            model_name = getattr(CONFIG.llm, "model_name", "")
        
        return cls(
            model_name=model_name,
            api_key=api_key,
            base_url=base_url
        )


def get_task_mode(task_name: str) -> LLMMode:
    """
    根据任务名称获取 LLM 模式
    """
    # 从 CONFIG 读取全局模式
    global_mode = getattr(CONFIG.llm, "mode", "default").lower()
    
    if global_mode == "normal":
        return LLMMode.NORMAL
    elif global_mode == "fast":
        return LLMMode.FAST
    
    # Default 模式：根据 task_name 从细粒度配置中获取
    # 如果配置了 default_modes，则根据任务名称返回对应模式
    default_modes = getattr(CONFIG.llm, "default_modes", {})
    if default_modes and task_name in default_modes:
        task_mode = default_modes[task_name].lower()
        if task_mode == "fast":
            return LLMMode.FAST
        else:
            return LLMMode.NORMAL
    
    # 如果没有配置，默认返回 NORMAL
    return LLMMode.NORMAL
