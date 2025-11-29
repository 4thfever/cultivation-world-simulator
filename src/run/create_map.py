from src.classes.map import Map
from src.classes.tile import TileType
from src.classes.essence import Essence, EssenceType
from src.classes.sect_region import SectRegion
from src.classes.region import Shape
from src.classes.sect import Sect
from src.utils.df import game_configs, get_str, get_int

BASE_W = 70
BASE_H = 50

def _scale_x(x: int, width: int) -> int:
    # 将以 BASE_W 为参考的 x 坐标按比例缩放到当前 width
    return int(round(x / BASE_W * width))

def _scale_y(y: int, height: int) -> int:
    # 将以 BASE_H 为参考的 y 坐标按比例缩放到当前 height
    return int(round(y / BASE_H * height))

def _scaled_range_x(x0: int, x1_exclusive: int, width: int) -> range:
    sx0 = max(0, min(width, _scale_x(x0, width)))
    sx1 = max(sx0, min(width, _scale_x(x1_exclusive, width)))
    return range(sx0, sx1)

def _scaled_range_y(y0: int, y1_exclusive: int, height: int) -> range:
    sy0 = max(0, min(height, _scale_y(y0, height)))
    sy1 = max(sy0, min(height, _scale_y(y1_exclusive, height)))
    return range(sy0, sy1)


def create_cultivation_world_map() -> Map:
    """
    创建修仙世界地图（按 0.8 比例缩小格子数量，保持构造不变）
    基准尺寸: 70x50 -> 实际尺寸: 56x40（约减少 36% 的 tile 数量）
    西部大漠，南部雨林，北边冰原，最东部和最南部海洋
    横向大河从大漠东部流向东南入海
    北方纵向山脉
    """
    # 将总格子数在宽高两个维度各缩小到 0.8 倍
    width = int(round(BASE_W * 0.8))
    height = int(round(BASE_H * 0.8))
    game_map = Map(width=width, height=height)
    
    # 缩放从配置中加载的区域到新地图尺度
    _scale_loaded_regions(game_map)
    # 创建基础地形
    _create_base_terrain(game_map)
    
    # 创建区域
    _assign_regions_to_tiles(game_map)
    
    return game_map

