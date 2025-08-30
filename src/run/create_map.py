from src.classes.tile import Map, TileType
from src.classes.essence import Essence, EssenceType

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
    _create_regions(game_map)
    
    return game_map

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

def _create_regions(game_map: Map):
    """创建区域并分配灵气"""
    
    # 收集各地形的坐标
    terrain_coords = {}
    for x in range(game_map.width):
        for y in range(game_map.height):
            tile_type = game_map.tiles[(x, y)].type
            if tile_type not in terrain_coords:
                terrain_coords[tile_type] = []
            terrain_coords[tile_type].append((x, y))
    
    # 西域流沙 (大漠)
    if TileType.DESERT in terrain_coords:
        essence = Essence({
            EssenceType.FIRE: 8,
            EssenceType.EARTH: 7,
            EssenceType.GOLD: 6,
            EssenceType.WATER: 1,
            EssenceType.WOOD: 2
        })
        game_map.create_region(
            "西域流沙",
            "茫茫大漠，黄沙漫天。此地火行灵气浓郁，土行次之，乃是修炼火系功法的绝佳之地。",
            essence,
            terrain_coords[TileType.DESERT]
        )
    
    # 南疆蛮荒 (雨林)
    if TileType.RAINFOREST in terrain_coords:
        essence = Essence({
            EssenceType.WOOD: 8,  # 木行主属性，但低于洞府的10
            EssenceType.WATER: 6,
            EssenceType.EARTH: 5,
            EssenceType.FIRE: 3,
            EssenceType.GOLD: 2
        })
        game_map.create_region(
            "南疆蛮荒",
            "古木参天，藤蔓缠绕。此地木行灵气极为浓郁，水行次之，是修炼木系功法和炼制灵药的宝地。",
            essence,
            terrain_coords[TileType.RAINFOREST]
        )
    
    # 极北冰原 (冰原)
    if TileType.GLACIER in terrain_coords:
        essence = Essence({
            EssenceType.WATER: 8,
            EssenceType.GOLD: 6,
            EssenceType.EARTH: 4,
            EssenceType.FIRE: 1,
            EssenceType.WOOD: 3
        })
        game_map.create_region(
            "极北冰原",
            "千里冰封，万年不化。此地水行灵气充沛，金行次之，寒气逼人，唯有修炼寒冰功法者方可久居。",
            essence,
            terrain_coords[TileType.GLACIER]
        )
    
    # 无边碧海 (海洋)
    if TileType.SEA in terrain_coords:
        essence = Essence({
            EssenceType.WATER: 8,  # 水行主属性，但低于洞府的10
            EssenceType.GOLD: 4,
            EssenceType.WOOD: 3,
            EssenceType.EARTH: 2,
            EssenceType.FIRE: 1
        })
        game_map.create_region(
            "无边碧海",
            "浩瀚无垠，波涛汹涌。此地水行灵气达到极致，蕴含无穷玄机，是水系修士向往的圣地。",
            essence,
            terrain_coords[TileType.SEA]
        )
    
    # 天河奔流 (大河)
    if TileType.WATER in terrain_coords:
        essence = Essence({
            EssenceType.WATER: 7,
            EssenceType.WOOD: 5,
            EssenceType.EARTH: 4,
            EssenceType.GOLD: 3,
            EssenceType.FIRE: 2
        })
        game_map.create_region(
            "天河奔流",
            "一江春水向东流，奔腾不息入东海。此河贯穿东西，水行灵气丰沛，滋养两岸万物生灵。",
            essence,
            terrain_coords[TileType.WATER]
        )
    
    # 青峰山脉 (山脉)
    if TileType.MOUNTAIN in terrain_coords:
        essence = Essence({
            EssenceType.EARTH: 8,
            EssenceType.GOLD: 7,
            EssenceType.FIRE: 5,
            EssenceType.WOOD: 3,
            EssenceType.WATER: 2
        })
        game_map.create_region(
            "青峰山脉",
            "连绵起伏，直插云霄。此地土行灵气深厚，金行次之，乃是修炼土系功法和寻找天材地宝的胜地。",
            essence,
            terrain_coords[TileType.MOUNTAIN]
        )
    
    # 万丈雪峰 (雪山)
    if TileType.SNOW_MOUNTAIN in terrain_coords:
        essence = Essence({
            EssenceType.WATER: 7,  # 水行主属性，但低于洞府的10
            EssenceType.GOLD: 6,   # 金行次要，但低于洞府的10
            EssenceType.EARTH: 6,
            EssenceType.FIRE: 1,
            EssenceType.WOOD: 2
        })
        game_map.create_region(
            "万丈雪峰",
            "雪峰皑皑，寒风刺骨。此地水行与金行灵气并重，是修炼冰系神通和淬炼法宝的绝佳之地。",
            essence,
            terrain_coords[TileType.SNOW_MOUNTAIN]
        )
    
    # 碧野千里 (草原)
    if TileType.GRASSLAND in terrain_coords:
        essence = Essence({
            EssenceType.WOOD: 5,  # 木行属性适中
            EssenceType.EARTH: 5,  # 土行属性适中
            EssenceType.WATER: 5,
            EssenceType.GOLD: 3,
            EssenceType.FIRE: 4
        })
        game_map.create_region(
            "碧野千里",
            "芳草萋萋，一望无际。此地木土并重，灵气平和，是修炼基础功法和放牧灵兽的理想之地。",
            essence,
            terrain_coords[TileType.GRASSLAND]
        )
    
    # 青云林海 (森林)
    if TileType.FOREST in terrain_coords:
        essence = Essence({
            EssenceType.WOOD: 7,  # 木行主属性，但低于洞府的10
            EssenceType.WATER: 4,
            EssenceType.EARTH: 4,
            EssenceType.GOLD: 3,
            EssenceType.FIRE: 3
        })
        game_map.create_region(
            "青云林海",
            "古树参天，绿意盎然。此地木行灵气浓郁，是修炼木系功法、采集灵草和驯服林间灵兽的宝地。",
            essence,
            terrain_coords[TileType.FOREST]
        )
    
    # 炎狱火山 (火山)
    if TileType.VOLCANO in terrain_coords:
        essence = Essence({
            EssenceType.FIRE: 8,  # 火行主属性，但低于洞府的10
            EssenceType.EARTH: 7,
            EssenceType.GOLD: 4,
            EssenceType.WATER: 1,
            EssenceType.WOOD: 1
        })
        game_map.create_region(
            "炎狱火山",
            "烈焰冲天，岩浆奔流。此地火行灵气达到极致，是修炼火系神通和锻造法宝的圣地，常人不可近。",
            essence,
            terrain_coords[TileType.VOLCANO]
        )
    
    # 为每个2*2城市、洞穴和遗迹创建独立区域
    _create_city_regions(game_map)
    _create_wuxing_caves_regions(game_map)
    _create_ruins_regions(game_map)
    

    

    
    # 沃土良田 (农田)
    if TileType.FARM in terrain_coords:
        essence = Essence({
            EssenceType.WOOD: 6,  # 木行属性较强
            EssenceType.EARTH: 6,  # 土行属性较强
            EssenceType.WATER: 6,
            EssenceType.GOLD: 2,
            EssenceType.FIRE: 3
        })
        game_map.create_region(
            "沃土良田",
            "土地肥沃，五谷丰登。此地木土并重，水行充沛，是种植灵药和培育灵植的理想之地。",
            essence,
            terrain_coords[TileType.FARM]
        )
    
    # 平原地带 (平原)
    if TileType.PLAIN in terrain_coords:
        essence = Essence({
            EssenceType.EARTH: 5,
            EssenceType.WOOD: 4,
            EssenceType.WATER: 4,
            EssenceType.GOLD: 3,
            EssenceType.FIRE: 3
        })
        game_map.create_region(
            "平原地带",
            "地势平坦，灵气平和。此地五行均衡，是初学修炼者打基础和建立宗门的理想之地。",
            essence,
            terrain_coords[TileType.PLAIN]
        )
    
    # 迷雾沼泽 (沼泽)
    if TileType.SWAMP in terrain_coords:
        essence = Essence({
            EssenceType.WATER: 6,  # 水行属性较强
            EssenceType.WOOD: 5,   # 木行属性适中
            EssenceType.EARTH: 5,
            EssenceType.FIRE: 2,
            EssenceType.GOLD: 3
        })
        game_map.create_region(
            "迷雾沼泽",
            "雾气缭绕，泥泞不堪。此地水木灵气浓郁，但瘴气丛生，是修炼毒功和寻找奇异灵草的危险之地。",
            essence,
            terrain_coords[TileType.SWAMP]
        )

