from __future__ import annotations

import random
from typing import Optional

from src.utils.config import CONFIG
from src.classes.avatar import Avatar
from src.classes.event import Event
from src.classes.story_teller import StoryTeller
from src.classes.technique import TechniqueGrade, get_random_upper_technique_for_avatar
from src.classes.treasure import Treasure, treasures_by_id


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


def _is_rogue_and_under_equipped(avatar: Avatar) -> bool:
    # 必须散修；法宝为空 或 功法非上品
    if avatar.sect is not None:
        return False
    has_no_treasure = avatar.treasure is None
    is_tech_lower = (avatar.technique is None) or (avatar.technique.grade is not TechniqueGrade.UPPER)
    return has_no_treasure or is_tech_lower


def _choose_kind(avatar: Avatar) -> str:
    # 如果无法宝，偏向法宝；否则若功法非上品，偏向功法；否则随机
    no_treasure = avatar.treasure is None
    tech_not_upper = (avatar.technique is None) or (avatar.technique.grade is not TechniqueGrade.UPPER)
    if no_treasure and tech_not_upper:
        return random.choice(["treasure", "technique"])  # 两者都缺，随机其一
    if no_treasure:
        return "treasure"
    if tech_not_upper:
        return "technique"
    return random.choice(["treasure", "technique"])


def _pick_theme(kind: str) -> str:
    if kind == "treasure":
        return random.choice(F_TREASURE_THEMES)
    return random.choice(F_TECHNIQUE_THEMES)


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
    - 触发条件：散修，且（无法宝 或 功法非上品）。
    - 结果：先决定奖励类型（法宝/功法），法宝世界唯一且不可重复；功法可重复但优先上品且需与灵根兼容。
    - 故事：仅给出主旨主题，由 LLM 自由发挥生成短故事。
    """
    prob = float(getattr(CONFIG.game, "fortune_probability", 0.0))
    if prob <= 0.0:
        return []
    if not _is_rogue_and_under_equipped(avatar):
        return []
    if random.random() >= prob:
        return []

    kind = _choose_kind(avatar)
    theme = _pick_theme(kind)

    res_text: str = ""

    if kind == "treasure":
        tr = _get_unique_treasure_for_world(avatar)
        if tr is None:
            # 回退到功法
            kind = "technique"
        else:
            avatar.treasure = tr
            res_text = f"{avatar.name} 获得法宝『{tr.name}』"

    if kind == "technique":
        tech = get_random_upper_technique_for_avatar(avatar)
        if tech is None:
            # 若无可用上品，则不奖励
            return []
        avatar.technique = tech
        res_text = f"{avatar.name} 得到上品功法『{tech.name}』"

    # 生成故事
    event_text = f"遭遇奇遇（{theme}），{res_text}"
    story_prompt = (
        f"请据此写100~150字小故事。"
    )
    story = StoryTeller.tell_from_actors(event_text, res_text, avatar, prompt=story_prompt)

    events: list[Event] = [
        Event(avatar.world.month_stamp, event_text),
        Event(avatar.world.month_stamp, story),
    ]
    return events


__all__ = [
    "try_trigger_fortune",
]


