from __future__ import annotations

import json
from typing import Dict, Any

from src.classes.action.registry import ActionRegistry
# 确保在收集注册表前加载所有动作模块（含 mutual actions）
import src.classes.action  # noqa: F401
import src.classes.mutual_action  # noqa: F401


ALL_ACTION_CLASSES = list(ActionRegistry.all())
ALL_ACTUAL_ACTION_CLASSES = list(ActionRegistry.all_actual())
ALL_ACTION_NAMES = [cls.__name__ for cls in ALL_ACTION_CLASSES]
ALL_ACTUAL_ACTION_NAMES = [cls.__name__ for cls in ALL_ACTUAL_ACTION_CLASSES]

def _build_action_info(action):
    info = {
        "desc": action.get_desc(),
        "require": action.get_requirements(),
    }
    if hasattr(action, 'PARAMS') and action.PARAMS:
        info["params"] = action.PARAMS

    cd = int(getattr(action, "ACTION_CD_MONTHS", 0) or 0)
    if cd > 0:
        info["cd_months"] = cd
    return info

def get_action_infos() -> Dict[str, Any]:
    """
    动态获取当前语言环境下的动作描述信息
    """
    return {
        action.__name__: _build_action_info(action)
        for action in ALL_ACTUAL_ACTION_CLASSES
    }

def get_action_infos_str() -> str:
    """
    获取JSON格式的动作描述字符串
    """
    return json.dumps(get_action_infos(), ensure_ascii=False, indent=2)

# 为了兼容性保留 ACTION_INFOS_STR，但请注意这可能是旧的（导入时的快照），不会随语言切换更新
# 建议使用 get_action_infos_str() 获取最新语言的描述
ACTION_INFOS = get_action_infos()
ACTION_INFOS_STR = json.dumps(ACTION_INFOS, ensure_ascii=False, indent=2)