def _create_city_regions(game_map: Map):
    """为每个2*2城市创建独立区域"""
    cities = [
        {"name": "青云城", "base_x": 34, "base_y": 21, "description": "繁华都市，人烟稠密，商贾云集。此地金行灵气较为集中，是交易天材地宝、寻找机缘的重要场所。"},
        {"name": "沙月城", "base_x": 14, "base_y": 19, "description": "沙漠绿洲中的贸易重镇，各路商队在此集结。金行灵气充沛，是修士补给和交流的重要据点。"},
        {"name": "翠林城", "base_x": 54, "base_y": 14, "description": "森林深处的修仙重镇，木行灵气与金行灵气并重。众多修士在此栖居，是修炼和炼宝的理想之地。"}
    ]
    
    for city in cities:
        base_x, base_y = city["base_x"], city["base_y"]
        city_coords = []
        
        for dx in range(2):
            for dy in range(2):
                x, y = base_x + dx, base_y + dy
                if game_map.is_in_bounds(x, y):
                    city_coords.append((x, y))
        
        essence = Essence({
            EssenceType.GOLD: 6,
            EssenceType.EARTH: 5,
            EssenceType.WOOD: 5,
            EssenceType.WATER: 4,
            EssenceType.FIRE: 4
        })
        
        game_map.create_region(
            city["name"],
            city["description"],
            essence,
            city_coords
        )

