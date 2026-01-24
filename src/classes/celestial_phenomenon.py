"""
天地灵机系统
=============

天地灵机是影响整个修仙世界的天象异动，提供全局性的buff/debuff。

特点：
- 不绑定任何角色，属于世界事件
- 定期变化（默认5年一次）
- 支持条件判断（如针对特定灵根、兵器类型等）
- 使用effect系统，与角色自身effects合并

扩展性：
- 未来可支持多天象并存（主天象+次天象）
- 未来可支持特殊事件触发天象变化（如飞升、大战等）
- 未来可支持地域性天象（只影响特定区域/宗门）
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional

from src.utils.df import game_configs, get_str, get_int
from src.classes.effect import load_effect_from_str
from src.classes.rarity import Rarity, get_rarity_from_str


@dataclass
class CelestialPhenomenon:
    """
    天地灵机（天象异动）
    
    字段与 static/game_configs/celestial_phenomenon.csv 对应：
    - id: 唯一标识符
    - name: 天象名称（修仙风格）
    - rarity: 稀有度（N/R/SR/SSR），决定显示颜色和出现概率
    - effects: JSON格式的效果配置，支持条件判断
    - desc: 天象描述文字（用于UI显示和事件生成）
    - duration_years: 持续年限（默认5年）
    """
    id: int
    name: str
    rarity: Rarity
    effects: dict[str, object]
    effect_desc: str
    desc: str
    duration_years: int
    
    @property
    def weight(self) -> float:
        """根据稀有度获取出现概率权重"""
        return self.rarity.weight
    
    def get_info(self) -> str:
        """获取简略信息"""
        return self.name
    
    def get_detailed_info(self) -> str:
        """获取详细信息"""
        from src.i18n import t
        effect_part = t(" Effect: {effect_desc}", effect_desc=self.effect_desc) if self.effect_desc else ""
        return t("{name} ({desc}{effect})", name=self.name, desc=self.desc, effect=effect_part)


def _load_celestial_phenomena() -> dict[int, CelestialPhenomenon]:
    """从配表加载天地灵机数据"""
    phenomena_by_id: dict[int, CelestialPhenomenon] = {}
    
    if "celestial_phenomenon" not in game_configs:
        return phenomena_by_id
    
    phenomenon_df = game_configs["celestial_phenomenon"]
    for row in phenomenon_df:
        # 解析稀有度
        rarity_str = get_str(row, "rarity", "N").upper()
        rarity = get_rarity_from_str(rarity_str) if rarity_str and rarity_str != "NAN" else get_rarity_from_str("N")
        
        # 解析effects
        effects = load_effect_from_str(get_str(row, "effects"))
        from src.classes.effect import format_effects_to_text
        effect_desc = format_effects_to_text(effects)
        
        phenomenon = CelestialPhenomenon(
            id=get_int(row, "id"),
            name=get_str(row, "name"),
            rarity=rarity,
            effects=effects,
            effect_desc=effect_desc,
            desc=get_str(row, "desc"),
            duration_years=get_int(row, "duration_years", 5),
        )
        phenomena_by_id[phenomenon.id] = phenomenon
    
    return phenomena_by_id


# 全局容器
celestial_phenomena_by_id: dict[int, CelestialPhenomenon] = {}

def reload():
    """重新加载数据，保留全局字典引用"""
    new_data = _load_celestial_phenomena()
    celestial_phenomena_by_id.clear()
    celestial_phenomena_by_id.update(new_data)

# 模块初始化时执行一次
reload()


def get_random_celestial_phenomenon() -> Optional[CelestialPhenomenon]:
    """
    按权重随机选择一个天地灵机
    
    Returns:
        CelestialPhenomenon 或 None（如果没有可用的天象）
    """
    if not celestial_phenomena_by_id:
        return None
    
    phenomena = list(celestial_phenomena_by_id.values())
    weights = [p.weight for p in phenomena]
    
    return random.choices(phenomena, weights=weights, k=1)[0]
