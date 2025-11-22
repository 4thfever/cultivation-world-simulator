from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Dict

from src.utils.df import game_configs, get_str, get_int
from src.classes.effect import load_effect_from_str
from src.classes.equipment_grade import EquipmentGrade
from src.classes.sect import Sect, sects_by_id


@dataclass
class Auxiliary:
    """
    辅助装备类：提供各种辅助功能的装备
    字段与 static/game_configs/auxiliary.csv 对应：
    - grade: 装备等级（普通、宝物、法宝）
    - sect_id: 对应宗门ID（见 sect.csv）；允许为空表示无特定宗门归属
    - effects: 解析为 dict，用于与 Avatar.effects 合并
    """
    id: int
    name: str
    grade: EquipmentGrade
    sect_id: Optional[int]
    desc: str
    effects: dict[str, object] = field(default_factory=dict)
    sect: Optional[Sect] = None
    # 特殊属性（用于存储实例特定数据）
    special_data: dict = field(default_factory=dict)

    def get_info(self) -> str:
        """获取简略信息"""
        return f"{self.name}"

    def get_detailed_info(self) -> str:
        """获取详细信息"""
        return f"{self.name}（{self.grade}，{self.desc}）"
    
    def get_colored_info(self) -> str:
        """获取带颜色标记的信息，供前端渲染使用"""
        r, g, b = self.grade.color_rgb
        return f"<color:{r},{g},{b}>{self.get_info()}</color>"

    def get_structured_info(self) -> dict:
        from src.utils.effect_desc import format_effects_to_text
        return {
            "name": self.name,
            "desc": self.desc,
            "grade": self.grade.value,
            "color": self.grade.color_rgb,
            "effect_desc": format_effects_to_text(self.effects),
        }


def _load_auxiliaries() -> tuple[Dict[int, Auxiliary], Dict[str, Auxiliary], Dict[int, Auxiliary]]:
    """从配表加载 auxiliary 数据。
    返回：(按ID、按名称、按宗门ID 的映射)。
    若同一宗门配置多个辅助装备，按首次出现保留（每门至多一个法宝级）。
    """
    auxiliaries_by_id: Dict[int, Auxiliary] = {}
    auxiliaries_by_name: Dict[str, Auxiliary] = {}
    auxiliaries_by_sect_id: Dict[int, Auxiliary] = {}

    df = game_configs.get("auxiliary")
    if df is None:
        return auxiliaries_by_id, auxiliaries_by_name, auxiliaries_by_sect_id

    for row in df:
        sect_id = get_int(row, "sect_id", -1)
        if sect_id == -1:
            sect_id = None

        effects = load_effect_from_str(get_str(row, "effects"))

        sect_obj: Optional[Sect] = sects_by_id.get(sect_id) if sect_id is not None else None

        # 解析grade
        grade_str = get_str(row, "grade", "普通")
        grade = EquipmentGrade.COMMON
        for g in EquipmentGrade:
            if g.value == grade_str:
                grade = g
                break

        a = Auxiliary(
            id=get_int(row, "id"),
            name=get_str(row, "name"),
            grade=grade,
            sect_id=sect_id,
            desc=get_str(row, "desc"),
            effects=effects,
            sect=sect_obj,
        )

        auxiliaries_by_id[a.id] = a
        auxiliaries_by_name[a.name] = a
        if a.sect_id is not None and a.sect_id not in auxiliaries_by_sect_id:
            auxiliaries_by_sect_id[a.sect_id] = a

    return auxiliaries_by_id, auxiliaries_by_name, auxiliaries_by_sect_id


auxiliaries_by_id, auxiliaries_by_name, auxiliaries_by_sect_id = _load_auxiliaries()
