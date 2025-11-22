from typing import Any

EFFECT_DESC_MAP = {
    "extra_hp_recovery_rate": "生命恢复速率",
    "extra_max_hp": "最大生命值",
    "extra_max_mp": "最大灵力值",
    "extra_max_lifespan": "最大寿元",
    "extra_weapon_proficiency_gain": "兵器熟练度获取",
    "extra_dual_cultivation_exp": "双修经验",
    "extra_breakthrough_success_rate": "突破成功率",
    "extra_fortune_probability": "奇遇概率",
    "extra_harvest_items": "采集获取物品",
    "extra_hunt_items": "狩猎获取物品",
    "extra_item_sell_price_multiplier": "物品出售价格",
    "extra_weapon_upgrade_chance": "兵器升级概率",
    "extra_plunder_multiplier": "掠夺收益",
    "extra_catch_success_rate": "捕捉灵兽成功率",
    "extra_cultivate_exp": "修炼经验",
    "extra_battle_strength_points": "战力点数",
    "extra_escape_success_rate": "逃跑成功率",
    "extra_observation_radius": "感知范围",
    "extra_move_step": "移动步长",
}

def format_value(key: str, value: Any) -> str:
    """
    格式化效果数值
    """
    if isinstance(value, (int, float)):
        # 处理百分比类型的字段
        if "rate" in key or "probability" in key or "chance" in key or "multiplier" in key or "gain" in key:
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
                if eff.get("when"):
                    parts.append(f"[条件触发] {text}")
                else:
                    parts.append(text)
        return "\n".join(parts)
    
    desc_list = []
    for k, v in effects.items():
        if k == "when":
            continue
            
        # 跳过 eval 表达式或者无法解析的 key，或者直接显示 key
        name = EFFECT_DESC_MAP.get(k, k)
        
        # 如果是 eval 表达式（字符串形式）
        if isinstance(v, str) and v.startswith("eval("):
            # 尝试提取简单的描述，或者显示"特殊效果"
            val_str = "特殊效果"
        else:
            val_str = format_value(k, v)
            
        desc_list.append(f"{name} {val_str}")
        
    return "；".join(desc_list)

