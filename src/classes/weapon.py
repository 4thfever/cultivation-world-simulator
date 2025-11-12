from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Dict

from src.utils.df import game_configs
from src.classes.effect import load_effect_from_str
from src.classes.equipment_grade import EquipmentGrade
from src.classes.weapon_type import WeaponType
from src.classes.sect import Sect, sects_by_id


@dataclass
class Weapon:
    """
    兵器类：用于战斗的装备
    字段与 static/game_configs/weapon.csv 对应：
    - weapon_type: 兵器类型（剑、刀、枪等）
    - grade: 装备等级（普通、宝物、法宝）
    - sect_id: 对应宗门ID（见 sect.csv）；允许为空表示无特定宗门归属
    - effects: 解析为 dict，用于与 Avatar.effects 合并
    """
    id: int
    name: str
    weapon_type: WeaponType
    grade: EquipmentGrade
    sect_id: Optional[int]
    desc: str
    effects: dict[str, object] = field(default_factory=dict)
    sect: Optional[Sect] = None
    # 特殊属性（如万魂幡的吞噬魂魄计数）
    special_data: dict = field(default_factory=dict)

    def get_info(self) -> str:
        """获取简略信息"""
        suffix = ""
        # 万魂幡特殊显示
        if self.name == "万魂幡" and self.special_data.get("devoured_souls", 0) > 0:
            suffix = f"（吞噬魂魄：{self.special_data['devoured_souls']}）"
        return f"{self.name}{suffix}"

    def get_detailed_info(self) -> str:
        """获取详细信息"""
        souls = ""
        if self.name == "万魂幡" and self.special_data.get("devoured_souls", 0) > 0:
            souls = f" 吞噬魂魄：{self.special_data['devoured_souls']}"
        return f"{self.name}（{self.weapon_type}·{self.grade}，{self.desc}）{souls}"


def _load_weapons() -> tuple[Dict[int, Weapon], Dict[str, Weapon], Dict[int, Weapon]]:
    """从配表加载 weapon 数据。
    返回：(按ID、按名称、按宗门ID 的映射)。
    若同一宗门配置多个兵器，按首次出现保留（每门至多一个法宝级）。
    """
    weapons_by_id: Dict[int, Weapon] = {}
    weapons_by_name: Dict[str, Weapon] = {}
    weapons_by_sect_id: Dict[int, Weapon] = {}

    df = game_configs.get("weapon")
    if df is None:
        return weapons_by_id, weapons_by_name, weapons_by_sect_id

    for _, row in df.iterrows():
        raw_sect = row.get("sect_id")
        sect_id: Optional[int] = None
        if raw_sect is not None and str(raw_sect).strip() and str(raw_sect).strip() != "nan":
            sect_id = int(float(raw_sect))

        raw_effects_val = row.get("effects", "")
        effects = load_effect_from_str(raw_effects_val)

        sect_obj: Optional[Sect] = sects_by_id.get(int(sect_id)) if sect_id is not None else None

        # 解析weapon_type
        weapon_type_str = str(row.get("weapon_type", ""))
        weapon_type = None
        for wt in WeaponType:
            if wt.value == weapon_type_str:
                weapon_type = wt
                break
        
        if weapon_type is None:
            raise ValueError(f"武器 {row['name']} 的weapon_type '{weapon_type_str}' 无效，必须是有效的兵器类型")

        # 解析grade
        grade_str = str(row.get("grade", "普通"))
        grade = EquipmentGrade.COMMON
        for g in EquipmentGrade:
            if g.value == grade_str:
                grade = g
                break

        w = Weapon(
            id=int(row["id"]),
            name=str(row["name"]),
            weapon_type=weapon_type,
            grade=grade,
            sect_id=sect_id,
            desc=str(row.get("desc", "")),
            effects=effects,
            sect=sect_obj,
        )

        weapons_by_id[w.id] = w
        weapons_by_name[w.name] = w
        if w.sect_id is not None and w.sect_id not in weapons_by_sect_id:
            weapons_by_sect_id[w.sect_id] = w

    return weapons_by_id, weapons_by_name, weapons_by_sect_id


weapons_by_id, weapons_by_name, weapons_by_sect_id = _load_weapons()


def get_common_weapon(weapon_type: WeaponType) -> Optional[Weapon]:
    """获取指定类型的普通兵器（用于兜底）"""
    weapon_name = f"普通{weapon_type.value}"
    return weapons_by_name.get(weapon_name)