def add_sect_headquarters(game_map: Map, enabled_sects: list[Sect]):
    """
    根据已启用的宗门列表，为其添加总部区域（2x2或1x2等小矩形，hover仅显示名称与描述）。
    若未启用（列表中无该宗门），则不添加对应总部。
    """
    # 为九个宗门设计坐标（根据地图地形大势和叙事）：
    # 仅登记矩形区域的西北角与东南角
    locs: dict[str, tuple[tuple[int, int], tuple[int, int]]] = {
        "明心剑宗": ((36, 10), (37, 11)),
        "百兽宗":   ((22, 22), (23, 23)),
        "水镜宗":   ((58, 22), (59, 23)),
        "冥王宗":   ((66, 8),  (67, 9)),
        "朱勾宗":   ((48, 8),  (49, 9)),
        "合欢宗":   ((62, 40), (63, 41)),
        "镇魂宗":   ((30, 46), (31, 47)),
        "幽魂噬影宗":((44, 38), (45, 39)),
        "千帆城":   ((60, 28), (61, 29)),
        "妙化宗":   ((42, 6),  (43, 7)),   # 北部冰原边缘
        "回玄宗":   ((52, 18), (53, 19)),  # 东北部森林边缘
        "不夜城":   ((28, 4),  (29, 5)),   # 极北冰原
        "天行健宗": ((38, 25), (39, 26)),  # 中部平原，浩然峰
        "噬魔宗":   ((10, 30), (11, 31)),  # 西部大漠深处
    }

    # 从 sect_region.csv 读取（按 sect_id 对齐）：sect_name、headquarter_name、headquarter_desc
    sect_region_df = game_configs["sect_region"]
    hq_by_id: dict[int, tuple[str, str, str]] = {
        get_int(row, "sect_id"): (
            get_str(row, "sect_name"),
            get_str(row, "headquarter_name"),
            get_str(row, "headquarter_desc"),
        )
        for row in sect_region_df
    }
    # 坐标字典按 sect.name 提供，转换为按 sect.id 对齐
    id_to_coords: dict[int, tuple[tuple[int, int], tuple[int, int]]] = {
        s.id: locs[s.name] for s in enabled_sects if s.name in locs
    }

    for sect in enabled_sects:
        coords = id_to_coords.get(sect.id)
        if coords is None:
            continue
        nw, se = coords
        # 名称与描述：优先使用 sect_region.csv；若为空则回退到 sect.headquarter / sect
        hq_name = getattr(sect.headquarter, "name", sect.name) or sect.name
        hq_desc = getattr(sect.headquarter, "desc", sect.desc) or sect.desc
        csv_entry = hq_by_id.get(sect.id)
        sect_name_for_region = sect.name
        if csv_entry is not None:
            sect_name_csv, csv_name, csv_desc = csv_entry
            if csv_name:
                hq_name = csv_name
            if csv_desc:
                hq_desc = csv_desc
            if sect_name_csv:
                sect_name_for_region = sect_name_csv
        # 按比例缩放左上角坐标，保持区域尺寸（如2x2）不变
        size_w = se[0] - nw[0]
        size_h = se[1] - nw[1]
        # 初步缩放坐标
        nw_x = _scale_x(nw[0], game_map.width)
        nw_y = _scale_y(nw[1], game_map.height)
        se_x = nw_x + size_w
        se_y = nw_y + size_h
        # 边界修正：确保 2x2 或 1x2 等固定尺寸完整在图内
        if se_x >= game_map.width:
            shift = se_x - (game_map.width - 1)
            nw_x -= shift
            se_x -= shift
        if se_y >= game_map.height:
            shift = se_y - (game_map.height - 1)
            nw_y -= shift
            se_y -= shift
        # 最终夹紧
        nw_x = max(0, min(game_map.width - 1, nw_x))
        nw_y = max(0, min(game_map.height - 1, nw_y))
        se_x = max(nw_x, min(game_map.width - 1, se_x))
        se_y = max(nw_y, min(game_map.height - 1, se_y))
        region = SectRegion(
            id=400 + sect.id,
            name=hq_name,
            desc=hq_desc,
            shape=Shape.RECTANGLE,
            north_west_cor=f"{nw_x},{nw_y}",
            south_east_cor=f"{se_x},{se_y}",
            sect_name=sect_name_for_region,
            sect_id=sect.id,
            image_path=str(getattr(sect.headquarter, "image", None)),
        )
        game_map.regions[region.id] = region
        game_map.region_names[region.name] = region
        # 刷新 Map 内部的宗门区域缓存
        game_map.update_sect_regions()
        
        # 将宗门范围内的 Tiles 设置为 SECT 锚点或 PLACEHOLDER
        for x in range(nw_x, se_x + 1): # 注意：se_x 是 inclusive 吗？Region 定义里可能是 inclusive，这里循环用 range 需要 +1
            for y in range(nw_y, se_y + 1):
                if not game_map.is_in_bounds(x, y):
                    continue
                
                # 判断是否为左上角
                if x == nw_x and y == nw_y:
                    game_map.tiles[(x, y)].type = TileType.SECT
                else:
                    game_map.tiles[(x, y)].type = TileType.PLACEHOLDER

    # 添加完成后，重新分配到 tiles
    _assign_regions_to_tiles(game_map)

