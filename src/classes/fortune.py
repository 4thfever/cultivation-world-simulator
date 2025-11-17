from __future__ import annotations

import random
from enum import Enum
from typing import Optional
import asyncio

from src.utils.config import CONFIG
from src.classes.avatar import Avatar
from src.classes.event import Event
from src.classes.story_teller import StoryTeller
from src.classes.technique import (
    TechniqueGrade,
    get_random_upper_technique_for_avatar,
    techniques_by_id,
    Technique,
    is_attribute_compatible_with_root,
    TechniqueAttribute,
)
from src.classes.weapon import Weapon, weapons_by_id
from src.classes.auxiliary import Auxiliary, auxiliaries_by_id
from src.classes.equipment_grade import EquipmentGrade
from src.classes.relation import Relation
from src.classes.alignment import Alignment


class FortuneKind(Enum):
    """奇遇类型"""
    WEAPON = "weapon"               # 兵器奇遇
    AUXILIARY = "auxiliary"         # 辅助装备奇遇
    TECHNIQUE = "technique"
    FIND_MASTER = "find_master"
    SPIRIT_STONE = "spirit_stone"   # 灵石奇遇
    CULTIVATION = "cultivation"     # 修为奇遇


F_WEAPON_THEMES: list[str] = [
    "误入洞府",
    "巧捡神兵",
    "误入试炼",
    "异象出世",
    "高人赠予",
]

