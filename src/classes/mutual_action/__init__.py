from __future__ import annotations

from .mutual_action import MutualAction
from .drive_away import DriveAway
from .attack import MutualAttack
from .conversation import Conversation
from .dual_cultivation import DualCultivation
from .talk import Talk
from .impart import Impart
from .gift import Gift
from .spar import Spar
from .occupy import Occupy
from .play import TeaParty, Chess
from .confess import Confess
from .swear_brotherhood import SwearBrotherhood
from src.classes.action.registry import register_action

__all__ = [
    "MutualAction",
    "DriveAway",
    "MutualAttack",
    "Conversation",
    "DualCultivation",
    "Talk",
    "Impart",
    "Gift",
    "Spar",
    "Occupy",
    "TeaParty",
    "Chess",
    "Confess",
    "SwearBrotherhood",
]

# 注册 mutual actions（均为实际动作）
register_action(actual=True)(DriveAway)
register_action(actual=True)(MutualAttack)
register_action(actual=True)(Conversation)
register_action(actual=True)(DualCultivation)
register_action(actual=True)(Talk)
register_action(actual=True)(Impart)
register_action(actual=True)(Gift)
register_action(actual=True)(Spar)
register_action(actual=True)(Occupy)
register_action(actual=True)(TeaParty)
register_action(actual=True)(Chess)
register_action(actual=True)(Confess)
register_action(actual=True)(SwearBrotherhood)
