from enum import Enum
from collections import defaultdict


class EssenceType(Enum):
    """
    灵气类型
    """
    GOLD = "GOLD"  # 金
    WOOD = "WOOD"  # 木
    WATER = "WATER"  # 水
    FIRE = "FIRE"  # 火
    EARTH = "EARTH"  # 土

    def __str__(self) -> str:
        """返回灵气类型的翻译名称"""
        from src.i18n import t
        return t(essence_msg_ids.get(self, self.value))
    
    @classmethod
    def from_str(cls, essence_str: str) -> 'EssenceType':
        """
        从字符串创建EssenceType实例
        
        Args:
            essence_str: 灵气的字符串表示
            
        Returns:
            对应的EssenceType枚举值
        """
        s = str(essence_str).strip().upper()
        
        # 建立映射
        mapping = {
            "金": "GOLD", "GOLD": "GOLD",
            "木": "WOOD", "WOOD": "WOOD",
            "水": "WATER", "WATER": "WATER",
            "火": "FIRE", "FIRE": "FIRE",
            "土": "EARTH", "EARTH": "EARTH"
        }
        
        etype_id = mapping.get(s)
        if etype_id:
            return cls(etype_id)
                
        raise ValueError(f"Unknown essence type: {essence_str}")

essence_msg_ids = {
    EssenceType.GOLD: "gold_essence",
    EssenceType.WOOD: "wood_essence",
    EssenceType.WATER: "water_essence",
    EssenceType.FIRE: "fire_essence",
    EssenceType.EARTH: "earth_essence"
}

# 兼容性：保留旧的dict用于from_str方法
essence_names = {
    EssenceType.GOLD: "金",
    EssenceType.WOOD: "木",
    EssenceType.WATER: "水",
    EssenceType.FIRE: "火",
    EssenceType.EARTH: "土"
}

class Essence():
    """
    灵气，用来描述某个region的灵气情况。
    灵气分为五种：金木水火土（先这些，之后加新的）
    每个region有五种灵气，每种灵气有不同的浓度。
    浓度从0~10。
    """
    def __init__(self, density: dict[EssenceType, int]):
        self.density = defaultdict(int)
        for essence_type, density in density.items():
            self.density[essence_type] = density

    def get_density(self, essence_type: EssenceType) -> int:
        return self.density[essence_type]

    def set_density(self, essence_type: EssenceType, density: int):
        self.density[essence_type] = density
