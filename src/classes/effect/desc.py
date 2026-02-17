from typing import Any
import re


def get_effect_desc(effect_key: str) -> str:
    """获取 effect 的描述名称（支持国际化）"""
    from src.i18n import t
    
    # 映射 effect_key -> msgid
    msgid_map = {
        "extra_hp_recovery_rate": "effect_extra_hp_recovery_rate",
        "extra_max_hp": "effect_extra_max_hp",
        "extra_max_lifespan": "effect_extra_max_lifespan",
        "extra_weapon_proficiency_gain": "effect_extra_weapon_proficiency_gain",
        "extra_dual_cultivation_exp": "effect_extra_dual_cultivation_exp",
        "extra_breakthrough_success_rate": "effect_extra_breakthrough_success_rate",
        "extra_retreat_success_rate": "effect_extra_retreat_success_rate",
        "extra_fortune_probability": "effect_extra_fortune_probability",
        "extra_misfortune_probability": "effect_extra_misfortune_probability",
        "extra_harvest_materials": "effect_extra_harvest_materials",
        "extra_hunt_materials": "effect_extra_hunt_materials",
        "extra_mine_materials": "effect_extra_mine_materials",
        "extra_item_sell_price_multiplier": "effect_extra_item_sell_price_multiplier",
        "shop_buy_price_reduction": "effect_shop_buy_price_reduction",
        "extra_weapon_upgrade_chance": "effect_extra_weapon_upgrade_chance",
        "extra_plunder_multiplier": "effect_extra_plunder_multiplier",
        "extra_catch_success_rate": "effect_extra_catch_success_rate",
        "extra_respire_exp": "effect_extra_respire_exp",
        "extra_respire_exp_multiplier": "effect_extra_respire_exp_multiplier",
        "extra_battle_strength_points": "effect_extra_battle_strength_points",
        "extra_escape_success_rate": "effect_extra_escape_success_rate",
        "extra_assassinate_success_rate": "effect_extra_assassinate_success_rate",
        "extra_observation_radius": "effect_extra_observation_radius",
        "extra_move_step": "effect_extra_move_step",
        "legal_actions": "effect_legal_actions",
        "damage_reduction": "effect_damage_reduction",
        "realm_suppression_bonus": "effect_realm_suppression_bonus",
        "respire_duration_reduction": "effect_respire_duration_reduction",
        "temper_duration_reduction": "effect_temper_duration_reduction",
        "extra_cast_success_rate": "effect_extra_cast_success_rate",
        "extra_refine_success_rate": "effect_extra_refine_success_rate",
        "extra_hidden_domain_drop_prob": "effect_extra_hidden_domain_drop_prob",
        "extra_hidden_domain_danger_prob": "effect_extra_hidden_domain_danger_prob",
        "extra_epiphany_probability": "effect_extra_epiphany_probability",
        "extra_educate_efficiency": "effect_extra_educate_efficiency",
        "extra_educate_prosperity_prob": "effect_extra_educate_prosperity_prob",
        "extra_temper_exp_multiplier": "effect_extra_temper_exp_multiplier",
    }
    
    msgid = msgid_map.get(effect_key, effect_key)
    return t(msgid)


def get_action_short_name(action_name: str) -> str:
    """获取 action 的简短名称（复用 Action 系统翻译）"""
    from src.i18n import t
    
    # 使用统一的命名规则
    msgid = f"action_{action_name.lower()}_short_name"
    return t(msgid)

def format_value(key: str, value: Any) -> str:
    """
    格式化效果数值
    """
    if key == "legal_actions" and isinstance(value, list):
        from src.i18n import t
        actions = [get_action_short_name(str(a)) for a in value]
        sep = t("action_list_separator")  # "、" 或 ", "
        return sep.join(actions)

    if isinstance(value, (int, float)):
        # 处理百分比类型的字段
        if "rate" in key or "probability" in key or "chance" in key or "multiplier" in key or "gain" in key or "reduction" in key or "bonus" in key:
            # 如果是小数，转为百分比。通常 0.1 表示 +10%
            # 但有些可能是直接的倍率？代码里 1.0 + value，所以 value 是增量
            if isinstance(value, float):
                percent = value * 100
                sign = "+" if percent > 0 else ""
                return f"{sign}{percent:.1f}%"
        
        # 处理数值类型的字段
        sign = "+" if value > 0 else ""
        return f"{sign}{value}"
    
    return str(value)