def _create_base_terrain(game_map: Map):
    """创建基础地形"""
    width, height = game_map.width, game_map.height
    
    # 先创建默认平原
    for x in range(width):
        for y in range(height):
            game_map.create_tile(x, y, TileType.PLAIN)
    
    # 西部大漠 (x: 0-18)
    for x in _scaled_range_x(0, 19, width):
        for y in range(height):
            game_map.tiles[(x, y)].type = TileType.DESERT
    
    # 南部雨林 (y: 35-49)
    for x in range(width):
        for y in _scaled_range_y(35, BASE_H, height):
            if game_map.tiles[(x, y)].type != TileType.DESERT:
                game_map.tiles[(x, y)].type = TileType.RAINFOREST
    
    # 北边冰原 (y: 0-8)
    for x in range(width):
        for y in _scaled_range_y(0, 9, height):
            if game_map.tiles[(x, y)].type != TileType.DESERT:
                game_map.tiles[(x, y)].type = TileType.GLACIER
    
    # 最东部海洋 (x: 65-69)
    for x in _scaled_range_x(65, BASE_W, width):
        for y in range(height):
            game_map.tiles[(x, y)].type = TileType.SEA
    
    # 最南部海洋 (y: 46-49)
    for x in range(width):
        for y in _scaled_range_y(46, BASE_H, height):
            game_map.tiles[(x, y)].type = TileType.SEA
    
    # 横向大河：从大漠东部(18,25)比例位置流向东南入海，河流更宽
    river_tiles = _calculate_wide_river_tiles(game_map)
    for x, y in river_tiles:
        if game_map.is_in_bounds(x, y):
            game_map.tiles[(x, y)].type = TileType.WATER
    
    # 北方纵向山脉 (x: 28-32, y: 5-20)
    for x in _scaled_range_x(28, 33, width):
        for y in _scaled_range_y(5, 21, height):
            if game_map.tiles[(x, y)].type == TileType.PLAIN:
                game_map.tiles[(x, y)].type = TileType.MOUNTAIN
    
    # 添加其他地形类型
    _add_other_terrains(game_map)