F_AUXILIARY_THEMES: list[str] = [
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

F_SPIRIT_STONE_THEMES: list[str] = [
    "偶遇灵矿",
    "洞府遗财",
    "击杀妖兽",
    "交易获利",
    "赌石得宝",
    "拾遗藏宝",
]

F_CULTIVATION_THEMES: list[str] = [
    "顿悟玄机",
    "古碑感悟",
    "服食灵药",
    "秘境修炼",
    "前辈灌顶",
    "灵泉淬体",
    "传承记忆",
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


def _can_get_weapon(avatar: Avatar) -> bool:
    """检查是否可以获得兵器奇遇：当前兵器是普通级时可触发"""
    if avatar.weapon is None:
        return True
    return avatar.weapon.grade == EquipmentGrade.COMMON


def _can_get_auxiliary(avatar: Avatar) -> bool:
    """检查是否可以获得辅助装备奇遇：无辅助装备或辅助装备非法宝级时可触发"""
    if avatar.auxiliary is None:
        return True
    return avatar.auxiliary.grade != EquipmentGrade.ARTIFACT


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


def _can_get_spirit_stone(avatar: Avatar) -> bool:
    """检查是否可以获得灵石奇遇"""
    # 任何人都可以获得灵石
    return True


def _can_get_cultivation(avatar: Avatar) -> bool:
    """检查是否可以获得修为奇遇"""
    # 只有未达到瓶颈的人才能获得修为
    return not avatar.cultivation_progress.is_in_bottleneck()


def _choose_kind(avatar: Avatar) -> FortuneKind:
    """
    从所有可能的奇遇中随机选择一个。
    可能的奇遇取决于角色当前状态。
    """
    possible_kinds: list[FortuneKind] = []
    
    # 兵器奇遇：当前兵器是普通级时可触发
    if _can_get_weapon(avatar):
        possible_kinds.append(FortuneKind.WEAPON)
    
    # 辅助装备奇遇：无辅助装备或辅助装备非法宝级时可触发
    if _can_get_auxiliary(avatar):
        possible_kinds.append(FortuneKind.AUXILIARY)
    
    # 功法奇遇：任何人功法非上品都可以（实际获得时会有限制）
    if _can_get_technique(avatar):
        possible_kinds.append(FortuneKind.TECHNIQUE)
    
    # 拜师奇遇：无师傅且世界中有合适的师傅
    if _can_get_master(avatar):
        possible_kinds.append(FortuneKind.FIND_MASTER)
    
    # 灵石奇遇：任何人都可以
    if _can_get_spirit_stone(avatar):
        possible_kinds.append(FortuneKind.SPIRIT_STONE)
    
    # 修为奇遇：未达到瓶颈的人可以
    if _can_get_cultivation(avatar):
        possible_kinds.append(FortuneKind.CULTIVATION)
    
    if not possible_kinds:
        return None
    
    return random.choice(possible_kinds)


def _pick_theme(kind: FortuneKind) -> str:
    if kind == FortuneKind.WEAPON:
        return random.choice(F_WEAPON_THEMES)
    elif kind == FortuneKind.AUXILIARY:
        return random.choice(F_AUXILIARY_THEMES)
    elif kind == FortuneKind.TECHNIQUE:
        return random.choice(F_TECHNIQUE_THEMES)
    elif kind == FortuneKind.FIND_MASTER:
        return random.choice(F_FIND_MASTER_THEMES)
    elif kind == FortuneKind.SPIRIT_STONE:
        return random.choice(F_SPIRIT_STONE_THEMES)
    elif kind == FortuneKind.CULTIVATION:
        return random.choice(F_CULTIVATION_THEMES)
    return ""


def _get_weapon_for_avatar(avatar: Avatar) -> Optional[Weapon]:
    """
    获取兵器：优先法宝 > 宝物 > 普通
    - 法宝：检查世界唯一性
    - 宝物：可重复
    - 普通：可重复
    """
    # 尝试获取法宝级兵器
    owned_artifact_ids: set[int] = set()
    for other in avatar.world.avatar_manager.avatars.values():
        if other.weapon is not None and other.weapon.grade == EquipmentGrade.ARTIFACT:
            owned_artifact_ids.add(other.weapon.id)
    
    artifact_candidates = [w for w in weapons_by_id.values() 
                          if w.grade == EquipmentGrade.ARTIFACT and w.id not in owned_artifact_ids]
    if artifact_candidates:
        return random.choice(artifact_candidates)
    
    # 尝试获取宝物级兵器
    treasure_candidates = [w for w in weapons_by_id.values() 
                          if w.grade == EquipmentGrade.TREASURE]
    if treasure_candidates:
        return random.choice(treasure_candidates)
    
    # 回退到普通级兵器（理论上不应该走到这里，因为普通级兵器不应该通过奇遇获得）
    return None


def _get_auxiliary_for_avatar(avatar: Avatar) -> Optional[Auxiliary]:
    """
    获取辅助装备：优先法宝 > 宝物
    - 法宝：检查世界唯一性
    - 宝物：可重复
    """
    # 尝试获取法宝级辅助装备
    owned_artifact_ids: set[int] = set()
    for other in avatar.world.avatar_manager.avatars.values():
        if other.auxiliary is not None and other.auxiliary.grade == EquipmentGrade.ARTIFACT:
            owned_artifact_ids.add(other.auxiliary.id)
    
    artifact_candidates = [a for a in auxiliaries_by_id.values() 
                          if a.grade == EquipmentGrade.ARTIFACT and a.id not in owned_artifact_ids]
    if artifact_candidates:
        return random.choice(artifact_candidates)
    
    # 尝试获取宝物级辅助装备
    treasure_candidates = [a for a in auxiliaries_by_id.values() 
                          if a.grade == EquipmentGrade.TREASURE]
    if treasure_candidates:
        return random.choice(treasure_candidates)
    
    return None


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


def _get_spirit_stone_amount(avatar: Avatar) -> int:
    """根据境界返回灵石数量（相当于一年狩猎售卖的收入）"""
    from src.classes.cultivation import Realm
    
    realm_ranges = {
        Realm.Qi_Refinement: (20, 30),
        Realm.Foundation_Establishment: (100, 150),
        Realm.Core_Formation: (200, 300),
        Realm.Nascent_Soul: (400, 600),
    }
    range_tuple = realm_ranges.get(
        avatar.cultivation_progress.realm, 
        (20, 30)  # 默认值
    )
    return random.randint(*range_tuple)


def _get_cultivation_exp(avatar: Avatar) -> int:
    """根据境界返回修为经验（相当于一年修炼的收益）"""
    from src.classes.cultivation import Realm
    
    realm_exp = {
        Realm.Qi_Refinement: 600,
        Realm.Foundation_Establishment: 800,
        Realm.Core_Formation: 1000,
        Realm.Nascent_Soul: 1200,
    }
    return realm_exp.get(
        avatar.cultivation_progress.realm,
        600  # 默认值
    )


async def try_trigger_fortune(avatar: Avatar) -> list[Event]:
    """
    在月度结算阶段尝试触发奇遇。
    规则：
    - 奇遇不是一个 action；仅在条件满足时以概率触发。
    - 触发条件：
      * 兵器奇遇：当前兵器是普通级
      * 辅助装备奇遇：无辅助装备或辅助装备非法宝级
      * 功法奇遇：功法非上品（不限散修/宗门，但宗门弟子只能获得本宗门或无宗门功法）
      * 拜师奇遇：无师傅且世界中有合适的师傅（优先同宗门，不能拜敌对阵营）
      * 灵石奇遇：任何人都可以触发
      * 修为奇遇：未达到瓶颈的人可以触发
    - 结果：
      * 兵器：优先法宝（世界唯一）> 宝物（可重复）
      * 辅助装备：优先法宝（世界唯一）> 宝物（可重复）
      * 功法：可重复，优先上品，需与灵根兼容，宗门弟子受宗门限制
      * 拜师：建立师徒关系
      * 灵石：根据境界获得灵石（相当于一年狩猎售卖收入）
      * 修为：根据境界增加修为经验（相当于一年修炼收益）
    - 故事：仅给出主旨主题，由 LLM 自由发挥生成短故事。
    """
    base_prob = float(getattr(CONFIG.game, "fortune_probability", 0.0))
    extra_prob = float(avatar.effects.get("extra_fortune_probability", 0.0))
    prob = base_prob + extra_prob
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

    if kind == FortuneKind.WEAPON:
        weapon = _get_weapon_for_avatar(avatar)
        if weapon is None:
            # 回退到功法
            kind = FortuneKind.TECHNIQUE
            theme = _pick_theme(kind)
        else:
            avatar.change_weapon(weapon)
            res_text = f"{avatar.name} 获得{weapon.grade}兵器『{weapon.name}』"

    if kind == FortuneKind.AUXILIARY:
        auxiliary = _get_auxiliary_for_avatar(avatar)
        if auxiliary is None:
            # 回退到功法
            kind = FortuneKind.TECHNIQUE
            theme = _pick_theme(kind)
        else:
            avatar.change_auxiliary(auxiliary)
            res_text = f"{avatar.name} 获得{auxiliary.grade}辅助装备『{auxiliary.name}』"

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

    elif kind == FortuneKind.SPIRIT_STONE:
        amount = _get_spirit_stone_amount(avatar)
        avatar.magic_stone.value += amount
        res_text = f"{avatar.name} 获得灵石 {amount} 枚"

    elif kind == FortuneKind.CULTIVATION:
        exp_gain = _get_cultivation_exp(avatar)
        avatar.cultivation_progress.add_exp(exp_gain)
        res_text = f"{avatar.name} 修为增长 {exp_gain} 点"

    # 生成故事（异步，等待完成）
    event_text = f"遭遇奇遇（{theme}），{res_text}"
    story_prompt = "请据此写100~150字小故事。"

    month_at_finish = avatar.world.month_stamp
    base_event = Event(month_at_finish, event_text, related_avatars=related_avatars, is_major=True)

    # 生成故事事件
    story = await StoryTeller.tell_from_actors_async(event_text, res_text, *actors_for_story, prompt=story_prompt)
    story_event = Event(month_at_finish, story, related_avatars=related_avatars, is_story=True)

    # 返回基础事件和故事事件
    return [base_event, story_event]


__all__ = [
    "try_trigger_fortune",
]


