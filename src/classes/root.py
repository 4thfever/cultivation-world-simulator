"""
灵根
目前只有五行：金木水火土。
其实和EssenceType很类似
但是单独拿出来是因为，之后可能整特殊的复杂灵根
所以这里单独定义一个Root类，用来描述灵根。
"""
from enum import Enum

from src.classes.essence import EssenceType

class Root(Enum):
    """
    灵根
    """
    GOLD = "金"
    WOOD = "木"
    WATER = "水"
    FIRE = "火"
    EARTH = "土"
    
    @classmethod
    def from_str(cls, root_str: str) -> 'Root':
        """
        从字符串创建Root实例
        
        Args:
            root_str: 灵根的字符串表示，如 "金", "木", "水", "火", "土"
            
        Returns:
            对应的Root枚举值
            
        Raises:
            ValueError: 如果字符串不匹配任何已知的灵根类型
        """
        for root in cls:
            if root.value == root_str:
                return root
        raise ValueError(f"Unknown root type: {root_str}")

corres_essence_type = {
    Root.GOLD: EssenceType.GOLD,
    Root.WOOD: EssenceType.WOOD,
    Root.WATER: EssenceType.WATER,
    Root.FIRE: EssenceType.FIRE,
    Root.EARTH: EssenceType.EARTH,
}