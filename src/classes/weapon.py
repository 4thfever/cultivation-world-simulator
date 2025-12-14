from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Dict

from src.utils.df import game_configs, get_str, get_int
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
    effect_desc: str = ""
    sect: Optional[Sect] = None
    # 特殊属性（如万魂幡的吞噬魂魄计数）
    special_data: dict = field(default_factory=dict)

    def __deepcopy__(self, memo):
        """
        自定义深拷贝：
        Sect 对象必须保持单例引用，不能深拷贝，否则会复制整个宗门及其所有成员，
        导致内存浪费和潜在的无限递归/哈希错误。
        """
        import copy
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        
        for k, v in self.__dict__.items():
            if k == 'sect':
                # 浅拷贝引用
                setattr(result, k, v)
            else:
                # 深拷贝其他属性
                setattr(result, k, copy.deepcopy(v, memo))
        return result

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
        
        effect_part = f" 效果：{self.effect_desc}" if self.effect_desc else ""
        return f"{self.name}（{self.weapon_type}·{self.grade}，{self.desc}{souls}）{effect_part}"
    
    def get_colored_info(self) -> str:
        """获取带颜色标记的信息，供前端渲染使用"""
        r, g, b = self.grade.color_rgb
        return f"<color:{r},{g},{b}>{self.get_info()}</color>"

    def get_structured_info(self) -> dict:
        
        # 基础描述
        full_desc = self.desc
        
        # 特殊数据处理
        souls = 0
        if self.name == "万魂幡":
            souls = self.special_data.get("devoured_souls", 0)
            if souls > 0:
                full_desc = f"{full_desc} (已吞噬魂魄：{souls})"
        
        return {
            "name": self.name,
            "desc": full_desc,
            "grade": self.grade.value,
            "color": self.grade.color_rgb,
            "type": self.weapon_type.value,
            "effect_desc": self.effect_desc,
        }


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

    for row in df:
        sect_id = get_int(row, "sect_id", -1)
        if sect_id == -1:
            sect_id = None

        effects = load_effect_from_str(get_str(row, "effects"))
        from src.utils.effect_desc import format_effects_to_text
        effect_desc = format_effects_to_text(effects)

        sect_obj: Optional[Sect] = sects_by_id.get(sect_id) if sect_id is not None else None

        # 解析weapon_type
        weapon_type_str = get_str(row, "weapon_type")
        weapon_type = None
        for wt in WeaponType:
            if wt.value == weapon_type_str:
                weapon_type = wt
                break
        
        if weapon_type is None:
            # 如果找不到对应类型，可以决定是跳过还是抛错
            # 这里保持原有逻辑，如果是空或者非法，抛错提示配置问题
            raise ValueError(f"武器 {get_str(row, 'name')} 的weapon_type '{weapon_type_str}' 无效，必须是有效的兵器类型")

        # 解析grade
        grade_str = get_str(row, "grade", "普通")
        grade = EquipmentGrade.COMMON
        for g in EquipmentGrade:
            if g.value == grade_str:
                grade = g
                break

        w = Weapon(
            id=get_int(row, "id"),
            name=get_str(row, "name"),
            weapon_type=weapon_type,
            grade=grade,
            sect_id=sect_id,
            desc=get_str(row, "desc"),
            effects=effects,
            effect_desc=effect_desc,
            sect=sect_obj,
        )

        weapons_by_id[w.id] = w
        weapons_by_name[w.name] = w
        if w.sect_id is not None and w.sect_id not in weapons_by_sect_id:
            weapons_by_sect_id[w.sect_id] = w

    return weapons_by_id, weapons_by_name, weapons_by_sect_id


weapons_by_id, weapons_by_name, weapons_by_sect_id = _load_weapons()


def get_common_weapon(weapon_type: WeaponType) -> Optional[Weapon]:
    """获取指定类型的凡品兵器（用于兜底）"""
    weapon_name = f"凡品{weapon_type.value}"
    return weapons_by_name.get(weapon_name)


def get_treasure_weapon(weapon_type: WeaponType) -> Optional[Weapon]:
    """获取指定类型的宝物级兵器"""
    from src.classes.equipment_grade import EquipmentGrade
    for weapon in weapons_by_id.values():
        if weapon.weapon_type == weapon_type and weapon.grade == EquipmentGrade.TREASURE:
            return weapon
    return None
