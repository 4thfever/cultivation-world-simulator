from typing import TYPE_CHECKING, List, Optional
import random

if TYPE_CHECKING:
    from src.classes.core.world import World
    from src.classes.core.avatar import Avatar
    from src.classes.core.sect import Sect

def get_born_region_id(
    world: "World", 
    parents: Optional[List["Avatar"]] = None, 
    sect: Optional["Sect"] = None
) -> int:
    """
    确定角色的出生地ID。
    规则：
    1. 如果有宗门（或父母有宗门），优先出生在宗门驻地。
    2. 否则，如果父母在某地，出生在离父母最近的城市。
    3. 否则，随机出生在一个城市。
    """
    # 1. 尝试从宗门获取
    target_sect = sect
    if not target_sect and parents:
        for p in parents:
            if p.sect:
                target_sect = p.sect
                break
    
    if target_sect:
        # 查找宗门驻地
        # Map 维护了 sect_regions: dict[int, Region]
        if hasattr(world.map, "sect_regions") and world.map.sect_regions:
             for rid, region in world.map.sect_regions.items():
                 # SectRegion 应该有 sect_id 属性
                 if getattr(region, "sect_id", None) == target_sect.id:
                     return rid

    # 2. 尝试从父母位置获取最近城市
    parent_loc = None
    if parents:
        for p in parents:
            if p.tile:
                parent_loc = p.tile.coordinate
                break
    
    if parent_loc:
        # 寻找最近的城市
        from src.classes.environment.region import CityRegion
        from src.utils.distance import chebyshev_distance
        
        min_dist = float('inf')
        nearest_city_id = -1
        
        # world.map.regions 包含了所有区域
        for rid, region in world.map.regions.items():
            if isinstance(region, CityRegion):
                dist = chebyshev_distance(parent_loc, region.center_loc)
                if dist < min_dist:
                    min_dist = dist
                    nearest_city_id = rid
        
        if nearest_city_id != -1:
            return nearest_city_id

    # 3. 随机城市
    from src.classes.environment.region import CityRegion
    city_ids = [rid for rid, r in world.map.regions.items() if isinstance(r, CityRegion)]
    if city_ids:
        return random.choice(city_ids)
        
    return -1
