from typing import TYPE_CHECKING, Optional

from src.classes.tile import Tile, TileType
from src.classes.sect_region import SectRegion

if TYPE_CHECKING:
    from src.classes.region import Region


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
        from src.classes.region import regions_by_id, regions_by_name
        from src.classes.region import normal_regions_by_id, normal_regions_by_name
        from src.classes.region import cultivate_regions_by_id, cultivate_regions_by_name
        from src.classes.region import city_regions_by_id, city_regions_by_name
        
        self.regions = regions_by_id
        self.region_names = regions_by_name
        self.normal_regions = normal_regions_by_id
        self.normal_region_names = normal_regions_by_name
        self.cultivate_regions = cultivate_regions_by_id
        self.cultivate_region_names = cultivate_regions_by_name
        self.city_regions = city_regions_by_id
        self.city_region_names = city_regions_by_name
        # 宗门总部区域集合（由地图生成阶段注入），保持与其他区域一致的“提前维护”策略
        self.update_sect_regions()

    def update_sect_regions(self) -> None:
        """根据当前 self.regions 动态刷新宗门总部区域字典。"""
        self.sect_regions = {rid: r for rid, r in self.regions.items() if isinstance(r, SectRegion)}

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

    def get_region(self, x: int, y: int) -> Optional['Region']:
        """
        获取一个region。
        """
        return self.tiles[(x, y)].region

    def get_info(self, detailed: bool = False) -> dict:
        """
        返回地图信息（dict）。
        - detailed=False：各类区域返回名称列表
        - detailed=True：各类区域返回详细信息字符串列表
        """
        def build_regions_info(regions_dict) -> list[str]:
            if detailed:
                return [r.get_detailed_info() for r in regions_dict.values()]
            return [r.get_info() for r in regions_dict.values()]

        return {
            "修炼区域（可以修炼以增进修为）": build_regions_info(self.cultivate_regions),
            "普通区域（可以狩猎或采集）": build_regions_info(self.normal_regions),
            "城市区域（可以交易）": build_regions_info(self.city_regions),
            "宗门总部（宗门弟子可在此进行疗伤等操作）": build_regions_info(self.sect_regions),
        }


