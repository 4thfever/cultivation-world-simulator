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
        # 维护“最终归属”的每个 region 的坐标集合（由分配流程写入）
        # key: region.id, value: list[(x, y)]
        self.region_cors: dict[int, list[tuple[int, int]]] = {}
        
        # 区域字典，由外部加载器 (load_map.py) 填充
        self.regions = {}
        self.region_names = {}
        self.sect_regions = {}
        
        # 这些分类字典可能暂时不再自动维护，或者需要 load_map.py 手动维护
        # 为了兼容性，先初始化为空
        self.normal_regions = {}
        self.normal_region_names = {}
        self.cultivate_regions = {}
        self.cultivate_region_names = {}
        self.city_regions = {}
        self.city_region_names = {}

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

    def get_info(self, detailed: bool = False, avatar: object = None) -> dict:
        """
        返回地图信息（dict）。
        avatar: 如果提供，将用于：
               1. 过滤仅返回 avatar.known_regions 中的区域
               2. 计算并在描述中追加从 avatar 当前位置到各区域的距离
        """
        if TYPE_CHECKING:
             from src.classes.avatar import Avatar

        from src.classes.region import NormalRegion, CultivateRegion, CityRegion
        from src.utils.distance import chebyshev_distance
        
        known_region_ids = avatar.known_regions if avatar else None
        current_loc = (avatar.pos_x, avatar.pos_y) if avatar else None
        
        def filter_regions(cls):
            return {
                rid: r for rid, r in self.regions.items() 
                if known_region_ids is None or rid in known_region_ids
            }

        def build_regions_info(regions_dict) -> list[str]:
            infos = []
            for r in regions_dict.values():
                base_info = r.get_detailed_info() if detailed else r.get_info()
                
                # 如果有当前位置，追加距离信息
                dist = chebyshev_distance(current_loc, r.center_loc)
                # 估算到达时间：距离 / 步长 (向上取整)
                step_len = avatar.move_step_length
                months = (dist + step_len - 1) // step_len
                # 避免显示 0 个月
                months = max(1, months)
                base_info += f"（距离：{months}月）"
                
                infos.append(base_info)
            return infos

        return {
            "修炼区域（可以修炼以增进修为）": build_regions_info(filter_regions(CultivateRegion)),
            "普通区域（可以狩猎或采集）": build_regions_info(filter_regions(NormalRegion)),
            "城市区域（可以交易）": build_regions_info(filter_regions(CityRegion)),
            "宗门总部（宗门弟子可在此进行疗伤等操作）": build_regions_info(filter_regions(SectRegion)),
        }
