from __future__ import annotations

import math
import random
from typing import Tuple, TYPE_CHECKING

from src.classes.technique import TechniqueGrade, get_suppression_bonus

if TYPE_CHECKING:
    from src.classes.avatar import Avatar


# 战斗力参数（参考文明6思想，但适配本项目数值体系）
_STRENGTH_LOG_SCALE: float = 10.0            # 修为强度的对数缩放：10×ln(1+level)
_GRADE_POINTS = {
    TechniqueGrade.LOWER: 0.0,
    TechniqueGrade.MIDDLE: 3.0,
    TechniqueGrade.UPPER: 6.0,
}
_SUPPRESSION_POINTS: float = 3.0             # 属性克制即加固定战斗力点数
_CIV6_K: float = 0.04                        # 伤害指数系数：e^(K×差值)
_WIN_BETA: float = 0.15                      # 胜率逻辑函数斜率
_MIN_WIN_RATE: float = 0.01                  # 最小胜率
_MAX_WIN_RATE: float = 0.99                  # 最大胜率
_BASE_DAMAGE_LOW: int = 24                   # 基础伤害下限（按 defender.maxHP/100 缩放）
_BASE_DAMAGE_HIGH: int = 36                  # 基础伤害上限（按 defender.maxHP/100 缩放）
_MIN_RATIO: float = 1.05                     # 最小相对优势比，确保赢家伤害严格更低
_PAIR_BIAS: float = 1.1                     # 成对偏置：让败者再多一点、赢家再少一点


def get_base_strength(self_avatar: "Avatar") -> float:
    """
    基础战斗力：与对手无关。
    = 10×ln(1+修为等级) + 品阶点数(0/3/6)
    """
    level = max(1, self_avatar.cultivation_progress.level)
    strength_from_level = _STRENGTH_LOG_SCALE * math.log1p(level)
    grade_points = 0.0
    if self_avatar.technique is not None:
        grade_points = _GRADE_POINTS.get(self_avatar.technique.grade, 0.0)
    # 来自效果的额外战斗力点数（例如法宝带来的被动加成）
    extra_raw = self_avatar.effects.get("extra_battle_strength_points", 0)
    extra_points = float(extra_raw or 0.0)
    return strength_from_level + grade_points + extra_points


def _combat_strength_vs(opponent: "Avatar", self_avatar: "Avatar") -> float:
    """
    相对战斗力：= 基础战斗力 + 克制点数(若克制则+3)
    """
    base = get_base_strength(self_avatar)
    suppression_points = 0.0
    if self_avatar.technique is not None and opponent.technique is not None:
        if get_suppression_bonus(self_avatar.technique.attribute, opponent.technique.attribute) > 0.0:
            suppression_points = _SUPPRESSION_POINTS
    return base + suppression_points


def _strength_diff(attacker: "Avatar", defender: "Avatar") -> float:
    return _combat_strength_vs(defender, attacker) - _combat_strength_vs(attacker, defender)


def get_effective_strength(self_avatar: "Avatar", opponent: "Avatar") -> float:
    """
    对外公开：返回 self_avatar 面对 opponent 时的折算战斗力。
    用于事件展示与调试，不参与状态修改。
    """
    return _combat_strength_vs(opponent, self_avatar)


def get_effective_strength_pair(a: "Avatar", b: "Avatar") -> tuple[float, float]:
    """
    一次性返回双方（a 面对 b，b 面对 a）的折算战斗力。
    顺序：(a_strength, b_strength)
    """
    return _combat_strength_vs(b, a), _combat_strength_vs(a, b)


def calc_win_rate(attacker: "Avatar", defender: "Avatar") -> float:
    """
    胜率 = sigmoid(β×战斗力差)，并夹紧到 [0.1, 0.9]
    - 战斗力差 = 有效战斗力(att) - 有效战斗力(def)
    - β 默认 0.15，使差值≈10时胜率≈0.82
    """
    diff = _strength_diff(attacker, defender)
    p = 1.0 / (1.0 + math.exp(-_WIN_BETA * diff))
    if p < _MIN_WIN_RATE:
        return _MIN_WIN_RATE
    if p > _MAX_WIN_RATE:
        return _MAX_WIN_RATE
    return p


def _base_damage_scale(defender: "Avatar") -> float:
    # 以 100 HP 为基准，将 Civ6 的 24~36 损伤映射到不同境界的 HP 档位
    max_hp = defender.hp.max
    return max(1.0, max_hp / 100.0)


def _damage_from_to(attacker: "Avatar", defender: "Avatar") -> int:
    """
    使用 Civ6 风格伤害：damage = U(24,36)×scale × e^(K×差值)
    - scale = defender.maxHP / 100，使不同境界下伤害相对一致
    - 差值 = strength(att) - strength(def)
    """
    diff = _strength_diff(attacker, defender)
    base = random.randint(_BASE_DAMAGE_LOW, _BASE_DAMAGE_HIGH) * _base_damage_scale(defender)
    dmg = base * math.exp(_CIV6_K * diff)
    return max(1, int(dmg))


def _damage_pair(winner: "Avatar", loser: "Avatar") -> tuple[int, int]:
    """
    成对伤害：使用同一基础与对称比值，保证赢家伤害严格小于败者伤害。
    - ratio = max(exp(K×|diff|), MIN_RATIO)
    - 中间尺度 = 几何均值 sqrt(scale_winner × scale_loser)
    - 败者伤害 = base × 中间尺度 × ratio
    - 赢家伤害 = base × 中间尺度 ÷ ratio
    """
    abs_diff = abs(_strength_diff(winner, loser))
    ratio = math.exp(_CIV6_K * abs_diff)
    ratio *= _PAIR_BIAS
    if ratio < _MIN_RATIO:
        ratio = _MIN_RATIO

    base = random.randint(_BASE_DAMAGE_LOW, _BASE_DAMAGE_HIGH)
    scale_w = _base_damage_scale(winner)
    scale_l = _base_damage_scale(loser)
    mid_scale = math.sqrt(scale_w * scale_l)

    loser_damage = max(1, int(base * mid_scale * ratio))
    winner_damage = max(1, int(base * mid_scale / ratio))
    return loser_damage, winner_damage


def decide_battle(attacker: "Avatar", defender: "Avatar") -> Tuple["Avatar", "Avatar", int, int]:
    """
    结算战斗，返回 (胜者, 败者, 败者掉血, 赢家掉血)。
    - 胜率由战斗力差的逻辑函数给出；
    - 双方伤害均按 Civ6 风格由同一差值决定（对称公式），HP 与战斗力独立。
    """
    p = calc_win_rate(attacker, defender)
    if random.random() < p:
        winner, loser = attacker, defender
    else:
        winner, loser = defender, attacker

    loser_damage, winner_damage = _damage_pair(winner, loser)
    return winner, loser, loser_damage, winner_damage


def get_escape_success_rate(attacker: "Avatar", defender: "Avatar") -> float:
    """
    逃跑成功率：defender 试图从 attacker 身边逃离
    基础成功率 0.1，可通过 defender 的 effects 提升
    """
    base_rate = 0.1
    bonus = float(defender.effects.get("extra_escape_success_rate", 0.0))
    return max(0.0, min(1.0, base_rate + bonus))