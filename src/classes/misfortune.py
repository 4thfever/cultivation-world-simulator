from __future__ import annotations

import random
from enum import Enum
from typing import Optional

from src.utils.config import CONFIG
from src.classes.avatar import Avatar
from src.classes.event import Event
from src.classes.story_teller import StoryTeller
from src.classes.fortune import get_cultivation_exp_reward

class MisfortuneKind(Enum):
    """霉运类型"""
    LOSS_SPIRIT_STONE = "loss_spirit_stone" # 破财
    INJURY = "injury"                       # 受伤
    CULTIVATION_BACKLASH = "backlash"       # 修为倒退


MF_LOSS_SPIRIT_STONE_THEMES: list[str] = [
    "遭遇扒手",
    "误买假货",
    "遭人勒索",
    "洞府失窃",
    "赌石惨败",
    "投资失败",
]

MF_INJURY_THEMES: list[str] = [
    "修炼岔气",
    "出门摔伤",
    "妖兽偷袭",
    "仇家闷棍",
    "误触机关",
    "天降横祸",
]

MF_BACKLASH_THEMES: list[str] = [
    "心魔滋生",
    "灵气逆行",
    "感悟错乱",
    "急火攻心",
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


def _pick_misfortune_theme(kind: MisfortuneKind) -> str:
    if kind == MisfortuneKind.LOSS_SPIRIT_STONE:
        return random.choice(MF_LOSS_SPIRIT_STONE_THEMES)
    elif kind == MisfortuneKind.INJURY:
        return random.choice(MF_INJURY_THEMES)
    elif kind == MisfortuneKind.CULTIVATION_BACKLASH:
        return random.choice(MF_BACKLASH_THEMES)
    return ""


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
    
    if random.random() >= prob:
        return []
        
    kind = _choose_misfortune_kind(avatar)
    if kind is None:
        return []
        
    theme = _pick_misfortune_theme(kind)
    res_text: str = ""
    
    if kind == MisfortuneKind.LOSS_SPIRIT_STONE:
        # 破财：随机数，不超过总量
        max_loss = avatar.magic_stone.value
        # 设定一个随机范围，例如 10~500，但受 max_loss 限制
        # 或者完全随机
        loss = random.randint(50, 300)
        loss = min(loss, max_loss)
        avatar.magic_stone.value -= loss
        res_text = f"{avatar.name} 损失灵石 {loss} 枚"
        
    elif kind == MisfortuneKind.INJURY:
        # 受伤：扣减HP
        # 扣减量：最大生命值的 10%~80% + 固定值
        max_hp = avatar.hp.max
        ratio = random.uniform(0.1, 0.8)
        damage = int(max_hp * ratio) + random.randint(10, 50)
        
        avatar.hp.cur -= damage
        # 注意：这里可能扣成负数，simulator 会在 _phase_resolve_death 中处理
        res_text = f"{avatar.name} 受到伤害 {damage} 点，剩余HP {avatar.hp.cur}/{max_hp}"
        
    elif kind == MisfortuneKind.CULTIVATION_BACKLASH:
        # 修为倒退
        # 扣减量：100~500
        loss = random.randint(100, 500)
        
        # 确保不扣到负数（或者允许负数？通常经验不为负）
        # 这里只扣减当前经验，不掉级
        current_exp = avatar.cultivation_progress.exp
        actual_loss = min(current_exp, loss)
        avatar.cultivation_progress.exp -= actual_loss
        
        res_text = f"{avatar.name} 修为倒退"
        
    # 生成故事
    event_text = f"遭遇霉运（{theme}），{res_text}"
    story_prompt = "请据此写100~300字小故事。只描述倒霉事件本身，不要描述角色的心理活动或者愈挫愈勇。"
    
    month_at_finish = avatar.world.month_stamp
    base_event = Event(month_at_finish, event_text, related_avatars=[avatar.id], is_major=True)
    
    story = await StoryTeller.tell_story(
        event_text, res_text, avatar, 
        prompt=story_prompt, 
        allow_relation_changes=False
    )
    story_event = Event(month_at_finish, story, related_avatars=[avatar.id], is_story=True)
    
    return [base_event, story_event]

