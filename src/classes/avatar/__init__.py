"""
Avatar 模块

将原 avatar.py 拆分为多个子模块，通过此 __init__.py 导出以保持向后兼容。
"""
from src.classes.avatar.core import (
    Avatar,
    Gender,
    gender_strs,
    MAX_HISTORY_EVENTS,
)

from src.classes.avatar.info_presenter import (
    get_avatar_info,
    get_avatar_structured_info,
    get_avatar_hover_info,
    get_avatar_expanded_info,
    get_other_avatar_info,
)

__all__ = [
    # 核心类
    "Avatar",
    "Gender",
    "gender_strs",
    "MAX_HISTORY_EVENTS",
    # 信息展示函数
    "get_avatar_info",
    "get_avatar_structured_info",
    "get_avatar_hover_info",
    "get_avatar_expanded_info",
    "get_other_avatar_info",
]

