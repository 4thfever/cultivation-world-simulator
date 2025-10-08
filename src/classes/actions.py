from __future__ import annotations

import json

from src.classes.action.registry import ActionRegistry
# 确保在收集注册表前加载所有动作模块（含 mutual actions）
import src.classes.action  # noqa: F401
import src.classes.mutual_action  # noqa: F401


ALL_ACTION_CLASSES = list(ActionRegistry.all())
ALL_ACTUAL_ACTION_CLASSES = list(ActionRegistry.all_actual())
ALL_ACTION_NAMES = [cls.__name__ for cls in ALL_ACTION_CLASSES]
ALL_ACTUAL_ACTION_NAMES = [cls.__name__ for cls in ALL_ACTUAL_ACTION_CLASSES]

ACTION_INFOS = {
    action.__name__: {
        "comment": getattr(action, "COMMENT", ""),
        "doable_requirements": getattr(action, "DOABLES_REQUIREMENTS", ""),
        "params": getattr(action, "PARAMS", {}),
    }
    for action in ALL_ACTUAL_ACTION_CLASSES
}
ACTION_INFOS_STR = json.dumps(ACTION_INFOS, ensure_ascii=False)