def _calculate_wide_river_tiles(game_map: Map):
    """计算宽阔大河的所有水域tiles（按比例缩放）"""
    w, h = game_map.width, game_map.height
    river_tiles = []
    
    # 按比例的关键节点
    start_x = _scale_x(18, w)
    start_y = _scale_y(25, h)
    phase_split_x = _scale_x(40, w)
    end1_x = _scale_x(65, w)
    end1_y = _scale_y(46, h)
    end2_x = _scale_x(68, w)
    end2_y = _scale_y(48, h)

    center_path = []
    x, y = start_x, start_y
    
    while x < end1_x and y < end1_y:
        center_path.append((x, y))
        if x < phase_split_x:
            x += 1
            if y < _scale_y(35, h):
                y += 1
        else:
            x += max(1, int(round(w / BASE_W * 2)))  # 按比例放大步幅
            y += 1
    
    while x < end2_x and y < end2_y:
        center_path.append((x, y))
        x += 1
        y += 1
    
    for i, (cx, cy) in enumerate(center_path):
        width_sel = 1 if i < len(center_path) // 3 else 2 if i < 2 * len(center_path) // 3 else 3
        for dx in range(-width_sel // 2, width_sel // 2 + 1):
            for dy in range(-width_sel // 2, width_sel // 2 + 1):
                river_tiles.append((cx + dx, cy + dy))
    
    return list(set(river_tiles))

def _create_2x2_cities(game_map: Map):
    """创建2*2的城市区域"""
    cities = [
        {"name": "青云城", "base_x": _scale_x(34, game_map.width), "base_y": _scale_y(21, game_map.height), "description": "繁华都市的中心"},
        {"name": "沙月城", "base_x": _scale_x(14, game_map.width), "base_y": _scale_y(19, game_map.height), "description": "沙漠绿洲中的贸易重镇"},
        {"name": "翠林城", "base_x": _scale_x(54, game_map.width), "base_y": _scale_y(14, game_map.height), "description": "森林深处的修仙重镇"}
    ]
    
    for city in cities:
        base_x, base_y = city["base_x"], city["base_y"]
        
        # 使用 2x2 布局：左上角为真实 CITY，其他为 PLACEHOLDER
        for dx in range(2):
            for dy in range(2):
                x, y = base_x + dx, base_y + dy
                if game_map.is_in_bounds(x, y):
                    if dx == 0 and dy == 0:
                         game_map.tiles[(x, y)].type = TileType.CITY
                    else:
                         game_map.tiles[(x, y)].type = TileType.PLACEHOLDER

def _create_2x2_wuxing_caves(game_map: Map):
    """创建2*2的五行洞府区域"""
    # 五行洞府配置：金木水火土
    wuxing_caves = [
        {"name": "太白金府", "base_x": _scale_x(24, game_map.width), "base_y": _scale_y(12, game_map.height), "element": EssenceType.GOLD, "description": "青峰山脉深处的金行洞府"},
        {"name": "青木洞天", "base_x": _scale_x(48, game_map.width), "base_y": _scale_y(18, game_map.height), "element": EssenceType.WOOD, "description": "青云林海中的木行洞府"},
        {"name": "玄水秘境", "base_x": _scale_x(67, game_map.width), "base_y": _scale_y(25, game_map.height), "element": EssenceType.WATER, "description": "无边碧海深处的水行洞府"},
        {"name": "离火洞府", "base_x": _scale_x(48, game_map.width), "base_y": _scale_y(33, game_map.height), "element": EssenceType.FIRE, "description": "炎狱火山旁的火行洞府"},
        {"name": "厚土玄宫", "base_x": _scale_x(32, game_map.width), "base_y": _scale_y(16, game_map.height), "element": EssenceType.EARTH, "description": "青峰山脉的土行洞府"}
    ]
    
    for cave in wuxing_caves:
        base_x, base_y = cave["base_x"], cave["base_y"]
        
        for dx in range(2):
            for dy in range(2):
                x, y = base_x + dx, base_y + dy
                if game_map.is_in_bounds(x, y):
                    if dx == 0 and dy == 0:
                         game_map.tiles[(x, y)].type = TileType.CAVE
                    else:
                         game_map.tiles[(x, y)].type = TileType.PLACEHOLDER

def _create_2x2_ruins(game_map: Map):
    """创建2*2的遗迹区域"""
    ruins = [
        {"name": "古越遗迹", "base_x": _scale_x(25, game_map.width), "base_y": _scale_y(40, game_map.height), "description": "雨林深处的上古遗迹"},
        {"name": "沧海遗迹", "base_x": _scale_x(66, game_map.width), "base_y": _scale_y(47, game_map.height), "description": "沉没在海中的远古文明遗迹"}
    ]
    
    for ruin in ruins:
        base_x, base_y = ruin["base_x"], ruin["base_y"]
        
        for dx in range(2):
            for dy in range(2):
                x, y = base_x + dx, base_y + dy
                if game_map.is_in_bounds(x, y):
                    if dx == 0 and dy == 0:
                         game_map.tiles[(x, y)].type = TileType.RUINS
                    else:
                         game_map.tiles[(x, y)].type = TileType.PLACEHOLDER

def _scale_loaded_regions(game_map: Map) -> None:
    """按比例缩放从 CSV 加载到 Map 的区域坐标。
    - 小型 2x2（或 1x2/2x1）保持尺寸不变，仅移动锚点
    - 其他矩形/正方形区域按比例缩放两角
    - 蜿蜒区域按比例缩放其包围框
    """
    new_regions: dict[int, object] = {}
    new_region_names: dict[str, object] = {}
    for region in list(game_map.regions.values()):
        try:
            nw_x, nw_y = map(int, str(region.north_west_cor).split(","))
            se_x, se_y = map(int, str(region.south_east_cor).split(","))
        except Exception:
            # 坐标异常的保持原样
            new_regions[region.id] = region
            new_region_names[region.name] = region
            continue
        width = game_map.width
        height = game_map.height
        cls = region.__class__
        shape = region.shape
        # 计算尺寸（包含端点，故差值为尺寸-1）
        span_w = max(0, se_x - nw_x)
        span_h = max(0, se_y - nw_y)
        if shape.name in ("RECTANGLE", "SQUARE") and span_w <= 1 and span_h <= 1:
            # 小区域保持尺寸：仅缩放左上角
            new_nw_x = max(0, min(width - 1, _scale_x(nw_x, width)))
            new_nw_y = max(0, min(height - 1, _scale_y(nw_y, height)))
            new_se_x = max(new_nw_x, min(width - 1, new_nw_x + span_w))
            new_se_y = max(new_nw_y, min(height - 1, new_nw_y + span_h))
        else:
            # 一般区域按比例缩放两角
            new_nw_x = max(0, min(width - 1, _scale_x(nw_x, width)))
            new_nw_y = max(0, min(height - 1, _scale_y(nw_y, height)))
            new_se_x = max(new_nw_x, min(width - 1, _scale_x(se_x, width)))
            new_se_y = max(new_nw_y, min(height - 1, _scale_y(se_y, height)))
        # 夹紧到地图范围
        new_nw_x = max(0, min(width - 1, new_nw_x))
        new_se_x = max(new_nw_x, min(width - 1, new_se_x))
        new_nw_y = max(0, min(height - 1, new_nw_y))
        new_se_y = max(new_nw_y, min(height - 1, new_se_y))

        params = {
            "id": region.id,
            "name": region.name,
            "desc": region.desc,
            "shape": shape,
            "north_west_cor": f"{new_nw_x},{new_nw_y}",
            "south_east_cor": f"{new_se_x},{new_se_y}",
        }
        # 附带子类特有字段
        # 普通区域需要保留物种ID列表，避免缩放重建后丢失物种信息
        if hasattr(region, "animal_ids"):
            params["animal_ids"] = list(getattr(region, "animal_ids") or [])
        if hasattr(region, "plant_ids"):
            params["plant_ids"] = list(getattr(region, "plant_ids") or [])
        if hasattr(region, "essence_type"):
            params["essence_type"] = getattr(region, "essence_type")
        if hasattr(region, "essence_density"):
            params["essence_density"] = getattr(region, "essence_density")
        # SectRegion 透传特有字段
        if hasattr(region, "sect_name"):
            params["sect_name"] = getattr(region, "sect_name")
        if hasattr(region, "sect_id"):
            params["sect_id"] = getattr(region, "sect_id")
        if hasattr(region, "image_path"):
            params["image_path"] = getattr(region, "image_path")
        new_region = cls(**params)  # 重新构建以刷新 cors/area/center
        new_regions[new_region.id] = new_region
        new_region_names[new_region.name] = new_region
    game_map.regions = new_regions
    game_map.region_names = new_region_names

def _add_other_terrains(game_map: Map):
    """添加其他地形类型到合适位置（按比例缩放区域范围）"""
    w, h = game_map.width, game_map.height
    # 草原 (中部区域)
    for x in _scaled_range_x(20, 40, w):
        for y in _scaled_range_y(12, 25, h):
            if game_map.tiles[(x, y)].type == TileType.PLAIN:
                game_map.tiles[(x, y)].type = TileType.GRASSLAND
    
    # 森林 (东中部区域)
    for x in _scaled_range_x(40, 60, w):
        for y in _scaled_range_y(10, 30, h):
            if game_map.tiles[(x, y)].type == TileType.PLAIN:
                game_map.tiles[(x, y)].type = TileType.FOREST
    
    # 雪山 (北部山脉附近)
    for x in _scaled_range_x(25, 35, w):
        for y in _scaled_range_y(2, 8, h):
            if game_map.tiles[(x, y)].type == TileType.GLACIER:
                game_map.tiles[(x, y)].type = TileType.SNOW_MOUNTAIN
    
    # 火山 (单独区域)
    for x in _scaled_range_x(52, 55, w):
        for y in _scaled_range_y(32, 35, h):
            if game_map.tiles[(x, y)].type == TileType.PLAIN:
                game_map.tiles[(x, y)].type = TileType.VOLCANO
    
    # 创建2*2城市区域
    _create_2x2_cities(game_map)
    
    # 创建2*2五行洞府区域
    _create_2x2_wuxing_caves(game_map)
    
    # 创建2*2遗迹区域
    _create_2x2_ruins(game_map)
    
    # 农田 (城市附近，改为不与草原重叠的区域)
    for x in _scaled_range_x(33, 38, w):
        for y in _scaled_range_y(25, 30, h):
            if game_map.tiles[(x, y)].type == TileType.PLAIN:
                game_map.tiles[(x, y)].type = TileType.FARM
    
    # 沼泽 (河流附近的低洼地区，避开雨林区域)
    for x in _scaled_range_x(42, 46, w):
        for y in _scaled_range_y(30, 34, h):
            if game_map.tiles[(x, y)].type == TileType.PLAIN:
                game_map.tiles[(x, y)].type = TileType.SWAMP

def _assign_regions_to_tiles(game_map: Map):
    """将区域分配给地图中的tiles"""
    # 初始化所有tiles的region为None
    for x in range(game_map.width):
        for y in range(game_map.height):
            game_map.tiles[(x, y)].region = None
    
    # 遍历所有region，为对应的坐标分配正确的region
    # 现在从map实例获取region信息，而不是直接从region.py导入
    for region in game_map.regions.values():
        for coord_x, coord_y in region.cors:
            # 确保坐标在地图范围内
            if game_map.is_in_bounds(coord_x, coord_y):
                game_map.tiles[(coord_x, coord_y)].region = region

    # 归并“最终归属”的坐标集合到 Map.region_cors，并回写到各 Region
    final_region_cors: dict[int, list[tuple[int, int]]] = {}
    for x in range(game_map.width):
        for y in range(game_map.height):
            tile = game_map.tiles[(x, y)]
            r = tile.region
            if r is None:
                continue
            rid = r.id
            if rid not in final_region_cors:
                final_region_cors[rid] = []
            final_region_cors[rid].append((x, y))

    # 写入 Map 级缓存
    game_map.region_cors = final_region_cors

    # 将最终坐标集合回写到各 Region 的 cors/area/center_loc
    for rid, region in list(game_map.regions.items()):
        cors = final_region_cors.get(rid, [])
        # 去重并排序，保证稳定性
        cors = sorted(set(cors))
        region.cors = cors
        region.area = len(cors)
        # 计算新的中心点（若无格点则保持原中心）
        if cors:
            region.center_loc = game_map.get_center_locs(cors)

if __name__ == "__main__":
    # 创建地图
    cultivation_map = create_cultivation_world_map()
    print(f"修仙世界地图创建完成！尺寸: {cultivation_map.width}x{cultivation_map.height}")
    
    # 统计各地形类型
    terrain_count = {}
    regions_count = {}
    for x in range(cultivation_map.width):
        for y in range(cultivation_map.height):
            tile = cultivation_map.get_tile(x, y)
            tile_type = tile.type.value
            if tile_type not in terrain_count:
                terrain_count[tile_type] = 0
            terrain_count[tile_type] += 1
            
            region = cultivation_map.get_region(x, y)
            if region.name not in regions_count:
                regions_count[region.name] = 0
            regions_count[region.name] += 1
    
    print("各地形类型分布:")
    for terrain_type, count in terrain_count.items():
        print(f"  {terrain_type}: {count}个地块")
    
    print("\n各区域分布:")
    for region_name, count in regions_count.items():
        print(f"  {region_name}: {count}个地块")
