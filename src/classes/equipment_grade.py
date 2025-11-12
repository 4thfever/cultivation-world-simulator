from enum import Enum


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
        return _grade_colors.get(self, (200, 200, 200))


# 装备等级颜色映射
_grade_colors = {
    EquipmentGrade.COMMON: (150, 150, 150),    # 灰色
    EquipmentGrade.TREASURE: (138, 43, 226),   # 紫色
    EquipmentGrade.ARTIFACT: (255, 215, 0),    # 金色
}

