import os
import csv
from src.classes.environment.map import Map
from src.classes.environment.tile import TileType
from src.classes.environment.region import Region, NormalRegion, CultivateRegion, CityRegion
from src.classes.environment.sect_region import SectRegion
from src.utils.df import game_configs, get_str, get_int
from src.classes.essence import EssenceType
from src.classes.core.sect import sects_by_id  # 直接导入已加载的宗门数据
from src.utils.config import CONFIG

# 静态配置路径
CONFIG_DIR = CONFIG.paths.game_configs

def load_cultivation_world_map() -> Map:
    """
    从静态 CSV 文件加载修仙世界地图。
    读取: tile_map.csv, region_map.csv
    以及: normal/city/cultivate/sect_region.csv
    """
    tile_csv = CONFIG_DIR / "tile_map.csv"
    region_csv = CONFIG_DIR / "region_map.csv"
    
    if not tile_csv.exists() or not region_csv.exists():
        raise FileNotFoundError(f"Map data files not found in {CONFIG_DIR}")

    # 1. 读取 Tile Map 以确定尺寸
    with open(tile_csv, 'r', encoding='utf-8') as f:
        tile_rows = list(csv.reader(f))
    
    height = len(tile_rows)
    width = len(tile_rows[0]) if height > 0 else 0
    
    game_map = Map(width=width, height=height)
    
    # 2. 填充 Tile Type
    for y, row in enumerate(tile_rows):
        for x, tile_name in enumerate(row):
            if x < width:
                try:
                    t_type = TileType[tile_name.upper()]
                except KeyError:
                    # 如果不是标准地形，则是宗门驻地名称
                    # 这些名称直接对应 SECT 类型
                    t_type = TileType.SECT
                
                game_map.create_tile(x, y, t_type)
    
    # 3. 读取 Region Map 并聚合坐标
    # region_coords: { region_id: [(x, y), ...] }
    region_coords = {}
    
    with open(region_csv, 'r', encoding='utf-8') as f:
        region_rows = list(csv.reader(f))
        
    for y, row in enumerate(region_rows):
        if y >= height: break
        for x, val in enumerate(row):
            if x >= width: break
            try:
                rid = int(val)
                if rid != -1:
                    if rid not in region_coords:
                        region_coords[rid] = []
                    region_coords[rid].append((x, y))
            except ValueError:
                continue

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
            
            # 构建参数
            params = {
                "id": rid,
                "name": get_str(row, "name"),
                "desc": get_str(row, "desc"),
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
