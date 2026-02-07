from __future__ import annotations

import random
from enum import Enum
from typing import Optional

from src.utils.config import CONFIG
from src.classes.avatar import Avatar
from src.classes.event import Event
from src.classes.story_teller import StoryTeller

class MisfortuneKind(Enum):
    """霉运类型"""
    LOSS_SPIRIT_STONE = "loss_spirit_stone" # 破财
    INJURY = "injury"                       # 受伤
    CULTIVATION_BACKLASH = "backlash"       # 修为倒退


MF_LOSS_SPIRIT_STONE_THEME_IDS: list[str] = [
    "misfortune_theme_pickpocket",
    "misfortune_theme_fake_goods",
    "misfortune_theme_blackmail",
    "misfortune_theme_theft",
    "misfortune_theme_gambling_loss",
    "misfortune_theme_bad_investment",
]

MF_INJURY_THEME_IDS: list[str] = [
    "misfortune_theme_cultivation_accident",
    "misfortune_theme_trip_fall",
    "misfortune_theme_beast_ambush",
    "misfortune_theme_enemy_attack",
    "misfortune_theme_trap",
    "misfortune_theme_disaster",
]

MF_BACKLASH_THEME_IDS: list[str] = [
    "misfortune_theme_heart_demon",
    "misfortune_theme_qi_deviation",
    "misfortune_theme_confusion",
    "misfortune_theme_anxiety",
]


def _choose_misfortune_kind(avatar: Avatar) -> Optional[MisfortuneKind]:
    """选择霉运类型"""
    candidates = []
    
    # 破财：必须有灵石
    if avatar.magic_stone.value > 0:
        candidates.append(MisfortuneKind.LOSS_SPIRIT_STONE)
    
    # 受伤：任何人都可以受伤
    candidates.append(MisfortuneKind.INJURY)
    
    # 修为倒退：只有修炼者（有修为且未满？）或者任何人都可以？
    # 简单处理：任何人都可以走火入魔
    candidates.append(MisfortuneKind.CULTIVATION_BACKLASH)
    
    if not candidates:
        return None
        
    return random.choice(candidates)


def _get_misfortune_theme(theme_id: str) -> str:
    """获取翻译后的霉运主题文本"""
    from src.i18n import t
    return t(theme_id)


def _pick_misfortune_theme(kind: MisfortuneKind) -> str:
    theme_id = ""
    if kind == MisfortuneKind.LOSS_SPIRIT_STONE:
        theme_id = random.choice(MF_LOSS_SPIRIT_STONE_THEME_IDS)
    elif kind == MisfortuneKind.INJURY:
        theme_id = random.choice(MF_INJURY_THEME_IDS)
    elif kind == MisfortuneKind.CULTIVATION_BACKLASH:
        theme_id = random.choice(MF_BACKLASH_THEME_IDS)
    
    return _get_misfortune_theme(theme_id) if theme_id else ""


async def try_trigger_misfortune(avatar: Avatar) -> list[Event]:
    """
    触发霉运
    规则：
    - 概率：config + effects
    - 类型：破财、受伤、修为倒退
    - 破财：随机数，不超过总量
    - 受伤：扣减HP，可能致死（由simulator结算）
    - 修为倒退：扣减经验，不降级（经验值可为负？）-> 此处逻辑：扣减当前经验，最小为0
    """
    base_prob = float(getattr(CONFIG.game, "misfortune_probability", 0.0))
    extra_prob = float(avatar.effects.get("extra_misfortune_probability", 0.0))
    prob = base_prob + extra_prob
    if prob <= 0.0:
        return []

    # 检查当前动作状态是否允许触发世界事件
    if not avatar.can_trigger_world_event:
        return []
    
    if random.random() >= prob:
        return []
        
    kind = _choose_misfortune_kind(avatar)
    if kind is None:
        return []
        
    theme = _pick_misfortune_theme(kind)
    res_text: str = ""
    
    from src.i18n import t

    if kind == MisfortuneKind.LOSS_SPIRIT_STONE:
        # 破财：随机数，不超过总量
        max_loss = avatar.magic_stone.value
        # 设定一个随机范围，例如 10~500，但受 max_loss 限制
        # 或者完全随机
        loss = random.randint(50, 300)
        loss = min(loss, max_loss)
        avatar.magic_stone.value -= loss
        res_text = t("misfortune_result_loss_spirit_stone", name=avatar.name, amount=loss)
        
    elif kind == MisfortuneKind.INJURY:
        # 受伤：扣减HP
        # 扣减量：最大生命值的 10%~30% + 固定值
        max_hp = avatar.hp.max
        ratio = random.uniform(0.1, 0.3)
        damage = int(max_hp * ratio) + random.randint(10, 50)
        
        avatar.hp.cur -= damage
        # 注意：这里可能扣成负数，simulator 会在 _phase_resolve_death 中处理
        res_text = t("misfortune_result_injury", name=avatar.name, damage=damage, current=avatar.hp.cur, max=max_hp)
        
    elif kind == MisfortuneKind.CULTIVATION_BACKLASH:
        # 修为倒退
        # 扣减量：100~500
        loss = random.randint(100, 500)
        
        # 确保不扣到负数（或者允许负数？通常经验不为负）
        # 这里只扣减当前经验，不掉级
        current_exp = avatar.cultivation_progress.exp
        actual_loss = min(current_exp, loss)
        avatar.cultivation_progress.exp -= actual_loss
        
        res_text = t("misfortune_result_backlash", name=avatar.name, amount=actual_loss)
        
    # 生成故事
    event_text = t("misfortune_event_format", theme=theme, result=res_text)
    story_prompt = t("misfortune_story_prompt")
    
    month_at_finish = avatar.world.month_stamp
    base_event = Event(month_at_finish, event_text, related_avatars=[avatar.id], is_major=True)
    
    story = await StoryTeller.tell_story(
        event_text, res_text, avatar, 
        prompt=story_prompt, 
        allow_relation_changes=False
    )
    story_event = Event(month_at_finish, story, related_avatars=[avatar.id], is_story=True)
    
    return [base_event, story_event]

