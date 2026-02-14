from __future__ import annotations

import random
from enum import Enum
from typing import Optional, Any
import asyncio

from src.utils.config import CONFIG
from src.classes.core.avatar import Avatar
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
from src.classes.items.weapon import Weapon, get_random_weapon_by_realm
from src.classes.items.auxiliary import Auxiliary, get_random_auxiliary_by_realm
from src.classes.relation.relation import Relation
from src.classes.alignment import Alignment
from src.systems.cultivation import Realm


class FortuneKind(Enum):
    """奇遇类型"""
    WEAPON = "weapon"               # 兵器奇遇
    AUXILIARY = "auxiliary"         # 辅助装备奇遇
    TECHNIQUE = "technique"
    FIND_MASTER = "find_master"
    SPIRIT_STONE = "spirit_stone"   # 灵石奇遇
    CULTIVATION = "cultivation"     # 修为奇遇


# Fortune theme msgids (for i18n)
F_WEAPON_THEME_IDS: list[str] = [
    "fortune_theme_wandered_into_cave",
    "fortune_theme_found_divine_weapon",
    "fortune_theme_entered_trial",
    "fortune_theme_phenomenon_appeared",
    "fortune_theme_gifted_by_master",
]

F_AUXILIARY_THEME_IDS: list[str] = [
    "fortune_theme_wandered_into_cave",
    "fortune_theme_found_treasure",
    "fortune_theme_entered_trial",
    "fortune_theme_phenomenon_appeared",
    "fortune_theme_guided_by_master",
]

F_TECHNIQUE_THEME_IDS: list[str] = [
    "fortune_theme_wandered_into_cave",
    "fortune_theme_found_treasure",
    "fortune_theme_entered_trial",
    "fortune_theme_guided_by_master",
    "fortune_theme_profound_insight",
]

F_FIND_MASTER_THEME_IDS: list[str] = [
    "fortune_theme_rescued_from_danger",
    "fortune_theme_impressed_by_character",
    "fortune_theme_showed_talent",
    "fortune_theme_chance_encounter",
    "fortune_theme_passed_test",
]

F_SPIRIT_STONE_THEME_IDS: list[str] = [
    "fortune_theme_found_spirit_vein",
    "fortune_theme_cave_treasure",
    "fortune_theme_slayed_beast",
    "fortune_theme_trade_profit",
    "fortune_theme_stone_gambling",
    "fortune_theme_found_cache",
]

F_CULTIVATION_THEME_IDS: list[str] = [
    "fortune_theme_sudden_enlightenment",
    "fortune_theme_ancient_stele",
    "fortune_theme_consumed_spirit_herb",
    "fortune_theme_secret_realm",
    "fortune_theme_empowerment",
    "fortune_theme_spirit_spring",
    "fortune_theme_inherited_memory",
]


def _get_fortune_theme(theme_id: str) -> str:
    """获取翻译后的奇遇主题文本"""
    from src.i18n import t
    return t(theme_id)


def _has_master(avatar: Avatar) -> bool:
    """检查是否已有师傅"""
    for other, rel in avatar.relations.items():
        if rel == Relation.IS_MASTER_OF:
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
    """检查是否可以获得兵器奇遇：当前兵器是练气级（练气）时可触发"""
    if avatar.weapon is None:
        return True
    return avatar.weapon.realm == Realm.Qi_Refinement


