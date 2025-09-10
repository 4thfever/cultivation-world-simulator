from enum import Enum
from collections import defaultdict


class EssenceType(Enum):
    """
    灵气类型
    """
    GOLD = "gold" # 金
    WOOD = "wood" # 木
    WATER = "water" # 水
    FIRE = "fire" # 火
    EARTH = "earth" # 土

    def __str__(self) -> str:
        """返回灵气类型的中文名称"""
        return essence_names.get(self, self.value)
    
    @classmethod
    def from_str(cls, essence_str: str) -> 'EssenceType':
        """
        从字符串创建EssenceType实例
        
        Args:
            essence_str: 灵气的字符串表示，如 "金", "木", "水", "火", "土"
            
        Returns:
            对应的EssenceType枚举值
            
        Raises:
            ValueError: 如果字符串不匹配任何已知的灵气类型
        """
        # 首先尝试匹配中文名称
        for essence_type, chinese_name in essence_names.items():
            if chinese_name == essence_str:
                return essence_type
        
        # 然后尝试匹配英文值
        for essence_type in cls:
            if essence_type.value == essence_str:
                return essence_type
                
        raise ValueError(f"Unknown essence type: {essence_str}")

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