def translate_condition(condition: str) -> str:
    """
    将代码形式的条件表达式转换为易读描述
    """
    from src.i18n import t
    import re

    if not condition:
        return t("Conditional effect")

    # 1. 处理 Persona 判断 (特质)
    # 模式: any(p.key == "CHILD_OF_FORTUNE" for p in avatar.personas)
    if "avatar.personas" in condition:
        # 优先匹配 key
        m_key = re.search(r'p\.key\s*==\s*["\'](.*?)["\']', condition)
        if m_key:
            key = m_key.group(1)
            # 尝试从全局数据中查找对应的 Persona Name
            from src.classes.persona import personas_by_id
            trait_name = key # 默认显示key，如果找到则显示name
            for p in personas_by_id.values():
                if p.key == key:
                    trait_name = p.name
                    break
            return t("Has [{trait}] trait", trait=trait_name)
        
        # 兼容旧的 name 匹配
        m_name = re.search(r'p\.name\s*==\s*["\'](.*?)["\']', condition)
        if m_name:
            return t("Has [{trait}] trait", trait=m_name.group(1))

    # 2. 处理 Alignment 判断 (阵营)
    # 模式: avatar.alignment == Alignment.RIGHTEOUS
    if "avatar.alignment" in condition:
        m_align = re.search(r'Alignment\.([A-Z_]+)', condition)
        if m_align:
            align_key = m_align.group(1)
            from src.classes.alignment import Alignment
            try:
                # 获取枚举并调用 str() 进行翻译
                align_enum = Alignment[align_key]
                return t("When alignment is {align}", align=str(align_enum))
            except KeyError:
                pass

    # 3. 处理 WeaponType 判断 (兵器类型)
    # 模式: avatar.weapon.type == WeaponType.SWORD
    if "avatar.weapon.type" in condition:
        m_weapon = re.search(r'WeaponType\.([A-Z_]+)', condition)
        if m_weapon:
            w_key = m_weapon.group(1)
            from src.classes.weapon_type import WeaponType
            try:
                w_enum = WeaponType[w_key]
                return t("When using {weapon_type}", weapon_type=str(w_enum))
            except KeyError:
                pass

    # 4. 兜底简化
    # 移除代码前缀和符号，使未识别的条件稍微可读一些
    simple_cond = condition
    simple_cond = simple_cond.replace("avatar.", "")
    simple_cond = simple_cond.replace("Alignment.", "")
    simple_cond = simple_cond.replace("WeaponType.", "")
    simple_cond = simple_cond.replace("==", ":")
    
    return t("When {condition}", condition=simple_cond)

def format_effects_to_text(effects: dict[str, Any] | list[dict[str, Any]]) -> str:
    """
    将 effects 字典转换为易读的文本描述。
    例如：{"extra_max_hp": 100} -> "最大生命值 +100" / "Max HP +100"
    """
    from src.i18n import t
    
    if not effects:
        return ""
        
    if isinstance(effects, list):
        parts = []
        for eff in effects:
            text = format_effects_to_text(eff)
            if text:
                parts.append(text)
        return "\n".join(parts)
    
    # 1. 优先检查是否有自定义的整体描述覆盖
    if "_desc" in effects:
        return t(effects["_desc"])

    desc_list = []
    for k, v in effects.items():
        if k in ["when", "duration_month", "when_desc"]:
            continue
            
        # 使用翻译函数获取名称
        name = get_effect_desc(k)
        
        # 如果是 eval 表达式（字符串形式）或者看起来像代码
        if isinstance(v, str):
            if v.startswith("eval(") or "avatar." in v or "//" in v:
                val_str = t("Special effect (dynamic)")
            else:
                val_str = format_value(k, v)
        else:
            val_str = format_value(k, v)
            
        desc_list.append(f"{name} {val_str}")
    
    # 使用翻译的分隔符
    sep = t("effect_separator")
    text = sep.join(desc_list)
    
    # 如果有条件，添加条件描述
    if effects.get("when"):
        if "when_desc" in effects:
            cond = t(effects["when_desc"])
        else:
            cond = translate_condition(str(effects["when"]))
        return f"[{cond}] {text}"
        
    return text