def _can_get_auxiliary(avatar: Avatar) -> bool:
    """检查是否可以获得辅助装备奇遇：无辅助装备或辅助装备是练气级时可触发"""
    if avatar.auxiliary is None:
        return True
    return avatar.auxiliary.realm == Realm.Qi_Refinement


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
    """选择并返回翻译后的主题文本"""
    theme_id = ""
    if kind == FortuneKind.WEAPON:
        theme_id = random.choice(F_WEAPON_THEME_IDS)
    elif kind == FortuneKind.AUXILIARY:
        theme_id = random.choice(F_AUXILIARY_THEME_IDS)
    elif kind == FortuneKind.TECHNIQUE:
        theme_id = random.choice(F_TECHNIQUE_THEME_IDS)
    elif kind == FortuneKind.FIND_MASTER:
        theme_id = random.choice(F_FIND_MASTER_THEME_IDS)
    elif kind == FortuneKind.SPIRIT_STONE:
        theme_id = random.choice(F_SPIRIT_STONE_THEME_IDS)
    elif kind == FortuneKind.CULTIVATION:
        theme_id = random.choice(F_CULTIVATION_THEME_IDS)
    
    return _get_fortune_theme(theme_id) if theme_id else ""


def _get_weapon_for_avatar(avatar: Avatar) -> Optional[Weapon]:
    """
    获取兵器：
    奇遇通常提供比当前境界更好的兵器。
    如果是练气期，提供筑基期兵器。
    其他境界提供同境界兵器（因为高境界兵器本身就稀有且强）。
    """
    target_realm = avatar.cultivation_progress.realm
    if target_realm == Realm.Qi_Refinement:
        target_realm = Realm.Foundation_Establishment
        
    return get_random_weapon_by_realm(target_realm)


def _get_auxiliary_for_avatar(avatar: Avatar) -> Optional[Auxiliary]:
    """
    获取辅助装备：
    规则同兵器。
    """
    target_realm = avatar.cultivation_progress.realm
    if target_realm == Realm.Qi_Refinement:
        target_realm = Realm.Foundation_Establishment
        
    return get_random_auxiliary_by_realm(target_realm)


def _get_fortune_technique_for_avatar(avatar: Avatar) -> Optional[Technique]:
    """
    为奇遇获取功法。
    规则：
    1. 散修：可以获得任何上品功法（与灵根/阵营/condition兼容）
    2. 宗门弟子：只能获得本宗门或无宗门的上品功法
    """
    candidates: list[Technique] = []
    
    # 确定允许的宗门 ID 范围
    allowed_sect_ids: set[Optional[int]] = {None}
    if avatar.sect is not None:
        allowed_sect_ids.add(avatar.sect.id)
    
    # 筛选功法
    for t in techniques_by_id.values():
        # 必须是上品
        if t.grade != TechniqueGrade.UPPER:
            continue
        
        # 宗门限制：宗门弟子只能获得本宗门或无宗门的功法
        if t.sect_id not in allowed_sect_ids:
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
    from src.systems.cultivation import Realm
    
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


