from typing import TYPE_CHECKING, List, Optional
import random

if TYPE_CHECKING:
    from src.classes.core.world import World
    from src.classes.core.avatar import Avatar
    from src.classes.core.sect import Sect

def get_born_region_id(
    world: "World", 
    parents: Optional[List["Avatar"]] = None, 
    sect: Optional["Sect"] = None,
    race: object | None = None,
) -> int:
    """
    确定角色的出生地ID。
    规则：
    1. 妖族优先出生在父母所在的野外区域，否则随机野外区域。
    2. 如果有宗门（或父母有宗门），优先出生在宗门驻地。
    3. 否则，如果父母在某地，出生在离父母最近的城市。
    4. 否则，随机出生在一个城市。
    """
    from src.classes.race import is_yao_race

    if is_yao_race(race):
        parent_region_id = _get_parent_wild_region_id(world, parents)
        if parent_region_id != -1:
            return parent_region_id
        wild_region_id = _get_random_wild_region_id(world)
        if wild_region_id != -1:
            return wild_region_id

    # 1. 尝试从宗门获取
    target_sect = sect
    if not target_sect and parents:
        for p in parents:
            if p.sect:
                target_sect = p.sect
                break
    
    if target_sect:
        from src.classes.sect_metadata import get_sect_region_id_by_sect_id

        sect_region_id = get_sect_region_id_by_sect_id(world, int(target_sect.id))
        if sect_region_id is not None:
            return sect_region_id

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


def _get_parent_wild_region_id(world: "World", parents: Optional[List["Avatar"]]) -> int:
    if not parents:
        return -1
    from src.classes.environment.region import NormalRegion

    for parent in parents:
        born_region_id = getattr(parent, "born_region_id", None)
        region = world.map.regions.get(born_region_id) if born_region_id is not None else None
        if isinstance(region, NormalRegion):
            return int(born_region_id)
        tile = getattr(parent, "tile", None)
        tile_region = getattr(tile, "region", None)
        if isinstance(tile_region, NormalRegion):
            return int(tile_region.id)
    return -1


def _get_random_wild_region_id(world: "World") -> int:
    from src.classes.environment.region import NormalRegion

    wild_ids = [int(rid) for rid, region in world.map.regions.items() if isinstance(region, NormalRegion)]
    if wild_ids:
        return random.choice(wild_ids)
    return -1
