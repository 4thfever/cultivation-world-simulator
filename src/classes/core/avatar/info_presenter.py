"""
Avatar 信息展示模块

将信息格式化逻辑从 Avatar 类中分离，作为独立函数提供。
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional, List

if TYPE_CHECKING:
    from src.classes.core.avatar.core import Avatar

from src.systems.battle import get_base_strength
from src.classes.relation.relation import get_relation_label
from src.classes.emotions import EMOTION_EMOJIS, EmotionType
from src.utils.config import CONFIG


def _get_effects_text(avatar: "Avatar") -> str:
    """获取格式化的效果文本"""
    from src.i18n import t
    from src.classes.effect import format_effects_to_text
    breakdown = avatar.get_effect_breakdown()
    effect_parts = []
    for source_name, effects in breakdown:
        desc_str = format_effects_to_text(effects)
        if desc_str:
            effect_parts.append(f"[{source_name}] {desc_str}")
    return "\n".join(effect_parts) if effect_parts else t("None")


def get_avatar_info(avatar: "Avatar", detailed: bool = False) -> dict:
    """
    获取 avatar 的信息，返回 dict；根据 detailed 控制信息粒度。
    """
    from src.i18n import t
    region = avatar.tile.region if avatar.tile is not None else None
    from src.classes.relation.relation import get_relations_strs
    relation_lines = get_relations_strs(avatar, max_lines=8)
    relations_info = t("relation_separator").join(relation_lines) if relation_lines else t("None")
    magic_stone_info = str(avatar.magic_stone)

    born_region_name = t("Unknown")
    if avatar.born_region_id and avatar.born_region_id != -1:
         r = avatar.world.map.regions.get(avatar.born_region_id)
         if r:
             born_region_name = r.name

    from src.classes.core.sect import get_sect_info_with_rank
    
    # [新增] 道统 (Orthodoxy)
    orthodoxy_info = t(avatar.orthodoxy.name) if avatar.orthodoxy else t("None")

    if detailed:
        weapon_info = t("{weapon_name}, Proficiency: {proficiency}%", 
                       weapon_name=avatar.weapon.get_detailed_info(), 
                       proficiency=f"{avatar.weapon_proficiency:.1f}") if avatar.weapon else t("None")
        auxiliary_info = avatar.auxiliary.get_detailed_info() if avatar.auxiliary else t("None")
        sect_info = get_sect_info_with_rank(avatar, detailed=True)
        alignment_info = avatar.alignment.get_detailed_info() if avatar.alignment is not None else t("Unknown")
        region_info = region.get_detailed_info() if region is not None else t("None")
        root_info = avatar.root.get_detailed_info()
        technique_info = avatar.technique.get_detailed_info() if avatar.technique is not None else t("None")
        cultivation_info = avatar.cultivation_progress.get_detailed_info()
        personas_info = ", ".join([p.get_detailed_info() for p in avatar.personas]) if avatar.personas else t("None")
        materials_info = t("material_separator").join([f"{mat.get_detailed_info()}x{quantity}" for mat, quantity in avatar.materials.items()]) if avatar.materials else t("None")
        appearance_info = avatar.appearance.get_detailed_info(avatar.gender)
        spirit_animal_info = avatar.spirit_animal.get_info() if avatar.spirit_animal is not None else t("None")
    else:
        weapon_info = avatar.weapon.get_info() if avatar.weapon is not None else t("None")
        auxiliary_info = avatar.auxiliary.get_info() if avatar.auxiliary is not None else t("None")
        sect_info = get_sect_info_with_rank(avatar, detailed=False)
        region_info = region.get_info() if region is not None else t("None")
        alignment_info = avatar.alignment.get_info() if avatar.alignment is not None else t("Unknown")
        root_info = avatar.root.get_info()
        technique_info = avatar.technique.get_info() if avatar.technique is not None else t("None")
        cultivation_info = avatar.cultivation_progress.get_info()
        personas_info = ", ".join([p.get_detailed_info() for p in avatar.personas]) if avatar.personas else t("None")
        materials_info = t("material_separator").join([f"{mat.get_info()}x{quantity}" for mat, quantity in avatar.materials.items()]) if avatar.materials else t("None")
        appearance_info = avatar.appearance.get_info()
        spirit_animal_info = avatar.spirit_animal.get_info() if avatar.spirit_animal is not None else t("None")

    info_dict = {
        t("Name"): avatar.name,
        t("Origin"): born_region_name,
        t("Gender"): str(avatar.gender),
        t("Age"): str(avatar.age),
        t("HP"): str(avatar.hp),
        t("Spirit Stones"): magic_stone_info,
        t("Relations"): relations_info,
        t("Sect"): sect_info,
        t("Orthodoxy"): orthodoxy_info,
        t("Alignment"): alignment_info,
        t("Region"): region_info,
        t("Spirit Root"): root_info,
        t("Technique"): technique_info,
        t("Realm"): cultivation_info,
        t("Traits"): personas_info,
        t("Materials"): materials_info,
        t("Appearance"): appearance_info,
        t("Weapon"): weapon_info,
        t("Auxiliary"): auxiliary_info,
        t("Emotion"): t(avatar.emotion.value),
        t("Current Action"): avatar.current_action_name,
        t("Long-term Goal"): avatar.long_term_objective.content if avatar.long_term_objective else t("None"),
        t("Short-term Goal"): avatar.short_term_objective if avatar.short_term_objective else t("None"),
    }
    
    if detailed:
        info_dict[t("Current Effects")] = _get_effects_text(avatar)
        if avatar.backstory:
            info_dict[t("Backstory")] = avatar.backstory

    # 绰号：仅在存在时显示
    if avatar.nickname is not None:
        info_dict[t("Nickname")] = avatar.nickname.value
    # 灵兽：仅在存在时显示
    if avatar.spirit_animal is not None:
        info_dict[t("Spirit Animal")] = spirit_animal_info
    return info_dict


def get_avatar_structured_info(avatar: "Avatar") -> dict:
    """
    获取结构化的角色信息，用于前端展示和交互。
    """
    # 基础信息
    from src.i18n import t
    emoji = EMOTION_EMOJIS.get(avatar.emotion, EMOTION_EMOJIS[EmotionType.CALM])
    
    born_region_name = t("Unknown")
    if avatar.born_region_id and avatar.born_region_id != -1:
         r = avatar.world.map.regions.get(avatar.born_region_id)
         if r:
             born_region_name = r.name

    start_age = None
    if avatar.cultivation_start_month_stamp is not None:
        start_age = (int(avatar.cultivation_start_month_stamp) - int(avatar.birth_month_stamp)) // 12

    info = {
        "id": avatar.id,
        "name": avatar.name,
        "origin": born_region_name,
        "born_region_id": avatar.born_region_id,
        "cultivation_start_age": start_age,
        "cultivation_start_month_stamp": int(avatar.cultivation_start_month_stamp) if avatar.cultivation_start_month_stamp else None,
        "gender": str(avatar.gender),
        "age": avatar.age.age,
        "lifespan": avatar.age.max_lifespan,
        "realm": avatar.cultivation_progress.get_info(),
        "level": avatar.cultivation_progress.level,
        "hp": {"cur": avatar.hp.cur, "max": avatar.hp.max},
        "alignment": str(avatar.alignment) if avatar.alignment else t("Unknown"),
        "magic_stone": avatar.magic_stone.value,
        "base_battle_strength": int(get_base_strength(avatar)),
        "emotion": {
            "name": t(avatar.emotion.value),
            "emoji": emoji,
            "desc": t(avatar.emotion.value)
        },
        "thinking": avatar.thinking,
        "short_term_objective": avatar.short_term_objective,
        "long_term_objective": avatar.long_term_objective.content if avatar.long_term_objective else "",
        "backstory": avatar.backstory if avatar.backstory else None,
        "nickname": avatar.nickname.value if avatar.nickname else None,
        "nickname_reason": avatar.nickname.reason if avatar.nickname else None,
        "is_dead": avatar.is_dead,
        "death_info": avatar.death_info,
        "action_state": t("Performing {action}", action=avatar.current_action_name)
    }

    # 1. 特质 (Personas)
    info["personas"] = [p.get_structured_info() for p in avatar.personas]
    
    # 2. 功法 (Technique)
    if avatar.technique:
        info["technique"] = avatar.technique.get_structured_info()
    else:
        info["technique"] = None
        
    # 3. 宗门 (Sect)
    if avatar.sect:
        sect_info = avatar.sect.get_structured_info()
        if avatar.sect_rank:
            from src.classes.sect_ranks import get_rank_display_name
            sect_info["rank"] = get_rank_display_name(avatar.sect_rank, avatar.sect)
        else:
            sect_info["rank"] = t("Disciple")
        info["sect"] = sect_info
    else:
        info["sect"] = None
        
    # [新增] 道统 (Orthodoxy)
    # 无论有无宗门，都返回道统信息（散修返回"天地"道统）
    if avatar.orthodoxy:
        info["orthodoxy"] = avatar.orthodoxy.get_info(detailed=True)
    else:
        info["orthodoxy"] = None
        
    # 补充：阵营详情
    from src.classes.alignment import alignment_info_msg_ids
    info["alignment"] = str(avatar.alignment) if avatar.alignment else t("Unknown")
    if avatar.alignment:
        desc_id = alignment_info_msg_ids.get(avatar.alignment, "")
        info["alignment_detail"] = {
            "name": str(avatar.alignment),
            "desc": t(desc_id) if desc_id else "",
        }

    # 4. 装备 (Weapon & Auxiliary)
    if avatar.weapon:
        w_info = avatar.weapon.get_structured_info()
        w_info["proficiency"] = f"{avatar.weapon_proficiency:.1f}%"
        info["weapon"] = w_info
    else:
        info["weapon"] = None
        
    if avatar.auxiliary:
        info["auxiliary"] = avatar.auxiliary.get_structured_info()
    else:
        info["auxiliary"] = None
        
    # 5. 材料 (Materials)
    materials_list = []
    for material, count in avatar.materials.items():
        m_info = material.get_structured_info()
        m_info["count"] = count
        materials_list.append(m_info)
    info["materials"] = materials_list
    
    # 6. 关系 (Relations)
    relations_list = []
    
    # 6.1 添加现有的修仙者关系
    existing_ids = set()
    for other, relation in avatar.relations.items():
        existing_ids.add(other.id)
        relations_list.append({
            "target_id": other.id,
            "name": other.name,
            "relation": get_relation_label(relation, avatar, other),
            "relation_type": relation.value,
            "realm": other.cultivation_progress.get_info(),
            "sect": other.sect.name if other.sect else t("Rogue Cultivator"),
            "is_mortal": False,
            "target_gender": other.gender.value
        })
    
    # 6.2 [新增] 添加凡人子女
    from src.classes.relation.relation import Relation, GENDERED_DISPLAY
    for child in avatar.children:
        if child.id not in existing_ids:
            # 凡人子女: Owner is Parent -> relation should be Relation.PARENT
            # Label should be Son/Daughter
            gender_val = child.gender.value
            # 查找对应的翻译 key (Relation.PARENT, "male") -> "relation_son"
            label_key = GENDERED_DISPLAY.get((Relation.IS_CHILD_OF, gender_val), "child")
            
            relations_list.append({
                "target_id": child.id,
                "name": child.name,
                "relation": t(label_key), 
                "relation_type": Relation.IS_CHILD_OF.value, # 这里的类型应该是 CHILD (Target is Child)
                "realm": t("Mortal"),
                "sect": t("None"),
                "is_mortal": True,
                "target_gender": gender_val
            })

    info["relations"] = relations_list
    
    # 7. 外貌
    info["appearance"] = avatar.appearance.get_info()
    
    # 8. 灵根
    from src.classes.root import format_root_cn
    root_str = format_root_cn(avatar.root)
    info["root"] = root_str
    info["root_detail"] = {
         "name": root_str,
         "desc": t("Contains elements: {elements}", elements=t("element_separator").join(str(e) for e in avatar.root.elements)),
         "effect_desc": avatar.root.effect_desc
    }
    
    # 9. 灵兽
    if avatar.spirit_animal:
         info["spirit_animal"] = avatar.spirit_animal.get_structured_info()

    # 当前效果
    info[t("Current Effects")] = _get_effects_text(avatar)

    return info


def get_avatar_expanded_info(
    avatar: "Avatar", 
    co_region_avatars: Optional[List["Avatar"]] = None,
    other_avatar: Optional["Avatar"] = None,
    detailed: bool = False
) -> dict:
    """
    获取角色的扩展信息，包含基础信息、观察到的角色和事件历史。
    
    Args:
        avatar: 目标角色
        co_region_avatars: 同区域的其他角色列表，用于"观察到的角色"字段
        other_avatar: 另一个角色，如果提供则返回两人共同经历的事件，否则返回单人事件
        detailed: 是否返回详细信息
    """
    from src.i18n import t
    info = get_avatar_info(avatar, detailed=detailed)

    observed: list[str] = []
    if co_region_avatars:
        for other in co_region_avatars[:8]:
            observed.append(t("{name}, Realm: {realm}", name=other.name, realm=other.cultivation_progress.get_info()))

    # 历史事件改为从全局事件管理器分类查询
    em = avatar.world.event_manager
    major_limit = CONFIG.social.major_event_context_num
    minor_limit = CONFIG.social.minor_event_context_num
    
    # 根据是否提供 other_avatar 决定获取单人事件还是双人共同事件
    if other_avatar is not None:
        major_events = em.get_major_events_between(avatar.id, other_avatar.id, limit=major_limit)
        minor_events = em.get_minor_events_between(avatar.id, other_avatar.id, limit=minor_limit)
    else:
        major_events = em.get_major_events_by_avatar(avatar.id, limit=major_limit)
        minor_events = em.get_minor_events_by_avatar(avatar.id, limit=minor_limit)
    
    major_list = [str(e) for e in major_events]
    minor_list = [str(e) for e in minor_events]

    info[t("Nearby Avatars")] = observed
    info[t("Major Events")] = major_list
    info[t("Recent Events")] = minor_list
    return info


def get_other_avatar_info(from_avatar: "Avatar", to_avatar: "Avatar") -> str:
    """
    仅显示几个字段：名字、绰号、境界、关系、宗门、阵营、外貌、功法、武器、辅助装备、HP
    """
    from src.i18n import t
    nickname = to_avatar.nickname.value if to_avatar.nickname else t("None")
    sect = to_avatar.sect.name if to_avatar.sect else t("Rogue Cultivator")
    tech = to_avatar.technique.get_info() if to_avatar.technique else t("None")
    weapon = to_avatar.weapon.get_info() if to_avatar.weapon else t("None")
    aux = to_avatar.auxiliary.get_info() if to_avatar.auxiliary else t("None")
    alignment = to_avatar.alignment
    
    # 关系可能为空
    relation = from_avatar.get_relation(to_avatar) or t("None")

    return t(
        "{name}, Nickname: {nickname}, Realm: {realm}, Relation: {relation}, Sect: {sect}, Alignment: {alignment}, Appearance: {appearance}, Technique: {technique}, Weapon: {weapon}, Auxiliary: {aux}, HP: {hp}",
        name=to_avatar.name,
        nickname=nickname,
        realm=to_avatar.cultivation_progress.get_info(),
        relation=relation,
        sect=sect,
        alignment=alignment,
        appearance=to_avatar.appearance.get_info(),
        technique=tech,
        weapon=weapon,
        aux=aux,
        hp=to_avatar.hp
    )


def get_avatar_desc(avatar: "Avatar", detailed: bool = False) -> str:
    """
    获取角色的文本描述。
    detailed=True 时包含详细的效果来源分析。
    """
    from src.i18n import t
    
    born_region_name = t("Unknown")
    if avatar.born_region_id and avatar.born_region_id != -1:
         r = avatar.world.map.regions.get(avatar.born_region_id)
         if r:
             born_region_name = r.name

    # 基础描述
    lines = [t("【{name}】 {gender} {age} years old", name=avatar.name, gender=avatar.gender, age=avatar.age)]
    lines.append(t("Origin: {origin}", origin=born_region_name))
    lines.append(t("Realm: {realm}", realm=avatar.cultivation_progress.get_info()))
    lines.append(t("Current Action: {action}", action=avatar.current_action_name))
    if avatar.sect:
        lines.append(t("Identity: {identity}", identity=avatar.get_sect_str()))
    
    if detailed:
        if avatar.backstory:
            lines.append(t("Backstory: {backstory}", backstory=avatar.backstory))
        lines.append(t("\n--- Current Effects Detail ---"))
        breakdown = avatar.get_effect_breakdown()
        
        from src.classes.effect import format_effects_to_text
        
        if not breakdown:
            lines.append(t("No additional effects"))
        else:
            for source_name, effects in breakdown:
                # 使用现有的 format_effects_to_text 将字典转为中文描述
                desc_str = format_effects_to_text(effects)
                if desc_str:
                    lines.append(f"[{source_name}]: {desc_str}")
                
    return "\n".join(lines)
