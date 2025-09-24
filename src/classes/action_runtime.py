from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any


# 运行时动作状态（字符串，便于与现有实现对接）
ActionStatus = str  # "running" | "completed" | "failed" | "blocked"


@dataclass
class ActionPlan:
    """
    计划中的动作项：尚未提交执行。
    仅包含 class 名与参数，外加可选的调度策略字段。
    """
    action_name: str
    params: Dict[str, Any]
    priority: int = 0
    expiry_month: Optional[int] = None  # 到期月戳；None 为不过期
    max_retries: int = 0
    attempted: int = 0


@dataclass
class ActionInstance:
    """
    已提交并开始执行的动作实例。
    """
    action: Any  # src.classes.action.Action
    params: Dict[str, Any]
    status: ActionStatus = "running"

