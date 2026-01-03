"""
Avatar 信息展示模块

将信息格式化逻辑从 Avatar 类中分离，作为独立函数提供。
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional, List

if TYPE_CHECKING:
    from src.classes.avatar.core import Avatar

from src.classes.battle import get_base_strength
from src.classes.relation import get_relation_label
from src.utils.config import CONFIG


def _get_effects_text(avatar: "Avatar") -> str:
    """获取格式化的效果文本"""
    from src.utils.effect_desc import format_effects_to_text
    breakdown = avatar.get_effect_breakdown()
    effect_parts = []
    for source_name, effects in breakdown:
        desc_str = format_effects_to_text(effects)
        if desc_str:
            effect_parts.append(f"[{source_name}] {desc_str}")
    return "\n".join(effect_parts) if effect_parts else "无"


def get_avatar_info(avatar: "Avatar", detailed: bool = False) -> dict:
    """
    获取 avatar 的信息，返回 dict；根据 detailed 控制信息粒度。
    """
    region = avatar.tile.region if avatar.tile is not None else None
    from src.classes.relation import get_relations_strs
    relation_lines = get_relations_strs(avatar, max_lines=8)
    relations_info = "；".join(relation_lines) if relation_lines else "无"
    magic_stone_info = str(avatar.magic_stone)

    from src.classes.sect import get_sect_info_with_rank
    
    if detailed:
        weapon_info = f"{avatar.weapon.get_detailed_info()}，熟练度：{avatar.weapon_proficiency:.1f}%" if avatar.weapon else "无"
        auxiliary_info = avatar.auxiliary.get_detailed_info() if avatar.auxiliary else "无"
        sect_info = get_sect_info_with_rank(avatar, detailed=True)
        alignment_info = avatar.alignment.get_detailed_info() if avatar.alignment is not None else "未知"
        region_info = region.get_detailed_info() if region is not None else "无"
        root_info = avatar.root.get_detailed_info()
        technique_info = avatar.technique.get_detailed_info() if avatar.technique is not None else "无"
        cultivation_info = avatar.cultivation_progress.get_detailed_info()
        personas_info = ", ".join([p.get_detailed_info() for p in avatar.personas]) if avatar.personas else "无"
        items_info = "，".join([f"{item.get_detailed_info()}x{quantity}" for item, quantity in avatar.items.items()]) if avatar.items else "无"
        appearance_info = avatar.appearance.get_detailed_info(avatar.gender)
        spirit_animal_info = avatar.spirit_animal.get_info() if avatar.spirit_animal is not None else "无"
    else:
        weapon_info = avatar.weapon.get_info() if avatar.weapon is not None else "无"
        auxiliary_info = avatar.auxiliary.get_info() if avatar.auxiliary is not None else "无"
        sect_info = get_sect_info_with_rank(avatar, detailed=False)
        region_info = region.get_info() if region is not None else "无"
        alignment_info = avatar.alignment.get_info() if avatar.alignment is not None else "未知"
        root_info = avatar.root.get_info()
        technique_info = avatar.technique.get_info() if avatar.technique is not None else "无"
        cultivation_info = avatar.cultivation_progress.get_info()
        personas_info = ", ".join([p.get_detailed_info() for p in avatar.personas]) if avatar.personas else "无"
        items_info = "，".join([f"{item.get_info()}x{quantity}" for item, quantity in avatar.items.items()]) if avatar.items else "无"
        appearance_info = avatar.appearance.get_info()
        spirit_animal_info = avatar.spirit_animal.get_info() if avatar.spirit_animal is not None else "无"

    info_dict = {
        "名字": avatar.name,
        "性别": str(avatar.gender),
        "年龄": str(avatar.age),
        "hp": str(avatar.hp),
        "灵石": magic_stone_info,
        "关系": relations_info,
        "宗门": sect_info,
        "阵营": alignment_info,
        "地区": region_info,
        "灵根": root_info,
        "功法": technique_info,
        "境界": cultivation_info,
        "特质": personas_info,
        "物品": items_info,
        "外貌": appearance_info,
        "兵器": weapon_info,
        "辅助装备": auxiliary_info,
    }
    
    if detailed:
        info_dict["当前效果"] = _get_effects_text(avatar)

    # 绰号：仅在存在时显示
    if avatar.nickname is not None:
        info_dict["绰号"] = avatar.nickname.value
    # 灵兽：仅在存在时显示
    if avatar.spirit_animal is not None:
        info_dict["灵兽"] = spirit_animal_info
    # 长期目标：仅在存在时显示
    if avatar.long_term_objective is not None:
        info_dict["长期目标"] = avatar.long_term_objective.content
    # 短期目标：仅在存在时显示
    if avatar.short_term_objective:
        info_dict["短期目标"] = avatar.short_term_objective
    return info_dict


def get_avatar_structured_info(avatar: "Avatar") -> dict:
    """
    获取结构化的角色信息，用于前端展示和交互。
    """
    # 基础信息
    info = {
        "id": avatar.id,
        "name": avatar.name,
        "gender": str(avatar.gender),
        "age": avatar.age.age,
        "lifespan": avatar.age.max_lifespan,
        "realm": avatar.cultivation_progress.realm.value,
        "level": avatar.cultivation_progress.level,
        "hp": {"cur": avatar.hp.cur, "max": avatar.hp.max},
        "alignment": str(avatar.alignment) if avatar.alignment else "未知",
        "magic_stone": avatar.magic_stone.value,
        "thinking": avatar.thinking,
        "short_term_objective": avatar.short_term_objective,
        "long_term_objective": avatar.long_term_objective.content if avatar.long_term_objective else "",
        "nickname": avatar.nickname.value if avatar.nickname else None,
        "nickname_reason": avatar.nickname.reason if avatar.nickname else None,
        "is_dead": avatar.is_dead,
        "death_info": avatar.death_info,
        "action_state": f"正在{getattr(avatar.current_action.action, 'ACTION_NAME', '思考')}" if hasattr(avatar, "current_action") and avatar.current_action and getattr(avatar.current_action, "action", None) else "思考"
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
            sect_info["rank"] = "弟子"
        info["sect"] = sect_info
    else:
        info["sect"] = None
        
    # 补充：阵营详情
    from src.classes.alignment import alignment_infos, alignment_strs
    info["alignment"] = str(avatar.alignment) if avatar.alignment else "未知"
    if avatar.alignment:
        cn_name = alignment_strs.get(avatar.alignment, avatar.alignment.value)
        desc = alignment_infos.get(avatar.alignment, "")
        info["alignment_detail"] = {
            "name": cn_name,
            "desc": desc,
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
        
    # 5. 物品 (Items)
    items_list = []
    for item, count in avatar.items.items():
        i_info = item.get_structured_info()
        i_info["count"] = count
        items_list.append(i_info)
    info["items"] = items_list
    
    # 6. 关系 (Relations)
    relations_list = []
    for other, relation in avatar.relations.items():
        relations_list.append({
            "target_id": other.id,
            "name": other.name,
            "relation": get_relation_label(relation, avatar, other),
            "realm": other.cultivation_progress.realm.value,
            "sect": other.sect.name if other.sect else "散修"
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
         "desc": f"包含元素：{'、'.join(str(e) for e in avatar.root.elements)}",
         "effect_desc": avatar.root.effect_desc
    }
    
    # 9. 灵兽
    if avatar.spirit_animal:
         info["spirit_animal"] = avatar.spirit_animal.get_structured_info()

    # 当前效果
    info["当前效果"] = _get_effects_text(avatar)

    return info


def get_avatar_hover_info(avatar: "Avatar") -> list[str]:
    """
    返回用于前端悬浮提示的多行信息。
    """
    def add_kv(lines: list[str], key: str, value: object) -> None:
        lines.append(f"{key}: {value}")

    def add_section(lines: list[str], title: str, body: list[str]) -> None:
        lines.append("")
        lines.append(f"{title}:")
        lines.extend(body)

    lines: list[str] = []
    # 基础信息
    if avatar.nickname:
        add_kv(lines, "绰号", f"「{avatar.nickname.value}」")
    
    add_kv(lines, "性别", avatar.gender)
    add_kv(lines, "年龄", avatar.age)
    add_kv(lines, "外貌", avatar.appearance.get_info())
    add_kv(lines, "阵营", avatar.alignment)
    add_kv(lines, "境界", str(avatar.cultivation_progress))
    add_kv(lines, "HP", avatar.hp)
    add_kv(lines, "战斗力", int(get_base_strength(avatar)))
    add_kv(lines, "宗门", avatar.get_sect_str())

    from src.classes.root import format_root_cn
    add_kv(lines, "灵根", format_root_cn(avatar.root))

    tech_str = avatar.technique.get_colored_info() if avatar.technique is not None else "无"
    add_kv(lines, "功法", tech_str)

    if avatar.personas:
        persona_parts = [p.get_colored_info() for p in avatar.personas]
        add_kv(lines, "特质", ", ".join(persona_parts))

    add_kv(lines, "灵石", str(avatar.magic_stone))

    # 物品
    if avatar.items:
        items_lines = [f"  {item.name} x{quantity}" for item, quantity in avatar.items.items()]
        add_section(lines, "物品", items_lines)
    else:
        add_kv(lines, "物品", "无")

    # 思考与目标
    if avatar.thinking:
        add_section(lines, "思考", [avatar.thinking])
    if avatar.long_term_objective:
        add_section(lines, "长期目标", [avatar.long_term_objective.content])
    if avatar.short_term_objective:
        add_section(lines, "短期目标", [avatar.short_term_objective])

    # 兵器（必有，使用颜色标记等级）
    if avatar.weapon is not None:
        weapon_text = avatar.weapon.get_colored_info()
        if avatar.weapon.desc:
            weapon_text += f"（{avatar.weapon.desc}）"
        add_kv(lines, "兵器", weapon_text)
    
    # 辅助装备（可选，使用颜色标记等级）
    if avatar.auxiliary is not None:
        auxiliary_text = avatar.auxiliary.get_colored_info()
        if avatar.auxiliary.desc:
            auxiliary_text += f"（{avatar.auxiliary.desc}）"
        add_kv(lines, "辅助装备", auxiliary_text)
    else:
        add_kv(lines, "辅助装备", "无")

    # 灵兽：仅在存在时显示
    if avatar.spirit_animal is not None:
        add_kv(lines, "灵兽", avatar.spirit_animal.get_info())

    # 关系（从自身视角分组展示）
    from src.classes.relation import get_relations_strs
    relation_lines = get_relations_strs(avatar, max_lines=15)
    if relation_lines:
        add_section(lines, "关系", [f"  {s}" for s in relation_lines])
    else:
        add_kv(lines, "关系", "无")

    return lines


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
    info = get_avatar_info(avatar, detailed=detailed)

    observed: list[str] = []
    if co_region_avatars:
        for other in co_region_avatars[:8]:
            observed.append(f"{other.name}，境界：{other.cultivation_progress.get_info()}")

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

    info["周围角色"] = observed
    info["重大事件"] = major_list
    info["短期事件"] = minor_list
    info["长期目标"] = avatar.long_term_objective.content if avatar.long_term_objective else "无"
    return info


def get_other_avatar_info(from_avatar: "Avatar", to_avatar: "Avatar") -> str:
    """
    仅显示几个字段：名字、绰号、境界、关系、宗门、阵营、外貌、功法、武器、辅助装备、HP
    """
    nickname = to_avatar.nickname.value if to_avatar.nickname else "无"
    sect = to_avatar.sect.name if to_avatar.sect else "散修"
    tech = to_avatar.technique.get_info() if to_avatar.technique else "无"
    weapon = to_avatar.weapon.get_info() if to_avatar.weapon else "无"
    aux = to_avatar.auxiliary.get_info() if to_avatar.auxiliary else "无"
    alignment = to_avatar.alignment
    
    # 关系可能为空
    relation = from_avatar.get_relation(to_avatar) or "无"

    return (
        f"{to_avatar.name}，绰号：{nickname}，境界：{to_avatar.cultivation_progress.get_info()}，"
        f"关系：{relation}，宗门：{sect}，阵营：{alignment}，"
        f"外貌：{to_avatar.appearance.get_info()}，功法：{tech}，兵器：{weapon}，辅助：{aux}，HP：{to_avatar.hp}"
    )


def get_avatar_desc(avatar: "Avatar", detailed: bool = False) -> str:
    """
    获取角色的文本描述。
    detailed=True 时包含详细的效果来源分析。
    """
    # 基础描述
    lines = [f"【{avatar.name}】 {avatar.gender} {avatar.age}岁"]
    lines.append(f"境界: {avatar.cultivation_progress.get_info()}")
    if avatar.sect:
        lines.append(f"身份: {avatar.get_sect_str()}")
    
    if detailed:
        lines.append("\n--- 当前效果明细 ---")
        breakdown = avatar.get_effect_breakdown()
        
        from src.utils.effect_desc import format_effects_to_text
        
        if not breakdown:
            lines.append("无额外效果")
        else:
            for source_name, effects in breakdown:
                # 使用现有的 format_effects_to_text 将字典转为中文描述
                desc_str = format_effects_to_text(effects)
                if desc_str:
                    lines.append(f"[{source_name}]: {desc_str}")
                
    return "\n".join(lines)
