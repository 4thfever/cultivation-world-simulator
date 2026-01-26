from __future__ import annotations

# 基类与工具
from .action import (
    Action,
    DefineAction,
    LLMAction,
    ChunkActionMixin,
    ActualActionMixin,
    InstantAction,
    TimedAction,
    long_action,
)
from .registry import register_action

# 具体动作（按文件拆分）
from .move import Move
from .move_to_region import MoveToRegion
from .move_to_avatar import MoveToAvatar
from .move_away_from_avatar import MoveAwayFromAvatar
from .move_away_from_region import MoveAwayFromRegion
from .escape import Escape
from .cultivate import Cultivate
from .breakthrough import Breakthrough
from .play import Play
from .hunt import Hunt
from .harvest import Harvest
from .sell import Sell
from .attack import Attack
from .plunder_mortals import PlunderMortals
from .help_mortals import HelpMortals
from .devour_mortals import DevourMortals
from .self_heal import SelfHeal
from .catch import Catch
from .nurture_weapon import NurtureWeapon
from .assassinate import Assassinate
from .move_to_direction import MoveToDirection
from .cast import Cast
from .refine import Refine
from .buy import Buy
from .mine import Mine
from .retreat import Retreat

# 注册到 ActionRegistry（标注是否为实际可执行动作）
register_action(actual=False)(Action)
register_action(actual=False)(DefineAction)
register_action(actual=False)(LLMAction)
register_action(actual=False)(ChunkActionMixin)
register_action(actual=False)(ActualActionMixin)
register_action(actual=False)(InstantAction)
register_action(actual=False)(TimedAction)

register_action(actual=False)(Move)
register_action(actual=True)(MoveToRegion)
register_action(actual=True)(MoveToAvatar)
register_action(actual=True)(MoveAwayFromAvatar)
register_action(actual=True)(MoveAwayFromRegion)
register_action(actual=False)(Escape)
register_action(actual=True)(Cultivate)
register_action(actual=True)(Breakthrough)
register_action(actual=True)(Play)
register_action(actual=True)(Hunt)
register_action(actual=True)(Harvest)
register_action(actual=True)(Sell)
register_action(actual=False)(Attack)
register_action(actual=True)(PlunderMortals)
register_action(actual=True)(HelpMortals)
register_action(actual=True)(DevourMortals)
register_action(actual=True)(SelfHeal)
register_action(actual=True)(Catch)
register_action(actual=True)(NurtureWeapon)
register_action(actual=True)(Assassinate)
register_action(actual=True)(MoveToDirection)
register_action(actual=True)(Cast)
register_action(actual=True)(Refine)
register_action(actual=True)(Buy)
register_action(actual=True)(Mine)
register_action(actual=True)(Retreat)
# Talk 已移动到 mutual_action 模块，在那里注册

__all__ = [
    # 基类
    "Action",
    "DefineAction",
    "LLMAction",
    "ChunkActionMixin",
    "ActualActionMixin",
    "InstantAction",
    "TimedAction",
    "long_action",
    # 派生类
    "Move",
    "MoveToRegion",
    "MoveToAvatar",
    "MoveAwayFromAvatar",
    "MoveAwayFromRegion",
    "Escape",
    "Cultivate",
    "Breakthrough",
    "Play",
    "Hunt",
    "Harvest",
    "Sell",
    "Attack",
    "PlunderMortals",
    "HelpMortals",
    "DevourMortals",
    "SelfHeal",
    "Catch",
    "NurtureWeapon",
    "Assassinate",
    "MoveToDirection",
    "Cast",
    "Refine",
    "Buy",
    "Mine",
    "Retreat",
]


