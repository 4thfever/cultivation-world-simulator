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


def decide_battle(attacker: "Avatar", defender: "Avatar") -> Tuple["Avatar", "Avatar", float]:
    """
    结算一场战斗，返回(胜者, 败者, 进攻方胜率)。
    仅做结果判定，不做数值伤害结算。
    """
    p = calc_win_rate(attacker, defender)
    if random.random() < p:
        return attacker, defender, p
    else:
        return defender, attacker, p

