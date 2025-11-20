from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.classes.region import Region
    from src.classes.avatar import Avatar

class TileType(Enum):
    PLAIN = "plain" # 平原
    WATER = "water" # 水域
    SEA = "sea" # 海洋
    MOUNTAIN = "mountain" # 山脉
    FOREST = "forest" # 森林
    CITY = "city" # 城市
    DESERT = "desert" # 沙漠
    RAINFOREST = "rainforest" # 热带雨林
    GLACIER = "glacier" # 冰川/冰原
    SNOW_MOUNTAIN = "snow_mountain" # 雪山
    VOLCANO = "volcano" # 火山
    GRASSLAND = "grassland" # 草原
    SWAMP = "swamp" # 沼泽
    CAVE = "cave" # 洞穴
    RUINS = "ruins" # 遗迹
    FARM = "farm" # 农田
    SECT = "sect" # 宗门
    PLACEHOLDER = "placeholder" # 2x2大建筑的占位符

@dataclass
class Tile():
    # 实际的地块
    type: TileType
    x: int
    y: int
    region: 'Region' = None # 可以是一个region的一部分，也可以不属于任何region


def get_avatar_distance(avatar1: 'Avatar', avatar2: 'Avatar') -> int:
    """
    计算两个 Avatar 之间的汉明距离（曼哈顿距离）
    
    Args:
        avatar1: 第一个角色
        avatar2: 第二个角色
    
    Returns:
        两个角色之间的距离
    """
    return abs(avatar1.pos_x - avatar2.pos_x) + abs(avatar1.pos_y - avatar2.pos_y)
