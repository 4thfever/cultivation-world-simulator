"""
Avatar 模块

将原 avatar.py 拆分为多个子模块，通过此 __init__.py 导出以保持向后兼容。
"""
from src.classes.core.avatar.core import (
    Avatar,
)
from src.classes.gender import Gender

from src.classes.core.avatar.info_presenter import (
    get_avatar_info,
    get_avatar_structured_info,
    get_avatar_expanded_info,
    get_other_avatar_info,
)

__all__ = [
    # 核心类
    "Avatar",
    "Gender",
    # 信息展示函数
    "get_avatar_info",
    "get_avatar_structured_info",
    "get_avatar_hover_info",
    "get_avatar_expanded_info",
    "get_other_avatar_info",
]

