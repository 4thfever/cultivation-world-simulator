from __future__ import annotations

import copy
import random
from dataclasses import dataclass, field
from typing import Optional, Dict

from src.utils.df import game_configs, get_str, get_int
from src.classes.effect import load_effect_from_str
from src.classes.cultivation import Realm
from src.classes.weapon_type import WeaponType


@dataclass
class Weapon:
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

    def get_info(self, detailed: bool = False) -> str:
        """获取信息"""
        if detailed:
            return self.get_detailed_info()
        return f"{self.name}"

    def get_detailed_info(self) -> str:
        """获取详细信息"""
        effect_part = f" 效果：{self.effect_desc}" if self.effect_desc else ""
        return f"{self.name}（{self.weapon_type}·{self.realm.value}，{self.desc}）{effect_part}"
    
    def get_colored_info(self) -> str:
        """获取带颜色标记的信息，供前端渲染使用"""
        r, g, b = self.realm.color_rgb
        return f"<color:{r},{g},{b}>{self.get_info()}</color>"

    def get_structured_info(self) -> dict:
        return {
            "name": self.name,
            "desc": self.desc,
            "grade": self.realm.value,
            "color": self.realm.color_rgb,
            "type": self.weapon_type.value,
            "effect_desc": self.effect_desc,
        }


def _load_weapons() -> tuple[Dict[int, Weapon], Dict[str, Weapon]]:
    """从配表加载 weapon 数据。
    返回：(按ID、按名称 的映射)。
    """
    weapons_by_id: Dict[int, Weapon] = {}
    weapons_by_name: Dict[str, Weapon] = {}

    df = game_configs.get("weapon")
    if df is None:
        return weapons_by_id, weapons_by_name

    for row in df:
        effects = load_effect_from_str(get_str(row, "effects"))
        from src.utils.effect_desc import format_effects_to_text
        effect_desc = format_effects_to_text(effects)

        # 解析weapon_type
        weapon_type_str = get_str(row, "weapon_type")
        weapon_type = None
        for wt in WeaponType:
            if wt.value == weapon_type_str:
                weapon_type = wt
                break
        
        if weapon_type is None:
            raise ValueError(f"武器 {get_str(row, 'name')} 的weapon_type '{weapon_type_str}' 无效，必须是有效的兵器类型")

        # 解析grade
        grade_str = get_str(row, "grade", "练气")
        try:
            realm = next(r for r in Realm if r.value == grade_str)
        except StopIteration:
            realm = Realm.Qi_Refinement

        w = Weapon(
            id=get_int(row, "id"),
            name=get_str(row, "name"),
            weapon_type=weapon_type,
            realm=realm,
            desc=get_str(row, "desc"),
            effects=effects,
            effect_desc=effect_desc,
        )

        weapons_by_id[w.id] = w
        weapons_by_name[w.name] = w

    return weapons_by_id, weapons_by_name


weapons_by_id, weapons_by_name = _load_weapons()


def get_random_weapon_by_realm(realm: Realm, weapon_type: Optional[WeaponType] = None) -> Optional[Weapon]:
    """获取指定境界（及可选类型）的随机兵器"""
    candidates = [w for w in weapons_by_id.values() if w.realm == realm]
    if weapon_type is not None:
        candidates = [w for w in candidates if w.weapon_type == weapon_type]
        
    if not candidates:
        return None
    return copy.deepcopy(random.choice(candidates))
