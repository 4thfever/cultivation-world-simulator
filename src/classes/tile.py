from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.classes.region import Region

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


@dataclass
class Tile():
    # 实际的地块
    type: TileType
    x: int
    y: int
    region: 'Region' = None # 可以是一个region的一部分，也可以不属于任何region

class Map():
    """
    通过dict记录position 到 tile。
    """
    def __init__(self, width: int, height: int):
        self.tiles = {}
        self.width = width
        self.height = height
        
        # 加载所有region数据到Map中
        self._load_regions()
    
    def _load_regions(self):
        """从配置文件加载所有区域数据到Map实例中"""
        # 延迟导入避免循环导入
        from src.classes.region import load_all_regions
        
        self.regions, self.region_names = load_all_regions()

    def is_in_bounds(self, x: int, y: int) -> bool:
        """
        判断坐标是否在地图边界内。
        """
        return 0 <= x < self.width and 0 <= y < self.height

    def create_tile(self, x: int, y: int, tile_type: TileType):
        self.tiles[(x, y)] = Tile(tile_type, x, y, region=None)

    def get_tile(self, x: int, y: int) -> Tile:
        return self.tiles[(x, y)]

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

    def get_region(self, x: int, y: int) -> 'Region | None':
        """
        获取一个region。
        """
        return self.tiles[(x, y)].region
