from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.classes.environment.region import Region
    from src.classes.core.avatar import Avatar

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
    RUIN = "ruin" # 遗迹
    FARM = "farm" # 农田
    SECT = "sect" # 宗门
    ISLAND = "island" # 岛屿
    BAMBOO = "bamboo" # 竹林
    GOBI = "gobi" # 戈壁
    TUNDRA = "tundra" # 苔原
    MARSH = "marsh" # 湿地


# ============================================================
# 2x2 大型Tile 配置
# ============================================================

# 固定的大型Tile类型 (基于 TileType)
LARGE_TILE_TYPES: set[TileType] = {
    TileType.CAVE,
    TileType.RUIN,
    TileType.SECT,
    TileType.CITY,
}

# 动态的大型Tile前缀 (用于宗门名、城市名等)
# 地图存储的tile名称如果以这些类别开头的子文件夹对应，则视为大型Tile
LARGE_TILE_CATEGORIES: set[str] = {"sect", "city"}


def is_large_tile(tile_name: str) -> bool:
    """
    判断一个tile名称是否为2x2大型tile。
    
    Args:
        tile_name: tile的名称（如 "cave", "明心剑宗", "青云城" 等）
    
    Returns:
        是否为大型tile
    """
    # 1. 检查是否为标准大型TileType
    try:
        t = TileType(tile_name.lower())
        return t in LARGE_TILE_TYPES
    except ValueError:
        pass
    
    # 2. 非标准类型：宗门名、城市名等
    # 这些tile的名称直接是中文名，它们的切片存在于 sects/ 或 cities/ 目录
    # 由于无法在此静态判断，我们假设所有非标准TileType的名称都是大型tile
    # (因为普通tile都在TileType枚举中)
    return True


def get_large_tile_slices(tile_name: str) -> list[str]:
    """
    获取大型tile的4个切片名称。
    
    Args:
        tile_name: 大型tile的名称
    
    Returns:
        4个切片名称的列表 [TL, TR, BL, BR]
    """
    return [f"{tile_name}_{i}" for i in range(4)]


@dataclass
class Tile():
    # 实际的地块
    type: TileType
    x: int
    y: int
    region: 'Region' = None # 可以是一个region的一部分，也可以不属于任何region

    @property
    def coordinate(self) -> tuple[int, int]:
        return (self.x, self.y)

    @property
    def location_name(self) -> str:
        """
        优雅地获取当前地点的名称。
        如果属于某个区域，返回区域名；否则返回'荒野'。
        """
        from src.i18n import t
        return self.region.name if self.region else t("Wilderness")


from src.utils.distance import manhattan_distance

def get_avatar_distance(avatar1: 'Avatar', avatar2: 'Avatar') -> int:
    """
    计算两个 Avatar 之间的曼哈顿距离
    
    Args:
        avatar1: 第一个角色
        avatar2: 第二个角色
    
    Returns:
        两个角色之间的距离
    """
    return manhattan_distance((avatar1.pos_x, avatar1.pos_y), (avatar2.pos_x, avatar2.pos_y))