def get_cultivation_exp_reward(avatar: Avatar) -> int:
    """根据境界返回修为经验（相当于一年修炼的收益）"""
    from src.systems.cultivation import Realm
    
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

    # 检查当前动作状态是否允许触发世界事件
    if not avatar.can_trigger_world_event:
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

    
    # 导入通用决策模块
    from src.classes.single_choice import handle_item_exchange

    if kind == FortuneKind.WEAPON:
        weapon = _get_weapon_for_avatar(avatar)
        if weapon is None:
            # 回退到功法
            kind = FortuneKind.TECHNIQUE
            theme = _pick_theme(kind)
        else:
            from src.i18n import t
            # 使用 str() 来触发 Realm 的 __str__ 方法进行 i18n 翻译。
            intro = t("You discovered a {realm} weapon『{weapon_name}』in your fortune.",
                     realm=str(weapon.realm), weapon_name=weapon.name)
            if avatar.weapon:
                intro += t(" But you already have『{weapon_name}』.", weapon_name=avatar.weapon.name)

            _, exchange_text = await handle_item_exchange(
                avatar=avatar,
                new_item=weapon,
                item_type="weapon",
                context_intro=intro,
                can_sell_new=False
            )
            res_text = t("Discovered weapon『{weapon_name}』, {exchange_text}", 
                        weapon_name=weapon.name, exchange_text=exchange_text)

    if kind == FortuneKind.AUXILIARY:
        auxiliary = _get_auxiliary_for_avatar(avatar)
        if auxiliary is None:
            # 回退到功法
            kind = FortuneKind.TECHNIQUE
            theme = _pick_theme(kind)
        else:
            from src.i18n import t
            # 使用 str() 来触发 Realm 的 __str__ 方法进行 i18n 翻译。
            intro = t("You discovered a {realm} auxiliary『{auxiliary_name}』in your fortune.",
                     realm=str(auxiliary.realm), auxiliary_name=auxiliary.name)
            if avatar.auxiliary:
                intro += t(" But you already have『{auxiliary_name}』.", auxiliary_name=avatar.auxiliary.name)

            _, exchange_text = await handle_item_exchange(
                avatar=avatar,
                new_item=auxiliary,
                item_type="auxiliary",
                context_intro=intro,
                can_sell_new=False
            )
            res_text = t("Discovered auxiliary『{auxiliary_name}』, {exchange_text}",
                        auxiliary_name=auxiliary.name, exchange_text=exchange_text)

    if kind == FortuneKind.TECHNIQUE:
        tech = _get_fortune_technique_for_avatar(avatar)
        if tech is None:
            return []
        
        from src.i18n import t
        intro = t("You comprehended an upper-grade technique『{technique_name}』in your fortune.",
                 technique_name=tech.name)
        if avatar.technique:
            intro += t(" This conflicts with your current technique『{technique_name}』.",
                      technique_name=avatar.technique.name)

        _, exchange_text = await handle_item_exchange(
            avatar=avatar,
            new_item=tech,
            item_type="technique",
            context_intro=intro,
            can_sell_new=False
        )
        res_text = t("Comprehended technique『{technique_name}』, {exchange_text}",
                    technique_name=tech.name, exchange_text=exchange_text)

    elif kind == FortuneKind.FIND_MASTER:
        master = _find_potential_master(avatar)
        if master is None:
            # 找不到合适的师傅
            return []
        # 建立师徒关系：avatar 是徒弟，master 是师傅
        # avatar 视 master 为 MASTER，master 视 avatar 为 DISCIPLE（自动设置对偶）。
        avatar.acknowledge_master(master)
        from src.i18n import t
        res_text = t("{avatar_name} became disciple of {master_name}",
                    avatar_name=avatar.name, master_name=master.name)
        related_avatars.append(master.id)
        actors_for_story = [avatar, master]  # 拜师奇遇需要两个人的信息

    elif kind == FortuneKind.SPIRIT_STONE:
        amount = _get_spirit_stone_amount(avatar)
        avatar.magic_stone.value += amount
        from src.i18n import t
        res_text = t("{avatar_name} obtained {amount} spirit stones",
                    avatar_name=avatar.name, amount=amount)

    elif kind == FortuneKind.CULTIVATION:
        exp_gain = get_cultivation_exp_reward(avatar)
        avatar.cultivation_progress.add_exp(exp_gain)
        from src.i18n import t
        res_text = t("{avatar_name} gained {exp_gain} cultivation experience",
                    avatar_name=avatar.name, exp_gain=exp_gain)

    # 生成故事（异步，等待完成）
    from src.i18n import t
    event_text = t("Encountered fortune ({theme}), {result}",
                   theme=theme, result=res_text)
    story_prompt = t("fortune_story_prompt")

    month_at_finish = avatar.world.month_stamp
    base_event = Event(month_at_finish, event_text, related_avatars=related_avatars, is_major=True)

    # 生成故事事件
    # 奇遇强制单人模式，不改变关系（因为关系已经在硬逻辑中处理了）
    story = await StoryTeller.tell_story(event_text, res_text, *actors_for_story, prompt=story_prompt, allow_relation_changes=False)
    story_event = Event(month_at_finish, story, related_avatars=related_avatars, is_story=True)

    # 返回基础事件和故事事件
    return [base_event, story_event]


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


__all__ = [
    "try_trigger_fortune",
    "get_cultivation_exp_reward",
    "try_trigger_misfortune",
]
