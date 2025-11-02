from __future__ import annotations

import random
from enum import Enum
from typing import Optional
import asyncio

from src.utils.config import CONFIG
from src.classes.avatar import Avatar
from src.classes.event import Event
from src.classes.story_teller import StoryTeller
from src.classes.action.event_helper import EventHelper
from src.utils.asyncio_utils import schedule_background
from src.classes.technique import (
    TechniqueGrade,
    get_random_upper_technique_for_avatar,
    techniques_by_id,
    Technique,
    is_attribute_compatible_with_root,
    TechniqueAttribute,
)
from src.classes.treasure import Treasure, treasures_by_id
from src.classes.relation import Relation
from src.classes.alignment import Alignment


class FortuneKind(Enum):
    """奇遇类型"""
    TREASURE = "treasure"
    TECHNIQUE = "technique"
    FIND_MASTER = "find_master"


F_TREASURE_THEMES: list[str] = [
    "误入洞府",
    "巧捡奇物",
    "误入试炼",
    "异象出世",
    "高人指点",
]

F_TECHNIQUE_THEMES: list[str] = [
    "误入洞府",
    "巧捡奇物",
    "误入试炼",
    "高人指点",
    "玄妙感悟",
]

F_FIND_MASTER_THEMES: list[str] = [
    "危难相救",
    "品行打动",
    "展露天赋",
    "机缘巧合",
    "通过考验",
]


def _has_master(avatar: Avatar) -> bool:
    """检查是否已有师傅"""
    for other, rel in avatar.relations.items():
        if rel == Relation.APPRENTICE:
            return True
    return False


def _is_alignment_compatible(avatar: Avatar, other: Avatar) -> bool:
    """检查两个角色的阵营是否兼容（不是敌对关系）"""
    from src.classes.alignment import Alignment
    if avatar.alignment is None or other.alignment is None:
        return True
    # 正邪不相容
    if avatar.alignment == Alignment.RIGHTEOUS and other.alignment == Alignment.EVIL:
        return False
    if avatar.alignment == Alignment.EVIL and other.alignment == Alignment.RIGHTEOUS:
        return False
    return True


def _find_potential_master(avatar: Avatar) -> Optional[Avatar]:
    """
    在世界中寻找潜在的师傅。
    规则：
    1. 等级 > avatar.level + 20
    2. 优先选择同宗门的高手
    3. 如果没有同宗门的，选择阵营兼容的其他人
    4. 不能拜敌对阵营的人为师
    """
    same_sect_candidates: list[Avatar] = []
    other_candidates: list[Avatar] = []
    
    for other in avatar.world.avatar_manager.avatars.values():
        if other is avatar:
            continue
        
        # 等级差检查
        level_diff = other.cultivation_progress.level - avatar.cultivation_progress.level
        if level_diff < 20:
            continue
        
        # 阵营兼容性检查
        if not _is_alignment_compatible(avatar, other):
            continue
        
        # 同宗门优先
        if avatar.sect is not None and other.sect == avatar.sect:
            same_sect_candidates.append(other)
        else:
            other_candidates.append(other)
    
    # 优先从同宗门选择
    if same_sect_candidates:
        return random.choice(same_sect_candidates)
    
    # 没有同宗门的，从其他候选中选择
    if other_candidates:
        return random.choice(other_candidates)
    
    return None


def _can_get_treasure(avatar: Avatar) -> bool:
    """检查是否可以获得法宝奇遇"""
    return avatar.treasure is None


def _can_get_technique(avatar: Avatar) -> bool:
    """
    检查是否可以获得功法奇遇
    - 任何人功法非上品都可以触发
    - 但实际能否获得功法，在获取时会有额外检查（宗门弟子有限制）
    """
    tech_not_upper = (avatar.technique is None) or (avatar.technique.grade is not TechniqueGrade.UPPER)
    return tech_not_upper


def _can_get_master(avatar: Avatar) -> bool:
    """检查是否可以获得拜师奇遇"""
    if _has_master(avatar):
        return False
    return _find_potential_master(avatar) is not None


def _choose_kind(avatar: Avatar) -> FortuneKind:
    """
    从所有可能的奇遇中随机选择一个。
    可能的奇遇取决于角色当前状态。
    """
    possible_kinds: list[FortuneKind] = []
    
    # 法宝奇遇：任何人无法宝都可以
    if _can_get_treasure(avatar):
        possible_kinds.append(FortuneKind.TREASURE)
    
    # 功法奇遇：任何人功法非上品都可以（实际获得时会有限制）
    if _can_get_technique(avatar):
        possible_kinds.append(FortuneKind.TECHNIQUE)
    
    # 拜师奇遇：无师傅且世界中有合适的师傅
    if _can_get_master(avatar):
        possible_kinds.append(FortuneKind.FIND_MASTER)
    
    if not possible_kinds:
        return None
    
    return random.choice(possible_kinds)


def _pick_theme(kind: FortuneKind) -> str:
    if kind == FortuneKind.TREASURE:
        return random.choice(F_TREASURE_THEMES)
    elif kind == FortuneKind.TECHNIQUE:
        return random.choice(F_TECHNIQUE_THEMES)
    elif kind == FortuneKind.FIND_MASTER:
        return random.choice(F_FIND_MASTER_THEMES)
    return ""


def _get_unique_treasure_for_world(avatar: Avatar) -> Optional[Treasure]:
    """获取世界唯一法宝：从全量里挑选一个未被任何人持有的"""
    owned_ids: set[int] = set()
    for other in avatar.world.avatar_manager.avatars.values():
        if other.treasure is not None:
            owned_ids.add(other.treasure.id)
    candidates = [t for t in treasures_by_id.values() if t.id not in owned_ids]
    if not candidates:
        return None
    return random.choice(candidates)


