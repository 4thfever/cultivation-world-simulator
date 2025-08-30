import itertools
from enum import Enum
from dataclasses import dataclass, field

from src.classes.essence import Essence, EssenceType

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

region_id_counter = itertools.count(1)


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
    essence: Essence
    id: int = field(init=False)
    center_loc: tuple[int, int] = field(init=False)
    area: int = field(init=False)

    def __post_init__(self):
        self.id = next(region_id_counter)

    def __str__(self) -> str:
        return f"区域。名字：{self.name}，描述：{self.description}，最浓的灵气：{self.get_most_dense_essence()}， 灵气值：{self.get_most_dense_essence_value()}"

    def get_most_dense_essence(self) -> EssenceType:
        return max(self.essence.density.items(), key=lambda x: x[1])[0]
    
    def get_most_dense_essence_value(self) -> int:
        most_dense_essence = self.get_most_dense_essence()
        return self.essence.density[most_dense_essence]

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Region):
            return False
        return self.id == other.id
    # 物产
    # 灵气
    # 其他

default_region = Region(name="平原", description="最普通的平原，没有什么可说的", essence=Essence(density={EssenceType.GOLD: 1, EssenceType.WOOD: 1, EssenceType.WATER: 1, EssenceType.FIRE: 1, EssenceType.EARTH: 1}))
default_region.area = 1  # 默认区域面积为1

@dataclass
class Tile():
    # 实际的地块
    type: TileType
    x: int
    y: int
    region: Region # 可以是一个region的一部分，也可以不属于任何region

class Map():
    """
    通过dict记录position 到 tile。
    """
    def __init__(self, width: int, height: int):
        self.tiles = {}
        self.regions = {}      # region_id -> region
        self.region_names = {} # region_name -> region
        self.width = width
        self.height = height

    def is_in_bounds(self, x: int, y: int) -> bool:
        """
        判断坐标是否在地图边界内。
        """
        return 0 <= x < self.width and 0 <= y < self.height

    def create_tile(self, x: int, y: int, tile_type: TileType):
        self.tiles[(x, y)] = Tile(tile_type, x, y, region=default_region)

    def get_tile(self, x: int, y: int) -> Tile:
        return self.tiles[(x, y)]

    def create_region(self, name: str, description: str, essence: Essence, locs: list[tuple[int, int]]):
        """
        创建一个region。
        """
        region = Region(name=name, description=description, essence=essence)
        center_loc = self.get_center_locs(locs)
        for loc in locs:
            self.tiles[loc].region = region
        region.center_loc = center_loc
        region.area = len(locs)
        self.regions[region.id] = region
        self.region_names[name] = region
        return region

    def get_center_locs(self, locs: list[tuple[int, int]]) -> tuple[int, int]:
        """
        获取locs的中心位置。
        如果几何中心恰好在位置列表中，返回几何中心；
        否则返回距离几何中心最近的实际位置。
        """
        if not locs:
            return (0, 0)
        
        # 分别计算x和y坐标的平均值
        avg_x = sum(loc[0] for loc in locs) // len(locs)
        avg_y = sum(loc[1] for loc in locs) // len(locs)
        center = (avg_x, avg_y)

        # 如果几何中心恰好在位置列表中，直接返回
        if center in locs:
            return center
        
        # 否则找到距离几何中心最近的实际位置
        def distance_squared(loc: tuple[int, int]) -> int:
            """计算到中心点的距离平方（避免开方运算）"""
            return (loc[0] - avg_x) ** 2 + (loc[1] - avg_y) ** 2
        
        return min(locs, key=distance_squared)

    def get_region(self, x: int, y: int) -> Region | None:
        """
        获取一个region。
        """
        return self.tiles[(x, y)].region
