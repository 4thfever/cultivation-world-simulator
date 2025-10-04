from __future__ import annotations

from typing import Any

from src.utils.config import CONFIG


class ActionConfig:
    """
    读取动作相关配置的轻量封装。

    用法：
        ActionConfig.get("actions.duration.play", default=6)
    支持以点号分隔的路径逐层 getattr，读取不到时返回 default。
    """
    @staticmethod
    def get(path: str, default: Any = None) -> Any:
        cur = CONFIG
        for part in path.split("."):
            cur = getattr(cur, part, None)
            if cur is None:
                return default
        return cur