def _get_fortune_technique_for_avatar(avatar: Avatar) -> Optional[Technique]:
    """
    为奇遇获取功法。
    规则：
    1. 散修：可以获得任何上品功法（与灵根/阵营/condition兼容）
    2. 宗门弟子：只能获得本宗门或无宗门的上品功法
    """
    candidates: list[Technique] = []
    
    # 确定允许的宗门范围
    allowed_sects: set[Optional[str]] = {None, ""}
    if avatar.sect is not None:
        sect_name = avatar.sect.name.strip() if avatar.sect.name else None
        if sect_name:
            allowed_sects.add(sect_name)
    
    # 筛选功法
    for t in techniques_by_id.values():
        # 必须是上品
        if t.grade != TechniqueGrade.UPPER:
            continue
        
        # 宗门限制：宗门弟子只能获得本宗门或无宗门的功法
        tech_sect = t.sect.strip() if t.sect else None
        if tech_sect not in allowed_sects:
            continue
        
        # condition 检查
        if not t.is_allowed_for(avatar):
            continue
        
        # 邪功法只能邪道修士修炼
        if t.attribute == TechniqueAttribute.EVIL and avatar.alignment != Alignment.EVIL:
            continue
        
        # 灵根兼容性
        if not is_attribute_compatible_with_root(t.attribute, avatar.root):
            continue
        
        candidates.append(t)
    
    if not candidates:
        return None
    
    # 按权重随机选择
    weights = [max(0.0, t.weight) for t in candidates]
    return random.choices(candidates, weights=weights, k=1)[0]


def try_trigger_fortune(avatar: Avatar) -> list[Event]:
    """
    在月度结算阶段尝试触发奇遇。
    规则：
    - 奇遇不是一个 action；仅在条件满足时以概率触发。
    - 触发条件：
      * 法宝奇遇：无法宝（不限散修/宗门）
      * 功法奇遇：功法非上品（不限散修/宗门，但宗门弟子只能获得本宗门或无宗门功法）
      * 拜师奇遇：无师傅且世界中有合适的师傅（优先同宗门，不能拜敌对阵营）
    - 结果：
      * 法宝：世界唯一且不可重复
      * 功法：可重复，优先上品，需与灵根兼容，宗门弟子受宗门限制
      * 拜师：建立师徒关系
    - 故事：仅给出主旨主题，由 LLM 自由发挥生成短故事。
    """
    prob = float(getattr(CONFIG.game, "fortune_probability", 0.0))
    if prob <= 0.0:
        return []
    
    if random.random() >= prob:
        return []

    # 从所有可能的奇遇中选择
    kind = _choose_kind(avatar)
    if kind is None:
        return []
    
    theme = _pick_theme(kind)
    res_text: str = ""
    related_avatars = [avatar.id]
    actors_for_story = [avatar]  # 用于生成故事的角色列表

    if kind == FortuneKind.TREASURE:
        tr = _get_unique_treasure_for_world(avatar)
        if tr is None:
            # 回退到功法
            kind = FortuneKind.TECHNIQUE
            theme = _pick_theme(kind)
        else:
            avatar.treasure = tr
            res_text = f"{avatar.name} 获得法宝『{tr.name}』"

    if kind == FortuneKind.TECHNIQUE:
        tech = _get_fortune_technique_for_avatar(avatar)
        if tech is None:
            # 若无可用上品功法（宗门弟子可能因宗门限制而找不到），则不奖励
            return []
        avatar.technique = tech
        res_text = f"{avatar.name} 得到上品功法『{tech.name}』"

    elif kind == FortuneKind.FIND_MASTER:
        master = _find_potential_master(avatar)
        if master is None:
            # 找不到合适的师傅
            return []
        # 建立师徒关系：avatar 是徒弟，master 是师傅
        avatar.set_relation(master, Relation.APPRENTICE)
        res_text = f"{avatar.name} 拜 {master.name} 为师"
        related_avatars.append(master.id)
        actors_for_story = [avatar, master]  # 拜师奇遇需要两个人的信息

    # 生成故事（异步避免阻塞）
    event_text = f"遭遇奇遇（{theme}），{res_text}"
    story_prompt = "请据此写100~150字小故事。"

    month_at_finish = avatar.world.month_stamp
    base_event = Event(month_at_finish, event_text, related_avatars=related_avatars)

    async def _gen_and_push_story():
        # 拜师奇遇传入两个角色，其他奇遇传入一个角色
        story = await StoryTeller.tell_from_actors_async(event_text, res_text, *actors_for_story, prompt=story_prompt)
        story_event = Event(month_at_finish, story, related_avatars=related_avatars)
        # 根据涉及角色数量推送事件
        if len(actors_for_story) == 1:
            EventHelper.push_self(story_event, avatar, to_sidebar=True)
        else:
            # 拜师奇遇涉及两个角色
            EventHelper.push_pair(story_event, initiator=avatar, target=actors_for_story[1], to_sidebar_once=True)

    def _fallback_sync():
        story = StoryTeller.tell_from_actors(event_text, res_text, *actors_for_story, prompt=story_prompt)
        story_event = Event(month_at_finish, story, related_avatars=related_avatars)
        if len(actors_for_story) == 1:
            EventHelper.push_self(story_event, avatar, to_sidebar=True)
        else:
            EventHelper.push_pair(story_event, initiator=avatar, target=actors_for_story[1], to_sidebar_once=True)

    schedule_background(_gen_and_push_story(), fallback=_fallback_sync)

    return [base_event]


__all__ = [
    "try_trigger_fortune",
]


