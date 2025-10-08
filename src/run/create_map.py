from src.classes.map import Map
from src.classes.tile import TileType
from src.classes.essence import Essence, EssenceType
from src.classes.sect_region import SectRegion
from src.classes.region import Shape
from src.classes.sect import Sect

def create_cultivation_world_map() -> Map:
    """
    创建修仙世界地图
    尺寸: 70x50
    西部大漠，南部雨林，北边冰原，最东部和最南部海洋
    横向大河从大漠东部流向东南入海
    北方纵向山脉
    """
    game_map = Map(width=70, height=50)
    
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
        "明心剑宗": ((36, 10), (37, 11)),   # 北部山脉以南的名门仙山
        "百兽宗":   ((22, 22), (23, 23)),   # 中西部靠近山林
        "水镜宗":   ((58, 22), (59, 23)),   # 湖心三岛——近东海内陆湖
        "冥王宗":   ((66, 8),  (67, 9)),    # 东北近海的群岛
        "朱勾宗":   ((48, 8),  (49, 9)),    # 东北内陆山地近雪域
        "合欢宗":   ((62, 40), (63, 41)),   # 东南近海桃花岛
        "镇魂宗":   ((30, 46), (31, 47)),   # 极南海上礁岛
        "幽魂噬影宗":((44, 38), (45, 39)),  # 南部雨林深处
        "千帆城":   ((60, 28), (61, 29)),   # 海上浮岛靠近入海口
    }

    name_to_sect = {s.name: s for s in enabled_sects}

    for sect_name, (nw, se) in locs.items():
        sect = name_to_sect.get(sect_name)
        if sect is None:
            continue
        # 名称与描述来自 sect.headquarter；若为空则用 sect 名称/描述
        hq_name = getattr(sect.headquarter, "name", sect.name) or sect.name
        hq_desc = getattr(sect.headquarter, "desc", sect.desc) or sect.desc
        region = SectRegion(
            id=400 + sect.id,  # 4xx 预留给宗门总部区域id
            name=hq_name,
            desc=hq_desc,
            shape=Shape.RECTANGLE,
            north_west_cor=f"{nw[0]},{nw[1]}",
            south_east_cor=f"{se[0]},{se[1]}",
            image_path=str(getattr(sect.headquarter, "image", None)),
        )
        game_map.regions[region.id] = region
        game_map.region_names[region.name] = region

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
    for x in range(19):
        for y in range(height):
            game_map.tiles[(x, y)].type = TileType.DESERT
    
    # 南部雨林 (y: 35-49)
    for x in range(width):
        for y in range(35, height):
            if game_map.tiles[(x, y)].type != TileType.DESERT:
                game_map.tiles[(x, y)].type = TileType.RAINFOREST
    
    # 北边冰原 (y: 0-8)
    for x in range(width):
        for y in range(9):
            if game_map.tiles[(x, y)].type != TileType.DESERT:
                game_map.tiles[(x, y)].type = TileType.GLACIER
    
    # 最东部海洋 (x: 65-69)
    for x in range(65, width):
        for y in range(height):
            game_map.tiles[(x, y)].type = TileType.SEA
    
    # 最南部海洋 (y: 46-49)
    for x in range(width):
        for y in range(46, height):
            game_map.tiles[(x, y)].type = TileType.SEA
    
    # 横向大河：从大漠东部(18, 25)流向东南入海，河流更宽
    river_tiles = _calculate_wide_river_tiles()
    for x, y in river_tiles:
        if game_map.is_in_bounds(x, y):
            game_map.tiles[(x, y)].type = TileType.WATER
    
    # 北方纵向山脉 (x: 28-32, y: 5-20)
    for x in range(28, 33):
        for y in range(5, 21):
            if game_map.tiles[(x, y)].type == TileType.PLAIN:
                game_map.tiles[(x, y)].type = TileType.MOUNTAIN
    
    # 添加其他地形类型
    _add_other_terrains(game_map)

