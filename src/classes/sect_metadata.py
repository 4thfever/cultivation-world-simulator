from __future__ import annotations

from typing import TYPE_CHECKING

from src.classes.core.sect import sects_by_id
from src.classes.environment.sect_region import SectRegion

if TYPE_CHECKING:
    from src.classes.core.sect import Sect
    from src.classes.core.world import World


def get_sect_region_by_sect_id(world: "World", sect_id: int) -> SectRegion | None:
    game_map = getattr(world, "map", None)
    sect_regions = getattr(game_map, "sect_regions", {}) or {}
    for region in sect_regions.values():
        if int(getattr(region, "sect_id", -1)) == int(sect_id):
            return region
    return None


def get_sect_region_id_by_sect_id(world: "World", sect_id: int) -> int | None:
    region = get_sect_region_by_sect_id(world, sect_id)
    if region is None:
        return None
    return int(getattr(region, "id", 0)) or None


def is_in_sect_headquarter(world: "World", sect: "Sect" | None, region: object) -> bool:
    if sect is None or not isinstance(region, SectRegion):
        return False
    return int(getattr(region, "sect_id", -1)) == int(getattr(sect, "id", -1))


def sync_world_sect_metadata(world: "World") -> None:
    """
    同步宗门本体与宗门驻地区域的派生展示字段。

    约定：
    - `Sect.id <-> SectRegion.sect_id` 是唯一绑定真源；
    - `Sect.headquarter.*` 和 `SectRegion.sect_name` 由该绑定派生；
    - 名称只用于展示，不再承担关系绑定职责。
    """
    game_map = getattr(world, "map", None)
    if game_map is None:
        return

    if hasattr(game_map, "update_sect_regions"):
        game_map.update_sect_regions()

    sect_regions = getattr(game_map, "sect_regions", {}) or {}
    for region in sect_regions.values():
        sect = sects_by_id.get(int(getattr(region, "sect_id", -1)))
        if sect is None:
            continue

        region.sect_name = str(getattr(sect, "name", "") or "")
        headquarter = getattr(sect, "headquarter", None)
        if headquarter is None:
            continue
        headquarter.name = str(getattr(region, "name", "") or "")
        headquarter.desc = str(getattr(region, "desc", "") or "")
