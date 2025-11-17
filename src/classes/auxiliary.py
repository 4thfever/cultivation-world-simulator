from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Dict

from src.utils.df import game_configs
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

    for _, row in df.iterrows():
        raw_sect = row.get("sect_id")
        sect_id: Optional[int] = None
        if raw_sect is not None and str(raw_sect).strip() and str(raw_sect).strip() != "nan":
            sect_id = int(float(raw_sect))

        raw_effects_val = row.get("effects", "")
        effects = load_effect_from_str(raw_effects_val)

        sect_obj: Optional[Sect] = sects_by_id.get(int(sect_id)) if sect_id is not None else None

        # 解析grade
        grade_str = str(row.get("grade", "普通"))
        grade = EquipmentGrade.COMMON
        for g in EquipmentGrade:
            if g.value == grade_str:
                grade = g
                break

        a = Auxiliary(
            id=int(row["id"]),
            name=str(row["name"]),
            grade=grade,
            sect_id=sect_id,
            desc=str(row.get("desc", "")),
            effects=effects,
            sect=sect_obj,
        )

        auxiliaries_by_id[a.id] = a
        auxiliaries_by_name[a.name] = a
        if a.sect_id is not None and a.sect_id not in auxiliaries_by_sect_id:
            auxiliaries_by_sect_id[a.sect_id] = a

    return auxiliaries_by_id, auxiliaries_by_name, auxiliaries_by_sect_id


auxiliaries_by_id, auxiliaries_by_name, auxiliaries_by_sect_id = _load_auxiliaries()