def _calculate_wide_river_tiles():
    """计算宽阔大河的所有水域tiles：从(18, 25)流向东南到海洋，宽度为3-4格"""
    river_tiles = []
    
    # 计算河流中心线
    center_path = []
    x, y = 18, 25
    
    while x < 65 and y < 46:
        center_path.append((x, y))
        # 向东南流淌
        if x < 40:
            x += 1
            if y < 35:
                y += 1
        else:
            x += 2
            y += 1
    
    # 连接到海洋
    while x < 68 and y < 48:
        center_path.append((x, y))
        x += 1
        y += 1
    
    # 根据中心线生成宽阔的河流
    for i, (cx, cy) in enumerate(center_path):
        # 河流宽度随位置变化：源头较窄，入海口较宽
        width = 1 if i < len(center_path) // 3 else 2 if i < 2 * len(center_path) // 3 else 3
        
        # 为每个中心点添加周围的水域
        for dx in range(-width//2, width//2 + 1):
            for dy in range(-width//2, width//2 + 1):
                nx, ny = cx + dx, cy + dy
                river_tiles.append((nx, ny))
    
    return list(set(river_tiles))  # 去重

def _create_2x2_cities(game_map: Map):
    """创建2*2的城市区域"""
    cities = [
        {"name": "青云城", "base_x": 34, "base_y": 21, "description": "繁华都市的中心"},
        {"name": "沙月城", "base_x": 14, "base_y": 19, "description": "沙漠绿洲中的贸易重镇"},
        {"name": "翠林城", "base_x": 54, "base_y": 14, "description": "森林深处的修仙重镇"}
    ]
    
    for city in cities:
        base_x, base_y = city["base_x"], city["base_y"]
        
        for dx in range(2):
            for dy in range(2):
                x, y = base_x + dx, base_y + dy
                if game_map.is_in_bounds(x, y):
                    game_map.tiles[(x, y)].type = TileType.CITY

def _create_2x2_wuxing_caves(game_map: Map):
    """创建2*2的五行洞府区域"""
    # 五行洞府配置：金木水火土
    wuxing_caves = [
        {"name": "太白金府", "base_x": 26, "base_y": 12, "element": EssenceType.GOLD, "description": "青峰山脉深处的金行洞府"},
        {"name": "青木洞天", "base_x": 48, "base_y": 18, "element": EssenceType.WOOD, "description": "青云林海中的木行洞府"},
        {"name": "玄水秘境", "base_x": 67, "base_y": 25, "element": EssenceType.WATER, "description": "无边碧海深处的水行洞府"},
        {"name": "离火洞府", "base_x": 50, "base_y": 33, "element": EssenceType.FIRE, "description": "炎狱火山旁的火行洞府"},
        {"name": "厚土玄宫", "base_x": 30, "base_y": 16, "element": EssenceType.EARTH, "description": "青峰山脉的土行洞府"}
    ]
    
    for cave in wuxing_caves:
        base_x, base_y = cave["base_x"], cave["base_y"]
        
        for dx in range(2):
            for dy in range(2):
                x, y = base_x + dx, base_y + dy
                if game_map.is_in_bounds(x, y):
                    game_map.tiles[(x, y)].type = TileType.CAVE

def _create_2x2_ruins(game_map: Map):
    """创建2*2的遗迹区域"""
    ruins = [
        {"name": "古越遗迹", "base_x": 25, "base_y": 40, "description": "雨林深处的上古遗迹"},
        {"name": "沧海遗迹", "base_x": 66, "base_y": 47, "description": "沉没在海中的远古文明遗迹"}
    ]
    
    for ruin in ruins:
        base_x, base_y = ruin["base_x"], ruin["base_y"]
        
        for dx in range(2):
            for dy in range(2):
                x, y = base_x + dx, base_y + dy
                if game_map.is_in_bounds(x, y):
                    game_map.tiles[(x, y)].type = TileType.RUINS

def _add_other_terrains(game_map: Map):
    """添加其他地形类型到合适位置"""
    # 草原 (中部区域)
    for x in range(20, 40):
        for y in range(12, 25):
            if game_map.tiles[(x, y)].type == TileType.PLAIN:
                game_map.tiles[(x, y)].type = TileType.GRASSLAND
    
    # 森林 (东中部区域)
    for x in range(40, 60):
        for y in range(10, 30):
            if game_map.tiles[(x, y)].type == TileType.PLAIN:
                game_map.tiles[(x, y)].type = TileType.FOREST
    
    # 雪山 (北部山脉附近)
    for x in range(25, 35):
        for y in range(2, 8):
            if game_map.tiles[(x, y)].type == TileType.GLACIER:
                game_map.tiles[(x, y)].type = TileType.SNOW_MOUNTAIN
    
    # 火山 (单独区域)
    for x in range(52, 55):
        for y in range(32, 35):
            if game_map.tiles[(x, y)].type == TileType.PLAIN:
                game_map.tiles[(x, y)].type = TileType.VOLCANO
    
    # 创建2*2城市区域
    _create_2x2_cities(game_map)
    
    # 创建2*2五行洞府区域
    _create_2x2_wuxing_caves(game_map)
    
    # 创建2*2遗迹区域
    _create_2x2_ruins(game_map)
    
    # 农田 (城市附近，改为不与草原重叠的区域)
    for x in range(33, 38):
        for y in range(25, 30):
            if game_map.tiles[(x, y)].type == TileType.PLAIN:
                game_map.tiles[(x, y)].type = TileType.FARM
    
    # 沼泽 (河流附近的低洼地区，避开雨林区域)
    for x in range(42, 46):
        for y in range(30, 34):
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
