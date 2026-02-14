from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional, Dict

from src.utils.df import game_configs, get_str, get_int
from src.classes.effect import load_effect_from_str
from src.systems.cultivation import Realm
from src.classes.weapon_type import WeaponType
from src.classes.items.item import Item


@dataclass
class Weapon(Item):
    """
    兵器类：用于战斗的装备
    字段与 static/game_configs/weapon.csv 对应：
    - weapon_type: 兵器类型（剑、刀、枪等）
    - realm: 装备等级（练气/筑基/金丹/元婴）
    - effects: 解析为 dict，用于与 Avatar.effects 合并
    """
    id: int
    name: str
    weapon_type: WeaponType
    realm: Realm
    desc: str
    effects: dict[str, object] = field(default_factory=dict)
    effect_desc: str = ""
    # 特殊属性（如万魂幡的吞噬魂魄计数）
    special_data: dict = field(default_factory=dict)

    def __hash__(self):
        return hash(self.id)

    def get_info(self, detailed: bool = False) -> str:
        """获取信息"""
        if detailed:
            return self.get_detailed_info()
        return f"{self.name}"

    def get_detailed_info(self) -> str:
        """获取详细信息"""
        from src.i18n import t
        effect_part = t(" Effect: {effect_desc}", effect_desc=self.effect_desc) if self.effect_desc else ""
        return f"[{self.id}] " + t("{name} ({type}·{realm}, {desc}){effect}",
                 name=self.name, type=str(self.weapon_type), realm=str(self.realm), 
                 desc=self.desc, effect=effect_part)
    
    def get_colored_info(self) -> str:
        """获取带颜色标记的信息，供前端渲染使用"""
        r, g, b = self.realm.color_rgb
        return f"<color:{r},{g},{b}>{self.get_info()}</color>"

    def get_structured_info(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "desc": self.desc,
            "grade": str(self.realm),
            "color": self.realm.color_rgb,
            "type": self.weapon_type.value,
            "effect_desc": self.effect_desc,
        }


def _load_weapons_data() -> tuple[Dict[int, Weapon], Dict[str, Weapon]]:
    """从配表加载 weapon 数据。
    返回：新的 (按ID、按名称 的映射)。
    """
    new_by_id: Dict[int, Weapon] = {}
    new_by_name: Dict[str, Weapon] = {}

    df = game_configs.get("weapon")
    if df is None:
        return new_by_id, new_by_name

    for row in df:
        effects = load_effect_from_str(get_str(row, "effects"))
        from src.classes.effect import format_effects_to_text
        effect_desc = format_effects_to_text(effects)

        # 解析weapon_type
        weapon_type_str = get_str(row, "weapon_type")
        weapon_type = WeaponType.from_str(weapon_type_str)
        
        # 解析grade
        grade_str = get_str(row, "grade", "QI_REFINEMENT")
        realm = Realm.from_str(grade_str)

        w = Weapon(
            id=get_int(row, "item_id"),
            name=get_str(row, "name"),
            weapon_type=weapon_type,
            realm=realm,
            desc=get_str(row, "desc"),
            effects=effects,
            effect_desc=effect_desc,
        )

        new_by_id[w.id] = w
        new_by_name[w.name] = w
        
        # 注册到全局注册表 (注意：ItemRegistry 在外部 reset 之后，这里会重新注册)
        from src.classes.items.registry import ItemRegistry
        ItemRegistry.register(w.id, w)

    return new_by_id, new_by_name

# 全局容器
weapons_by_id: Dict[int, Weapon] = {}
weapons_by_name: Dict[str, Weapon] = {}

def reload():
    """重新加载数据，保留全局字典引用"""
    new_id, new_name = _load_weapons_data()
    
    weapons_by_id.clear()
    weapons_by_id.update(new_id)
    
    weapons_by_name.clear()
    weapons_by_name.update(new_name)

# 模块初始化时执行一次
reload()


def get_random_weapon_by_realm(realm: Realm, weapon_type: Optional[WeaponType] = None) -> Optional[Weapon]:
    """获取指定境界（及可选类型）的随机兵器"""
    candidates = [w for w in weapons_by_id.values() if w.realm == realm]
    if weapon_type is not None:
        candidates = [w for w in candidates if w.weapon_type == weapon_type]
        
    if not candidates:
        return None
    return random.choice(candidates).instantiate()