def _create_wuxing_caves_regions(game_map: Map):
    """为每个2*2五行洞府创建独立区域"""
    wuxing_caves = [
        {"name": "太白金府", "base_x": 26, "base_y": 12, "element": EssenceType.GOLD, 
         "description": "青峰山脉深处的金行洞府，金精气凝，刀剑鸣音不绝，乃金系修士的最高圣地。"},
        {"name": "青木洞天", "base_x": 48, "base_y": 18, "element": EssenceType.WOOD, 
         "description": "青云林海中的木行洞府，生机盎然，灵药遍地，乃木系修士的最高圣地。"},
        {"name": "玄水秘境", "base_x": 67, "base_y": 25, "element": EssenceType.WATER, 
         "description": "无边碧海深处的水行洞府，碧波万里，水精凝神，乃水系修士的最高圣地。"},
        {"name": "离火洞府", "base_x": 50, "base_y": 33, "element": EssenceType.FIRE, 
         "description": "炎狱火山旁的火行洞府，烈焰冲天，真火精纯，乃火系修士的最高圣地。"},
        {"name": "厚土玄宫", "base_x": 30, "base_y": 16, "element": EssenceType.EARTH, 
         "description": "青峰山脉的土行洞府，厚德载物，山岳共鸣，乃土系修士的最高圣地。"}
    ]
    
    for cave in wuxing_caves:
        base_x, base_y = cave["base_x"], cave["base_y"]
        cave_coords = []
        
        for dx in range(2):
            for dy in range(2):
                x, y = base_x + dx, base_y + dy
                if game_map.is_in_bounds(x, y):
                    cave_coords.append((x, y))
        
        # 每个洞府的主属性灵气为10（最高值），其他属性较低
        essence_config = {essence_type: 2 for essence_type in EssenceType}
        essence_config[cave["element"]] = 10  # 主属性达到最高值
        
        essence = Essence(essence_config)
        
        game_map.create_region(
            cave["name"],
            cave["description"],
            essence,
            cave_coords
        )

def _create_ruins_regions(game_map: Map):
    """为每个2*2遗迹创建独立区域"""
    ruins = [
        {"name": "古越遗迹", "base_x": 25, "base_y": 40, "description": "雨林深处的上古遗迹，古藤缠绕，木行灵气与金行灵气交融。蕴藏古老功法与灵药配方。"},
        {"name": "沧海遗迹", "base_x": 66, "base_y": 47, "description": "沉没在海中的远古文明遗迹，水行灵气浓郁，潮汐间偶有宝物现世。"}
    ]
    
    for ruin in ruins:
        base_x, base_y = ruin["base_x"], ruin["base_y"]
        ruin_coords = []
        
        for dx in range(2):
            for dy in range(2):
                x, y = base_x + dx, base_y + dy
                if game_map.is_in_bounds(x, y):
                    ruin_coords.append((x, y))
        
        # 根据遗迹位置调整灵气配置
        if ruin["name"] == "古越遗迹":  # 雨林深处
            essence = Essence({
                EssenceType.WOOD: 8,
                EssenceType.GOLD: 6,
                EssenceType.WATER: 5,
                EssenceType.EARTH: 4,
                EssenceType.FIRE: 3
            })
        else:  # 沧海遗迹，海中
            essence = Essence({
                EssenceType.WATER: 9,
                EssenceType.GOLD: 6,
                EssenceType.EARTH: 3,
                EssenceType.WOOD: 3,
                EssenceType.FIRE: 2
            })
        
        game_map.create_region(
            ruin["name"],
            ruin["description"],
            essence,
            ruin_coords
        )

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
