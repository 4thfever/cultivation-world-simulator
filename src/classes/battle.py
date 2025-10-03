from __future__ import annotations

import random
from typing import Tuple, TYPE_CHECKING

from src.classes.cultivation import Realm

if TYPE_CHECKING:
    from src.classes.avatar import Avatar


def _realm_order(realm: Realm) -> int:
    """
    将境界映射为数值顺序，用于胜率计算。
    """
    order_map = {
        Realm.Qi_Refinement: 1,
        Realm.Foundation_Establishment: 2,
        Realm.Core_Formation: 3,
        Realm.Nascent_Soul: 4,
    }
    return order_map.get(realm, 1)


def calc_win_rate(attacker: "Avatar", defender: "Avatar") -> float:
    """
    根据双方境界粗略计算进攻方胜率。
    基准50%，每高一个大境界+15%，限制在[0.1, 0.9]。
    """
    atk_order = _realm_order(attacker.cultivation_progress.realm)
    def_order = _realm_order(defender.cultivation_progress.realm)
    delta = atk_order - def_order
    base = 0.5 + 0.15 * delta
    return max(0.1, min(0.9, base))


def decide_battle(attacker: "Avatar", defender: "Avatar") -> Tuple["Avatar", "Avatar", int]:
    """
    结算一场战斗，返回(胜者, 败者, 伤害值)。
    伤害值根据胜负双方境界差距给出，范围约 [30, 80]。
    """
    p = calc_win_rate(attacker, defender)
    if random.random() < p:
        winner, loser = attacker, defender
    else:
        winner, loser = defender, attacker

    damage = get_damage(winner, loser)
    return winner, loser, damage

def get_escape_success_rate(attacker: "Avatar", defender: "Avatar") -> float:
    """
    逃跑成功率：临时返回常量值，后续可基于双方能力细化。
    attacker: 追击方（通常为进攻者）
    defender: 逃跑方（通常为被攻击者）
    """
    return 0.1

def get_damage(winner: "Avatar", loser: "Avatar") -> int:
    """
    根据胜负双方境界差距估算伤害：基础100，差一大境界+100，上限500。
    """
    gap = max(0, _realm_order(winner.cultivation_progress.realm) - _realm_order(loser.cultivation_progress.realm))
    # return min(500, 100 + 100 * gap)
    return 500