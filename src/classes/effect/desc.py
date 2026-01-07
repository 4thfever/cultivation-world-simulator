from typing import Any
import re

EFFECT_DESC_MAP = {
    "extra_hp_recovery_rate": "生命恢复速率",
    "extra_max_hp": "最大生命值",
    "extra_max_lifespan": "最大寿元",
    "extra_weapon_proficiency_gain": "兵器熟练度获取",
    "extra_dual_cultivation_exp": "双修经验",
    "extra_breakthrough_success_rate": "突破成功率",
    "extra_fortune_probability": "奇遇概率",
    "extra_misfortune_probability": "霉运概率",
    "extra_harvest_items": "采集获取物品",
    "extra_hunt_items": "狩猎获取物品",
    "extra_item_sell_price_multiplier": "物品出售价格",
    "shop_buy_price_reduction": "购买折扣",
    "extra_weapon_upgrade_chance": "兵器升级概率",
    "extra_plunder_multiplier": "搜刮收益",
    "extra_catch_success_rate": "捕捉灵兽成功率",
    "extra_cultivate_exp": "修炼经验",
    "extra_battle_strength_points": "战力点数",
    "extra_escape_success_rate": "逃跑成功率",
    "extra_assassinate_success_rate": "暗杀成功率",
    "extra_observation_radius": "感知范围",
    "extra_move_step": "移动步长",
    "legal_actions": "特殊能力",
    "damage_reduction": "伤害减免",
    "realm_suppression_bonus": "境界压制",
    "cultivate_duration_reduction": "修炼时长缩减",
    "extra_cast_success_rate": "铸造成功率",
    "extra_refine_success_rate": "炼丹成功率",
}

ACTION_DESC_MAP = {
    "DualCultivation": "双修",
    "DevourMortals": "吞噬凡人",
}

def format_value(key: str, value: Any) -> str:
    """
    格式化效果数值
    """
    if key == "legal_actions" and isinstance(value, list):
        actions = [ACTION_DESC_MAP.get(str(a), str(a)) for a in value]
        return "、".join(actions)

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
    将代码形式的条件表达式转换为易读的中文描述。
    """
    if not condition:
        return "条件触发"
        
    # 特殊复杂模式：any(p.name == "xxx" for p in avatar.personas)
    if "avatar.personas" in condition and "any" in condition:
        m = re.search(r'p\.name\s*==\s*["\'](.*?)["\']', condition)
        if m:
            return f"拥有【{m.group(1)}】特质"

    s = condition
    
    # 1. 变量映射
    vars_map = {
        "avatar.weapon.type": "武器类型",
        "avatar.weapon.weapon_type.value": "武器类型",
        "avatar.weapon.proficiency": "兵器熟练度",
        "avatar.weapon": "兵器",
        "avatar.cultivation_progress.realm.value": "境界等级",
        "avatar.cultivation_progress.level": "修为等级",
        "avatar.alignment": "立场",
        "avatar.age": "年龄",
        "avatar.spirit_animal": "灵兽",
        "avatar.sect": "宗门",
        "avatar.auxiliary": "辅助装备",
    }
    
    # 2. 枚举值映射
    enums_map = {
        "WeaponType.SWORD": "剑",
        "WeaponType.SABER": "刀",
        "WeaponType.SPEAR": "枪",
        "WeaponType.STAFF": "棍",
        "WeaponType.FAN": "扇",
        "WeaponType.WHIP": "鞭",
        "WeaponType.ZITHER": "琴",
        "WeaponType.FLUTE": "笛",
        "WeaponType.HIDDEN_WEAPON": "暗器",
        
        "Alignment.RIGHTEOUS": "正道",
        "Alignment.GOOD": "正道", 
        "Alignment.EVIL": "魔道",
        "Alignment.NEUTRAL": "中立",
    }
    
    # 执行变量和枚举替换
    for k, v in vars_map.items():
        s = s.replace(k, v)
        
    for k, v in enums_map.items():
        s = s.replace(k, v)

    # 3. 特殊语法处理 (is not None, is None)
    # 必须在变量替换之后，普通运算符替换之前
    if " is not None" in s:
        s = re.sub(r'([^\s]+)\s+is\s+not\s+None', r'拥有\1', s)
    if " is None" in s:
        s = re.sub(r'([^\s]+)\s+is\s+None', r'未拥有\1', s)
    
    # 4. 运算符映射
    ops_map = {
        "==": "为",
        "!=": "非",
        ">=": "≥",
        "<=": "≤",
        ">": "＞",
        "<": "＜",
        " and ": " 且 ",
        " or ": " 或 ",
        " in ": " 属于 ",
        " not ": "非",
    }

    for k, v in ops_map.items():
        s = s.replace(k, v)

    # 清理符号
    s = s.replace('"', '').replace("'", "")
    s = s.replace('[', '【').replace(']', '】')
    
    return f"当{s.strip()}"

def format_effects_to_text(effects: dict[str, Any] | list[dict[str, Any]]) -> str:
    """
    将 effects 字典转换为易读的文本描述。
    例如：{"extra_max_hp": 100} -> "最大生命值 +100"
    """
    if not effects:
        return ""
        
    if isinstance(effects, list):
        parts = []
        for eff in effects:
            text = format_effects_to_text(eff)
            if text:
                parts.append(text)
        return "\n".join(parts)
    
    desc_list = []
    for k, v in effects.items():
        if k == "when":
            continue
            
        # 跳过 eval 表达式或者无法解析的 key，或者直接显示 key
        name = EFFECT_DESC_MAP.get(k, k)
        
        # 如果是 eval 表达式（字符串形式）或者看起来像代码
        if isinstance(v, str):
            if v.startswith("eval(") or "avatar." in v or "//" in v:
                # 尝试提取简单的描述，或者显示"特殊效果"
                val_str = "特殊效果（动态）"
            else:
                val_str = format_value(k, v)
        else:
            val_str = format_value(k, v)
            
        desc_list.append(f"{name} {val_str}")
    
    text = "；".join(desc_list)
    
    # 如果有条件，添加条件描述
    if effects.get("when"):
        cond = translate_condition(str(effects["when"]))
        return f"[{cond}] {text}"
        
    return text

