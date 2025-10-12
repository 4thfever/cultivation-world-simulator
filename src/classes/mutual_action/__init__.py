from __future__ import annotations

from .mutual_action import MutualAction
from .drive_away import DriveAway
from .attack import Attack
from .conversation import Conversation
from .dual_cultivation import DualCultivation
from src.classes.action.registry import register_action

__all__ = [
    "MutualAction",
    "DriveAway",
    "Attack",
    "Conversation",
    "DualCultivation",
]

# 注册 mutual actions（均为实际动作）
register_action(actual=True)(DriveAway)
register_action(actual=True)(Attack)
register_action(actual=True)(Conversation)
register_action(actual=True)(DualCultivation)


