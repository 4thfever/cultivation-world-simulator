from enum import Enum
from dataclasses import dataclass

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

@dataclass
class Region():
    """
    理想中，一些地块应当在一起组成一个区域。
    比如，某山；某湖、江、海；某森林；某平原；某城市；
    一些分布，比如物产，按照Region来分布。
    再比如，灵气，应当也是按照region分布的。
    默认，一个region内部的属性，是共通的。
    同时，NPC应当对Region有观测和认知。
    """
    name: str
    description: str
    qi: int # 灵气，从0~255
    # 物产
    # 灵气
    # 其他

@dataclass
class Tile():
    # 实际的地块
    type: TileType
    x: int
    y: int
    # region: Region

class Map():
    """
    通过dict记录position 到 tile。
    TODO: 记录region到position的映射。
    TODO: 有特色的地貌，比如西部大漠，东部平原，最东海洋和岛国。南边热带雨林，北边雪山和冰原。
    """
    def __init__(self, width: int, height: int):
        self.tiles = {}
        self.width = width
        self.height = height

    def is_in_bounds(self, x: int, y: int) -> bool:
        """
        判断坐标是否在地图边界内。
        """
        return 0 <= x < self.width and 0 <= y < self.height

    def create_tile(self, x: int, y: int, tile_type: TileType):
        self.tiles[(x, y)] = Tile(tile_type, x, y)

    def get_tile(self, x: int, y: int) -> Tile:
        return self.tiles[(x, y)]