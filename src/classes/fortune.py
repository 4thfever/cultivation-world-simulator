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
from src.classes.technique import TechniqueGrade, get_random_upper_technique_for_avatar
from src.classes.treasure import Treasure, treasures_by_id
from src.classes.relation import Relation


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


def _is_rogue_and_under_equipped(avatar: Avatar) -> bool:
    # 必须散修；法宝为空 或 功法非上品
    if avatar.sect is not None:
        return False
    has_no_treasure = avatar.treasure is None
    is_tech_lower = (avatar.technique is None) or (avatar.technique.grade is not TechniqueGrade.UPPER)
    return has_no_treasure or is_tech_lower


def _has_master(avatar: Avatar) -> bool:
    """检查是否已有师傅"""
    for other, rel in avatar.relations.items():
        if rel == Relation.MASTER:
            return True
    return False


def _find_potential_master(avatar: Avatar) -> Optional[Avatar]:
    """
    在世界中寻找潜在的师傅。
    条件：等级 > avatar.level + 20
    """
    candidates: list[Avatar] = []
    for other in avatar.world.avatar_manager.avatars.values():
        if other is avatar:
            continue
        level_diff = other.cultivation_progress.level - avatar.cultivation_progress.level
        if level_diff >= 20:
            candidates.append(other)
    
    if not candidates:
        return None
    return random.choice(candidates)


def _choose_kind(avatar: Avatar) -> FortuneKind:
    """
    从所有可能的奇遇中随机选择一个。
    可能的奇遇取决于角色当前状态。
    """
    possible_kinds: list[FortuneKind] = []
    
    # 法宝奇遇：散修且无法宝
    if avatar.sect is None and avatar.treasure is None:
        possible_kinds.append(FortuneKind.TREASURE)
    
    # 功法奇遇：散修且功法非上品
    if avatar.sect is None:
        tech_not_upper = (avatar.technique is None) or (avatar.technique.grade is not TechniqueGrade.UPPER)
        if tech_not_upper:
            possible_kinds.append(FortuneKind.TECHNIQUE)
    
    # 拜师奇遇：无师傅且世界中有合适的师傅
    if not _has_master(avatar):
        if _find_potential_master(avatar) is not None:
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
    # 世界唯一法宝：从全量里挑选一个未被任何人持有的
    owned_ids: set[int] = set()
    for other in avatar.world.avatar_manager.avatars.values():
        if other.treasure is not None:
            owned_ids.add(other.treasure.id)
    candidates = [t for t in treasures_by_id.values() if t.id not in owned_ids]
    if not candidates:
        return None
    return random.choice(candidates)


def try_trigger_fortune(avatar: Avatar) -> list[Event]:
    """
    在月度结算阶段尝试触发奇遇。
    规则：
    - 奇遇不是一个 action；仅在条件满足时以概率触发。
    - 触发条件：散修且（无法宝 或 功法非上品），或者无师傅。
    - 结果：先决定奖励类型（法宝/功法/拜师），法宝世界唯一且不可重复；功法可重复但优先上品且需与灵根兼容；拜师建立师徒关系。
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
        tech = get_random_upper_technique_for_avatar(avatar)
        if tech is None:
            # 若无可用上品，则不奖励
            return []
        avatar.technique = tech
        res_text = f"{avatar.name} 得到上品功法『{tech.name}』"

    elif kind == FortuneKind.FIND_MASTER:
        master = _find_potential_master(avatar)
        if master is None:
            # 找不到合适的师傅
            return []
        # 建立师徒关系
        avatar.set_relation(master, Relation.MASTER)
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


