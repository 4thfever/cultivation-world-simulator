from src.classes.environment.map import Map
from src.classes.environment.tile import TileType
from src.classes.environment.region import NormalRegion, CultivateRegion, CityRegion
from src.classes.environment.sect_region import SectRegion
from src.utils.df import game_configs, get_str, get_int, get_float
from src.classes.essence import EssenceType
from src.classes.core.sect import sects_by_id  # 直接导入已加载的宗门数据
from src.run.map_presets import resolve_map_source_file
from src.run.map_source import (
    MapSource,
    collect_region_coords,
    derive_tile_rows_from_region_rows,
    map_source_to_dict,
    read_map_source,
)

def load_cultivation_world_map(map_id: str | None = None) -> Map:
    """
    从 region-first 地图源加载修仙世界地图。
    读取: maps/<map_id>/map.json
    以及: normal/city/cultivate/sect_region.csv
    """
    preset, source_path = resolve_map_source_file(map_id)
    source = read_map_source(source_path)
    return build_map_from_source(
        source,
        map_id=preset.id,
        map_name=preset.localized_name,
        preset_version=preset.version,
    )


def build_map_from_source(
    source: MapSource,
    *,
    map_id: str | None = None,
    map_name: str = "",
    preset_version: int | None = None,
) -> Map:
    tile_rows = derive_tile_rows_from_region_rows(
        source.region_rows,
        wilderness_tile=source.wilderness_tile,
    )
    game_map = build_map_from_rows(
        tile_rows,
        source.region_rows,
        map_id=map_id or source.map_id,
        map_name=map_name,
        preset_version=preset_version if preset_version is not None else source.version,
        region_overrides={
            region_id: override.to_dict()
            for region_id, override in source.region_overrides.items()
        },
    )
    game_map.wilderness_tile = source.wilderness_tile
    game_map.landmarks = {
        region_id: landmark.to_dict()
        for region_id, landmark in source.landmarks.items()
    }
    game_map.region_overrides = {
        region_id: override.to_dict()
        for region_id, override in source.region_overrides.items()
    }
    game_map.map_source = map_source_to_dict(source)
    return game_map


def build_map_from_rows(
    tile_rows: list[list[str]],
    region_rows: list[list[str | int]],
    *,
    map_id: str = "classic",
    map_name: str = "",
    preset_version: int = 1,
    region_overrides: dict[int, dict[str, object]] | None = None,
) -> Map:
    """Build a Map from already parsed tile and region matrices."""
    height = len(tile_rows)
    width = len(tile_rows[0]) if height > 0 else 0
    
    game_map = Map(width=width, height=height, map_id=map_id, map_name=map_name, preset_version=preset_version)
    game_map.region_overrides = region_overrides or {}
    
    # 2. 填充 Tile Type
    for y, row in enumerate(tile_rows):
        for x, tile_name in enumerate(row):
            if x < width:
                try:
                    t_type = TileType[tile_name.upper()]
                except KeyError:
                    if tile_name.startswith("city_"):
                        t_type = TileType.CITY
                    else:
                        # 洞府、遗迹和宗门切片都走大型 region 覆盖层。
                        # 底层地貌由地图查询序列化时提供，避免前端尝试渲染
                        # 没有普通地形贴图的 CAVE/RUIN/SECT。
                        t_type = TileType.SECT
                
                game_map.create_tile(x, y, t_type)
    
    normalized_region_rows: list[list[int]] = []
    for y, row in enumerate(region_rows):
        if y >= height:
            break
        normalized_region_row: list[int] = []
        for x, val in enumerate(row):
            if x >= width:
                break
            try:
                normalized_region_row.append(int(val))
            except (ValueError, TypeError):
                normalized_region_row.append(-1)
        normalized_region_rows.append(normalized_region_row)

    region_coords = collect_region_coords(normalized_region_rows)

    # 4. 加载 Region 元数据并创建对象
    _load_and_assign_regions(game_map, region_coords)
    
    # 5. 更新缓存
    game_map.update_sect_regions()
    
    return game_map

def _load_and_assign_regions(game_map: Map, region_coords: dict[int, list[tuple[int, int]]]):
    """
    读取各 region.csv，创建 Region 对象，并分配给 Map 和 Tile
    """
    
    # 辅助函数：处理 Region 数据
    def process_region_config(df, cls, type_tag):
        for row in df:
            rid = get_int(row, "id")
            
            if rid not in region_coords:
                continue
            
            cors = region_coords[rid]
            
            override = (getattr(game_map, "region_overrides", {}) or {}).get(rid, {})
            # 构建参数
            params = {
                "id": rid,
                "name": str(override.get("name") or get_str(row, "name")),
                "desc": str(override.get("desc") or get_str(row, "desc")),
                "cors": cors,
            }
            
            # 特有字段处理
            if type_tag == "normal":
                params["animal_ids"] = _parse_list(get_str(row, "animal_ids"))
                params["plant_ids"] = _parse_list(get_str(row, "plant_ids"))
                params["lode_ids"] = _parse_list(get_str(row, "lode_ids"))
            elif type_tag == "cultivate":
                params["essence_type"] = EssenceType.from_str(get_str(row, "root_type"))
                params["essence_density"] = get_int(row, "root_density")
                params["sub_type"] = get_str(row, "sub_type") or "cave"
            elif type_tag == "city":
                sell_ids_str = get_str(row, "sell_item_ids")
                if sell_ids_str:
                    try:
                        import ast
                        ids = ast.literal_eval(sell_ids_str)
                        if isinstance(ids, list):
                            params["sell_item_ids"] = ids
                    except Exception as e:
                        print(f"Error parsing sell_item_ids for city {rid}: {e}")
                params["population"] = get_float(row, "initial_population", 80.0)
                params["population_capacity"] = get_float(row, "population_capacity", 120.0)

            elif type_tag == "sect":
                sect_id = get_int(row, "sect_id")
                params["sect_id"] = sect_id
                
                # 直接从已加载的 sects_by_id 中获取宗门对象
                # 如果找不到对应的 sect_id，默认使用驻地名称作为兜底（防止崩溃），但正常情况下应该能找到
                sect_obj = sects_by_id.get(sect_id)
                if sect_obj:
                    params["sect_name"] = sect_obj.name
                else:
                    params["sect_name"] = get_str(row, "name")
            
            # 实例化
            try:
                region_obj = cls(**params)
                game_map.regions[rid] = region_obj
                
                # 写入 Map 缓存 (region_cors)
                game_map.region_cors[rid] = cors
                
                # 绑定到 Tiles
                for rx, ry in cors:
                    if game_map.is_in_bounds(rx, ry):
                        game_map.tiles[(rx, ry)].region = region_obj
                        
            except Exception as e:
                print(f"Error creating region {rid}: {e}")

    # 执行加载
    process_region_config(game_configs["normal_region"], NormalRegion, "normal")
    process_region_config(game_configs["city_region"], CityRegion, "city")
    process_region_config(game_configs["cultivate_region"], CultivateRegion, "cultivate")
    process_region_config(game_configs["sect_region"], SectRegion, "sect")

def _parse_list(s: str) -> list[int]:
    if not s: return []
    res = []
    for x in s.split(","):
        x = x.strip()
        if x:
            try:
                res.append(int(float(x)))
            except (ValueError, TypeError):
                pass
    return res
