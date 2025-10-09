from __future__ import annotations

import random
from typing import Tuple, TYPE_CHECKING
import random

from src.classes.cultivation import Realm
from src.classes.technique import get_suppression_bonus, get_grade_advantage_bonus

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
    胜率计算（返回进攻方胜率 p ∈ [0.1, 0.9]）：
    - 基准：50%
    - 境界差：每高一大境界 +15%
    - 功法品阶差：按品阶差的相对加成（可正可负）
    - 属性克制：若进攻方克制防守方，再 +10%
    最后夹紧到 [0.1, 0.9]
    """
    atk_order = _realm_order(attacker.cultivation_progress.realm)
    def_order = _realm_order(defender.cultivation_progress.realm)
    delta = atk_order - def_order
    base = 0.5 + 0.15 * delta
    # 功法品阶差相对加成
    atk_grade = getattr(getattr(attacker, "technique", None), "grade", None)
    def_grade = getattr(getattr(defender, "technique", None), "grade", None)
    base += get_grade_advantage_bonus(atk_grade, def_grade)
    # 属性克制：若进攻方克制防守方，再+10%
    atk_attr = getattr(getattr(attacker, "technique", None), "attribute", None)
    def_attr = getattr(getattr(defender, "technique", None), "attribute", None)
    if atk_attr is not None and def_attr is not None:
        base += get_suppression_bonus(atk_attr, def_attr)
    return max(0.1, min(0.9, base))


def decide_battle(attacker: "Avatar", defender: "Avatar") -> Tuple["Avatar", "Avatar", int, int]:
    """
    结算一场战斗，返回(胜者, 败者, 败者掉血, 赢家掉血)。
    规则：
    - 先按 calc_win_rate 判定胜负；
    - 以 get_damage 计算基准伤害，再让败者“多掉一点血”（适度上调，例如 +15%）；
    - 赢家也会受伤，但伤害不超过败者伤害的一半（随机 15%~40% 区间）。
    """
    p = calc_win_rate(attacker, defender)
    if random.random() < p:
        winner, loser = attacker, defender
    else:
        winner, loser = defender, attacker

    base_damage = get_damage(winner, loser)
    # 败者多掉一点血：适度上调，保持上限由 HP.reduce 自然处理
    loser_damage = max(1, int(base_damage * 1.15))

    # 赢家也掉血，但不超过败者的一半：在 15%~40% 的范围取随机值
    rnd_ratio = random.uniform(0.15, 0.40)
    winner_damage = int(loser_damage * rnd_ratio)
    winner_damage = max(0, min(winner_damage, loser_damage // 2))

    return winner, loser, loser_damage, winner_damage

def get_escape_success_rate(attacker: "Avatar", defender: "Avatar") -> float:
    """
    逃跑成功率：临时返回常量值，后续可基于双方能力细化。
    attacker: 追击方（通常为进攻者）
    defender: 逃跑方（通常为被攻击者）
    """
    return 0.1

def get_damage(winner: "Avatar", loser: "Avatar") -> int:
    """
    伤害计算（返回单次战斗伤害值，整数）：
    1) 先计算“期望伤害” expected：
       - 境界差：base = 100 + 80 × gap，其中 gap = max(0, winnerRealmOrder - loserRealmOrder)
       - 功法品阶差：按品阶差 bonus 调整 expected *= (1 + bonus)
       - 属性克制：若胜者克制败者，再乘 1.15
       - 夹紧：期望伤害最终限制在 [30, 500]
    2) 再生成随机区间：[low, high] = [0.85×expected, 1.15×expected]
    3) 下限与比例保护：不低于败者最大HP的 10%，并至少为 15 的硬下限
    4) 返回区间内的随机整数
    """
    gap = max(0, _realm_order(winner.cultivation_progress.realm) - _realm_order(loser.cultivation_progress.realm))
    expected = 100 + 80 * gap
    win_grade = getattr(getattr(winner, "technique", None), "grade", None)
    lose_grade = getattr(getattr(loser, "technique", None), "grade", None)
    expected *= (1.0 + get_grade_advantage_bonus(win_grade, lose_grade))
    win_attr = getattr(getattr(winner, "technique", None), "attribute", None)
    lose_attr = getattr(getattr(loser, "technique", None), "attribute", None)
    if win_attr is not None and lose_attr is not None:
        if get_suppression_bonus(win_attr, lose_attr) > 0:
            expected *= 1.15
    # 期望伤害夹紧
    expected = max(30.0, min(500.0, expected))

    # 设定伤害区间并随机
    low = int(expected * 0.85)
    high = int(expected * 1.15)

    # 与最大HP挂钩的最低保护
    loser_max_hp = getattr(getattr(loser, "hp", None), "max", 0) or 0
    hp_floor = int(max(15, loser_max_hp * 0.10))
    low = max(low, hp_floor)
    high = max(high, low + 1)

    return random.randint(low, high)