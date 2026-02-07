from __future__ import annotations

import math
import random
from typing import Tuple, TYPE_CHECKING, Callable, Awaitable, Optional

from src.classes.technique import TechniqueGrade, get_suppression_bonus

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar
    from src.classes.event import Event


# 战斗力参数（参考文明6思想，但适配本项目数值体系）
# 境界基础战力
_REALM_BASE_STRENGTH = {
    "Qi_Refinement": 10.0,
    "Foundation_Establishment": 20.0,
    "Core_Formation": 30.0,
    "Nascent_Soul": 40.0,
}
# 小境界（阶段）额外加成
_STAGE_BONUS_STRENGTH = {
    "Early_Stage": 0.0,
    "Middle_Stage": 2.5,
    "Late_Stage": 5.0,
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
    基础战斗力（重构版）：
    = 境界基准值 + 小境界加成 + 额外效果
    """
    # 1. 获取当前境界的基础值
    realm_name = self_avatar.cultivation_progress.realm.name
    base_val = _REALM_BASE_STRENGTH.get(realm_name, 10.0)
    
    # 2. 获取小境界（阶段）加成
    stage_name = self_avatar.cultivation_progress.stage.name
    stage_bonus = _STAGE_BONUS_STRENGTH.get(stage_name, 0.0)
    
    strength_from_level = base_val + stage_bonus
    
    # 来自效果的额外战斗力点数（例如功法、法宝带来的被动加成）
    extra_raw = self_avatar.effects.get("extra_battle_strength_points", 0)
    extra_points = float(extra_raw or 0.0)
    return strength_from_level + extra_points


def _combat_strength_vs(opponent: "Avatar", self_avatar: "Avatar") -> float:
    """
    相对战斗力：= 基础战斗力 + 克制点数(若克制则+3)
    """
    base = get_base_strength(self_avatar)
    
    # 属性克制加成
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

def _damage_pair(winner: "Avatar", loser: "Avatar") -> tuple[int, int]:
    """
    成对伤害：使用同一基础与对称比值，保证赢家伤害严格小于败者伤害。
    - ratio = max(exp(K×|diff|), MIN_RATIO)
    - 中间尺度 = 几何均值 sqrt(scale_winner × scale_loser)
    - 败者伤害 = base × 中间尺度 × ratio × (1 - loser的伤害减免)
    - 赢家伤害 = base × 中间尺度 ÷ ratio × (1 - winner的伤害减免)
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

    # 计算原始伤害
    loser_damage_raw = base * mid_scale * ratio
    winner_damage_raw = base * mid_scale / ratio
    
    # 应用伤害减免效果
    loser_reduction_raw = loser.effects.get("damage_reduction", 0.0)
    loser_reduction = max(0.0, min(1.0, float(loser_reduction_raw or 0.0)))
    winner_reduction_raw = winner.effects.get("damage_reduction", 0.0)
    winner_reduction = max(0.0, min(1.0, float(winner_reduction_raw or 0.0)))
    
    loser_damage = max(1, int(loser_damage_raw * (1.0 - loser_reduction)))
    winner_damage = max(1, int(winner_damage_raw * (1.0 - winner_reduction)))
    
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


def get_assassination_success_rate(attacker: "Avatar", defender: "Avatar") -> float:
    """
    暗杀成功率：
    - 基础 10%
    - 同境界 10%
    - 每高一个大境界 +5%，每低一个大境界 -5%
    - 范围 [1%, 100%]
    """
    from src.systems.cultivation import Realm
    realm_order = {
        Realm.Qi_Refinement: 1,
        Realm.Foundation_Establishment: 2,
        Realm.Core_Formation: 3,
        Realm.Nascent_Soul: 4,
    }
    
    base_rate = 0.10
    
    attacker_rank = realm_order.get(attacker.cultivation_progress.realm, 1)
    defender_rank = realm_order.get(defender.cultivation_progress.realm, 1)
    
    diff = attacker_rank - defender_rank
    rate = base_rate + diff * 0.05
    
    # 应用额外暗杀成功率加成
    extra = float(attacker.effects.get("extra_assassinate_success_rate", 0.0))
    rate += extra
    
    return max(0.01, min(1.0, rate))


async def gen_battle_result_text(
    winner: "Avatar",
    loser: "Avatar",
    l_dmg: int,
    w_dmg: int,
    is_fatal: bool,
    prefix: str = "",
    action_desc: str = "战胜了",
    postfix: str = "",
    check_loot: bool = False
) -> str:
    """
    生成标准战斗结果文本。
    """
    text_prefix = f"{prefix} " if prefix else ""
    if is_fatal:
        text = f"{text_prefix}{winner.name} {action_desc} {loser.name}{postfix}，造成 {l_dmg} 点伤害。{loser.name} 遭受重创，当场陨落。"
        if check_loot:
            from src.classes.kill_and_grab import kill_and_grab
            text += await kill_and_grab(winner, loser)
        return text
    else:
        return f"{text_prefix}{winner.name} {action_desc} {loser.name}{postfix}，{loser.name} 受伤 {l_dmg} 点，{winner.name} 也受伤 {w_dmg} 点。"


async def handle_battle_finish(
    world,
    attacker: "Avatar",
    target: "Avatar",
    res: Tuple["Avatar", "Avatar", int, int],
    start_event_content: str,
    story_prompt: str,
    outcome_text_func: Optional[Callable[["Avatar", "Avatar", int, int, bool], Awaitable[str]]] = None,
    check_loot: bool = False,
    prefix: str = "",
    action_desc: str = "战胜了",
    postfix: str = ""
) -> list["Event"]:
    """
    处理战斗结果的通用逻辑（生成事件、故事、处理死亡）。
    
    Args:
        world: 世界对象
        attacker: 发起者
        target: 目标
        res: decide_battle 的结果 (winner, loser, loser_damage, winner_damage)
        start_event_content: 开始事件的内容（用于故事生成）
        story_prompt: 故事生成的提示词
        outcome_text_func: (可选) 异步回调函数，用于生成结果文本。
                           如果为 None，则使用标准生成逻辑。
                           参数: (winner, loser, loser_damage, winner_damage, is_fatal)
                           返回: 结果文本字符串
        check_loot: 是否检查杀人夺宝（仅当 is_fatal 为 True 且使用默认文本生成时生效，或者 outcome_text_func 自己处理）
        prefix: 默认文本生成的前缀（仅当 outcome_text_func 为 None 时生效）
        action_desc: 默认文本生成的动作描述（仅当 outcome_text_func 为 None 时生效）
        postfix: 默认文本生成的后缀（仅当 outcome_text_func 为 None 时生效）
    """
    from src.classes.event import Event
    from src.classes.story_teller import StoryTeller
    from src.classes.death import handle_death
    from src.classes.death_reason import DeathReason, DeathType

    winner, loser, loser_damage, winner_damage = res
    is_fatal = loser.hp <= 0
    
    # 生成结果文本
    if outcome_text_func:
        result_text = await outcome_text_func(winner, loser, loser_damage, winner_damage, is_fatal)
    else:
        result_text = await gen_battle_result_text(
            winner, loser, loser_damage, winner_damage, is_fatal,
            prefix=prefix, action_desc=action_desc, postfix=postfix, check_loot=check_loot
        )
    
    # 构造事件
    rel_ids = [attacker.id]
    if target:
        rel_ids.append(target.id)
        
    result_event = Event(world.month_stamp, result_text, related_avatars=rel_ids, is_major=True)
    
    # 确定故事生成的起始文本（如果为空则使用结果文本作为兜底）
    start_content = start_event_content
    if not start_content:
        start_content = result_text

    # 生成故事
    story = await StoryTeller.tell_story(
        start_content,
        result_event.content,
        attacker,
        target,
        prompt=story_prompt,
        allow_relation_changes=True
    )
    story_event = Event(world.month_stamp, story, related_avatars=rel_ids, is_story=True)
    
    # 处理死亡
    if is_fatal:
        handle_death(world, loser, DeathReason(DeathType.BATTLE, killer_name=winner.name))
    return [result_event, story_event]
