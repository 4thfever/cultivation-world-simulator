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

corres_essence_type = {
    Root.GOLD: EssenceType.GOLD,
    Root.WOOD: EssenceType.WOOD,
    Root.WATER: EssenceType.WATER,
    Root.FIRE: EssenceType.FIRE,
    Root.EARTH: EssenceType.EARTH,
}