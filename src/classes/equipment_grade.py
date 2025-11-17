from enum import Enum
from src.classes.color import Color, EQUIPMENT_GRADE_COLORS


class EquipmentGrade(Enum):
    """
    装备等级枚举
    """
    COMMON = "普通"      # 无限复制，作为兜底
    TREASURE = "宝物"    # 可有多个，无数量限制
    ARTIFACT = "法宝"    # 全世界唯一
    
    def __str__(self) -> str:
        return self.value
    
    @property
    def color_rgb(self) -> tuple[int, int, int]:
        """返回装备等级对应的RGB颜色值"""
        color_map = {
            EquipmentGrade.COMMON: EQUIPMENT_GRADE_COLORS["COMMON"],
            EquipmentGrade.TREASURE: EQUIPMENT_GRADE_COLORS["TREASURE"],
            EquipmentGrade.ARTIFACT: EQUIPMENT_GRADE_COLORS["ARTIFACT"],
        }
        return color_map.get(self, Color.COMMON_WHITE)

