import os
import sys
import random
from typing import List, Tuple, Dict, Any

# 将项目根目录加入 Python 路径，确保可以导入 `src` 包
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 依赖项目内部模块
from src.front.front import Front
from src.sim.simulator import Simulator
from src.classes.world import World
from src.classes.tile import Map, TileType
from src.classes.avatar import Avatar, Gender
from src.classes.calendar import Month, Year
from src.classes.action import Move
from src.classes.essence import Essence, EssenceType
from src.classes.cultivation import CultivationProgress
from src.classes.root import Root
from src.classes.age import Age


def clamp(value: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, value))


def circle_points(cx: int, cy: int, r: int, width: int, height: int) -> List[Tuple[int, int]]:
    pts: List[Tuple[int, int]] = []
    r2 = r * r
    for y in range(clamp(cy - r, 0, height - 1), clamp(cy + r, 0, height - 1) + 1):
        for x in range(clamp(cx - r, 0, width - 1), clamp(cx + r, 0, width - 1) + 1):
            if (x - cx) * (x - cx) + (y - cy) * (y - cy) <= r2:
                pts.append((x, y))
    return pts


def build_rich_random_map(width: int = 50, height: int = 35, *, seed: int | None = None) -> Map:
    if seed is not None:
        random.seed(seed)

    game_map = Map(width=width, height=height)

    # 1) 底色：平原
    for y in range(height):
        for x in range(width):
            game_map.create_tile(x, y, TileType.PLAIN)

    # 2) 西部大漠（左侧宽带），先铺设便于后续北/南带覆盖
    desert_w = max(6, width // 6)  # 增加沙漠宽度
    desert_tiles: List[Tuple[int, int]] = []
    for y in range(height):
        for x in range(0, desert_w):
            game_map.create_tile(x, y, TileType.DESERT)
            desert_tiles.append((x, y))

    # 3) 北部雪山与冰原（顶部宽带，覆盖整宽度）
    north_band = max(4, height // 6)  # 增加北部带宽度
    snow_mountain_tiles: List[Tuple[int, int]] = []
    glacier_tiles: List[Tuple[int, int]] = []
    for y in range(0, north_band):
        for x in range(width):
            game_map.create_tile(x, y, TileType.SNOW_MOUNTAIN)
            snow_mountain_tiles.append((x, y))
    # 局部冰川簇
    for _ in range(random.randint(3, 5)):  # 增加冰川数量
        cx = random.randint(1, width - 2)
        cy = random.randint(0, north_band - 1)
        r = random.randint(1, 3)  # 增加冰川半径
        for x, y in circle_points(cx, cy, r, width, height):
            if y < north_band:
                game_map.create_tile(x, y, TileType.GLACIER)
                glacier_tiles.append((x, y))

    # 4) 南部热带雨林（底部宽带，覆盖整宽度）
    south_band = max(4, height // 6)  # 增加南部带宽度
    rainforest_tiles: List[Tuple[int, int]] = []
    for y in range(height - south_band, height):
        for x in range(width):
            game_map.create_tile(x, y, TileType.RAINFOREST)
            rainforest_tiles.append((x, y))

    # 5) 最东海域（右侧宽带），最后铺海以覆盖前面的地形；随后在海中造岛
    sea_band_w = max(4, width // 7)  # 增加海域宽度
    sea_x0 = width - sea_band_w
    sea_tiles: List[Tuple[int, int]] = []
    for y in range(height):
        for x in range(sea_x0, width):
            game_map.create_tile(x, y, TileType.SEA)
            sea_tiles.append((x, y))
    # 岛屿：在海域内生成若干小岛（平原/森林）
    for _ in range(random.randint(4, 7)):  # 增加岛屿数量
        cx = random.randint(sea_x0, width - 2)
        cy = random.randint(1, height - 2)
        r = random.randint(1, 3)  # 增加岛屿半径
        kind = random.choice([TileType.PLAIN, TileType.FOREST])
        for x, y in circle_points(cx, cy, r, width, height):
            if x >= sea_x0:
                game_map.create_tile(x, y, kind)

    # 6) 若干湖泊（水域圆斑，限制在中部非海域）
    for _ in range(random.randint(4, 7)):  # 增加湖泊数量
        cx = random.randint(max(2, desert_w + 1), sea_x0 - 2)
        cy = random.randint(north_band + 1, height - south_band - 2)
        r = random.randint(1, 4)  # 增加湖泊半径
        for x, y in circle_points(cx, cy, r, width, height):
            if x < sea_x0:
                game_map.create_tile(x, y, TileType.WATER)

    # 7) 中部山脉：聚集成为横向山脉群（避开海域和上下带，左移）
    mountain_tiles: List[Tuple[int, int]] = []
    # 左移山脉生成范围，从沙漠边缘开始，但不要延伸到太右边
    mountain_end_x = sea_x0 - max(5, width // 10)  # 留出更多空间给东部
    
    # 选择山脉中心区域，让山脉在这个区域内聚集
    mountain_center_x = (desert_w + mountain_end_x) // 2
    mountain_center_y = (north_band + height - south_band) // 2
    
    # 生成多条横向山脉链，形成山脉群
    mountain_chains = random.randint(3, 5)  # 3-5条山脉链
    for chain in range(mountain_chains):
        # 每条山脉链的起始位置在中心区域附近
        start_x = mountain_center_x + random.randint(-3, 3)
        start_y = mountain_center_y + random.randint(-2, 2)
        
        # 山脉链长度
        chain_length = random.randint(12, 20)  # 增加山脉长度
        
        # 主要方向：横向为主，允许小幅上下摆动
        main_dx = 1 if random.random() < 0.5 else -1  # 主要横向方向
        main_dy = 0  # 主要垂直方向为0
        
        x, y = start_x, start_y
        
        for step in range(chain_length):
            if 0 <= x < mountain_end_x and north_band <= y < height - south_band:
                game_map.create_tile(x, y, TileType.MOUNTAIN)
                mountain_tiles.append((x, y))
                
                # 随机添加分支山脉，增加聚集效果
                if random.random() < 0.3:
                    branch_length = random.randint(2, 6)
                    bx, by = x, y
                    for _ in range(branch_length):
                        # 分支方向：倾向于向中心聚集
                        if bx < mountain_center_x:
                            branch_dx = random.choice([0, 1])
                        elif bx > mountain_center_x:
                            branch_dx = random.choice([0, -1])
                        else:
                            branch_dx = random.choice([-1, 0, 1])
                        
                        if by < mountain_center_y:
                            branch_dy = random.choice([0, 1])
                        elif by > mountain_center_y:
                            branch_dy = random.choice([0, -1])
                        else:
                            branch_dy = random.choice([-1, 0, 1])
                        
                        bx += branch_dx
                        by += branch_dy
                        
                        if (0 <= bx < mountain_end_x and north_band <= by < height - south_band and
                            (bx, by) not in mountain_tiles):
                            game_map.create_tile(bx, by, TileType.MOUNTAIN)
                            mountain_tiles.append((bx, by))
            
            # 主要方向移动
            x += main_dx
            
            # 垂直方向：允许小幅摆动，但倾向于回归中心线
            if random.random() < 0.7:  # 70%概率向中心回归
                if y > mountain_center_y:
                    y -= 1
                elif y < mountain_center_y:
                    y += 1
            else:  # 30%概率随机摆动
                y += random.choice([-1, 0, 1])
            
            # 确保y在有效范围内
            y = max(north_band, min(height - south_band - 1, y))

    # 8) 中部森林：几个圆斑（调整范围与山脉一致）
    for _ in range(random.randint(5, 9)):  # 增加森林数量
        cx = random.randint(desert_w + 1, mountain_end_x - 2)
        cy = random.randint(north_band + 1, height - south_band - 2)
        r = random.randint(2, 5)  # 增加森林半径
        for x, y in circle_points(cx, cy, r, width, height):
            game_map.create_tile(x, y, TileType.FOREST)
    
    # 8.5) 火山：在中央山脉附近生成一个火山
    volcano_tiles: List[Tuple[int, int]] = []
    # 在中央山脉的边缘附近生成火山，避免覆盖重要山脉
    # 选择山脉区域的边缘位置
    volcano_edge_choices = []
    
    # 检查山脉区域的四个边缘
    if mountain_center_x > desert_w + 5:  # 左边缘
        volcano_edge_choices.append((mountain_center_x - 3, mountain_center_y))
    if mountain_center_x < mountain_end_x - 5:  # 右边缘
        volcano_edge_choices.append((mountain_center_x + 3, mountain_center_y))
    if mountain_center_y > north_band + 5:  # 上边缘
        volcano_edge_choices.append((mountain_center_x, mountain_center_y - 3))
    if mountain_center_y < height - south_band - 5:  # 下边缘
        volcano_edge_choices.append((mountain_center_x, mountain_center_y + 3))
    
    # 如果没有合适的边缘位置，选择山脉区域内的非山脉位置
    if not volcano_edge_choices:
        for attempt in range(10):
            vx = mountain_center_x + random.randint(-4, 4)
            vy = mountain_center_y + random.randint(-4, 4)
            if (0 <= vx < mountain_end_x and north_band <= vy < height - south_band and
                game_map.get_tile(vx, vy).type != TileType.MOUNTAIN):
                volcano_edge_choices.append((vx, vy))
                break
    
    # 如果还是没有找到合适位置，就在山脉中心附近找一个
    if not volcano_edge_choices:
        volcano_edge_choices.append((mountain_center_x, mountain_center_y))
    
    # 选择火山位置
    volcano_center_x, volcano_center_y = random.choice(volcano_edge_choices)
    volcano_radius = random.randint(2, 3)  # 减小火山半径
    
    # 生成火山，但避免覆盖重要的山脉
    for x, y in circle_points(volcano_center_x, volcano_center_y, volcano_radius, width, height):
        if (0 <= x < mountain_end_x and north_band <= y < height - south_band):
            current_tile = game_map.get_tile(x, y)
            # 只在非山脉地形上生成火山，或者在山脉边缘生成
            if current_tile.type != TileType.MOUNTAIN or random.random() < 0.3:
                game_map.create_tile(x, y, TileType.VOLCANO)
                volcano_tiles.append((x, y))

    # 8.6) 草原：在平原区域生成一些草原
    grassland_tiles: List[Tuple[int, int]] = []
    for _ in range(random.randint(4, 7)):  # 增加草原数量
        cx = random.randint(desert_w + 1, mountain_end_x - 2)
        cy = random.randint(north_band + 1, height - south_band - 2)
        r = random.randint(2, 5)  # 增加草原半径
        for x, y in circle_points(cx, cy, r, width, height):
            if x < sea_x0:
                current_tile = game_map.get_tile(x, y)
                if current_tile.type == TileType.PLAIN:  # 只在平原上生成草原
                    game_map.create_tile(x, y, TileType.GRASSLAND)
                    grassland_tiles.append((x, y))

    # 8.7) 沼泽：在水域附近生成一些沼泽
    swamp_tiles: List[Tuple[int, int]] = []
    for _ in range(random.randint(3, 6)):  # 增加沼泽数量
        cx = random.randint(desert_w + 1, sea_x0 - 2)
        cy = random.randint(north_band + 1, height - south_band - 2)
        r = random.randint(1, 3)  # 增加沼泽半径
        for x, y in circle_points(cx, cy, r, width, height):
            if x < sea_x0:
                # 检查周围是否有水域
                has_water_nearby = False
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        nx, ny = x + dx, y + dy
                        if game_map.is_in_bounds(nx, ny):
                            nearby_tile = game_map.get_tile(nx, ny)
                            if nearby_tile.type in (TileType.WATER, TileType.SEA):
                                has_water_nearby = True
                                break
                    if has_water_nearby:
                        break
                
                if has_water_nearby:
                    current_tile = game_map.get_tile(x, y)
                    if current_tile.type in (TileType.PLAIN, TileType.GRASSLAND):
                        game_map.create_tile(x, y, TileType.SWAMP)
                        swamp_tiles.append((x, y))

    # 8.8) 洞穴：在山脉附近生成一些洞穴
    cave_tiles: List[Tuple[int, int]] = []
    for _ in range(random.randint(3, 6)):  # 增加洞穴数量
        cx = random.randint(desert_w + 1, mountain_end_x - 1)
        cy = random.randint(north_band + 1, height - south_band - 2)
        # 检查周围是否有山脉
        has_mountain_nearby = False
        for dx in [-2, -1, 0, 1, 2]:
            for dy in [-2, -1, 0, 1, 2]:
                nx, ny = cx + dx, cy + dy
                if game_map.is_in_bounds(nx, ny):
                    nearby_tile = game_map.get_tile(nx, ny)
                    if nearby_tile.type == TileType.MOUNTAIN:
                        has_mountain_nearby = True
                        break
            if has_mountain_nearby:
                break
        
        if has_mountain_nearby:
            current_tile = game_map.get_tile(cx, cy)
            if current_tile.type in (TileType.PLAIN, TileType.GRASSLAND):
                game_map.create_tile(cx, cy, TileType.CAVE)
                cave_tiles.append((cx, cy))

    # 8.9) 遗迹：随机在一些地方生成古代遗迹
    ruins_tiles: List[Tuple[int, int]] = []
    for _ in range(random.randint(3, 5)):  # 增加遗迹数量
        cx = random.randint(desert_w + 1, sea_x0 - 2)
        cy = random.randint(north_band + 1, height - south_band - 2)
        current_tile = game_map.get_tile(cx, cy)
        if current_tile.type in (TileType.PLAIN, TileType.GRASSLAND, TileType.DESERT):
            game_map.create_tile(cx, cy, TileType.RUINS)
            ruins_tiles.append((cx, cy))

    # 9) 城市：2~4个，2x2格子，尽量落在非极端地形
    cities = 0
    attempts = 0
    city_positions = []  # 记录城市位置用于后续生成农田
    city_tiles = []  # 记录所有城市格子
    
    while cities < random.randint(2, 4) and attempts < 300:  # 增加尝试次数
        attempts += 1
        # 选择城市左上角位置
        x = random.randint(0, width - 2)  # 确保有2x2的空间
        y = random.randint(0, height - 2)
        
        # 检查2x2区域是否都适合建城
        can_build_city = True
        for dx in range(2):
            for dy in range(2):
                nx, ny = x + dx, y + dy
                if not game_map.is_in_bounds(nx, ny):
                    can_build_city = False
                    break
                t = game_map.get_tile(nx, ny)
                if t.type in (TileType.WATER, TileType.SEA, TileType.MOUNTAIN, TileType.GLACIER, 
                             TileType.SNOW_MOUNTAIN, TileType.DESERT, TileType.VOLCANO, TileType.SWAMP, 
                             TileType.CAVE, TileType.RUINS):
                    can_build_city = False
                    break
            if not can_build_city:
                break
        
        if can_build_city:
            # 创建2x2城市
            city_tiles_for_this_city = []
            for dx in range(2):
                for dy in range(2):
                    nx, ny = x + dx, y + dy
                    game_map.create_tile(nx, ny, TileType.CITY)
                    city_tiles_for_this_city.append((nx, ny))
                    city_tiles.append((nx, ny))
            city_positions.append((x, y))  # 记录左上角位置
            cities += 1

    # 8.10) 农田：在城市附近生成一些农田
    farm_tiles: List[Tuple[int, int]] = []
    
    # 在每个城市周围生成农田
    for city_x, city_y in city_positions:
        for _ in range(random.randint(4, 8)):  # 增加农田数量
            # 在城市周围3-6格范围内生成农田
            fx = city_x + random.randint(-6, 6)
            fy = city_y + random.randint(-6, 6)
            if game_map.is_in_bounds(fx, fy):
                current_tile = game_map.get_tile(fx, fy)
                if current_tile.type in (TileType.PLAIN, TileType.GRASSLAND):
                    game_map.create_tile(fx, fy, TileType.FARM)
                    farm_tiles.append((fx, fy))

    # 9.5) 生成一条横贯东西的长河（允许小幅上下摆动与随机加宽，避开沙漠和大海）
    river_tiles: List[Tuple[int, int]] = []
    # 选一条靠近中部的基准纬线，避开极北/极南带
    base_y = clamp(height // 2 + random.randint(-3, 3), north_band + 2, height - south_band - 3)
    y = base_y
    
    # 确保河流从西边开始，到东边结束，不断流
    for x in range(0, width):
        # 检查当前位置是否为沙漠或大海，如果是则跳过
        current_tile = game_map.get_tile(x, y)
        if current_tile.type in (TileType.DESERT, TileType.SEA):
            continue
            
        # 开凿主河道
        game_map.create_tile(x, y, TileType.WATER)
        river_tiles.append((x, y))
        
        # 随机加宽 1-2 格（上下其一或两个），但要避开沙漠和大海
        if random.random() < 0.6:  # 增加加宽概率
            # 选择加宽方向
            wide_directions = []
            if y > 0:
                wide_tile = game_map.get_tile(x, y - 1)
                if wide_tile.type not in (TileType.DESERT, TileType.SEA):
                    wide_directions.append(-1)
            if y < height - 1:
                wide_tile = game_map.get_tile(x, y + 1)
                if wide_tile.type not in (TileType.DESERT, TileType.SEA):
                    wide_directions.append(1)
            
            # 随机选择1-2个方向加宽
            if wide_directions:
                num_wide = random.randint(1, min(2, len(wide_directions)))
                selected_directions = random.sample(wide_directions, num_wide)
                for dy in selected_directions:
                    wy = y + dy
                    game_map.create_tile(x, wy, TileType.WATER)
                    river_tiles.append((x, wy))
        
        # 轻微摆动（-1, 0, 1），并缓慢回归基准线
        drift_choices = [-1, 0, 1]
        dy = random.choice(drift_choices)
        # 回归力：偏离过大时更倾向于向 base_y 靠拢
        if y - base_y > 3:
            dy = -1 if random.random() < 0.8 else dy
        elif base_y - y > 3:
            dy = 1 if random.random() < 0.8 else dy
        y = clamp(y + dy, north_band + 1, height - south_band - 2)

    # 11) 聚类函数：用于后续命名山脉/森林
    def find_type_clusters(tile_type: TileType) -> list[list[Tuple[int, int]]]:
        visited: set[Tuple[int, int]] = set()
        clusters: list[list[Tuple[int, int]]] = []
        for (tx, ty), t in game_map.tiles.items():
            if t.type is not tile_type or (tx, ty) in visited:
                continue
            stack = [(tx, ty)]
            visited.add((tx, ty))
            comp: list[Tuple[int, int]] = []
            while stack:
                cx, cy = stack.pop()
                comp.append((cx, cy))
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if not game_map.is_in_bounds(nx, ny) or (nx, ny) in visited:
                        continue
                    tt = game_map.get_tile(nx, ny)
                    if tt.type is tile_type:
                        visited.add((nx, ny))
                        stack.append((nx, ny))
            clusters.append(comp)
        return clusters

    # 高山：阈值较低，便于更多命名；森林：阈值更高，避免碎片
    all_mountain_clusters = find_type_clusters(TileType.MOUNTAIN)
    mountain_clusters = [c for c in all_mountain_clusters if len(c) >= 8]
    forest_clusters = [c for c in find_type_clusters(TileType.FOREST) if len(c) >= 12]

    # 组装所有地理信息到一个统一的配置 dict
    regions_cfg: List[Dict[str, Any]] = []
    if desert_tiles:
        regions_cfg.append({
            "name": "大漠", 
            "description": "西部荒漠地带", 
            "essence": Essence(density={
                EssenceType.EARTH: 8, 
                EssenceType.FIRE: 6, 
                EssenceType.GOLD: 4, 
                EssenceType.WOOD: 2, 
                EssenceType.WATER: 1
            }), 
            "tiles": desert_tiles
        })
    if sea_tiles:
        regions_cfg.append({
            "name": "东海", 
            "description": "最东边的大海", 
            "essence": Essence(density={
                EssenceType.WATER: 10, 
                EssenceType.EARTH: 3, 
                EssenceType.GOLD: 2, 
                EssenceType.WOOD: 1, 
                EssenceType.FIRE: 1
            }), 
            "tiles": sea_tiles
        })
    if rainforest_tiles:
        regions_cfg.append({
            "name": "南疆雨林", 
            "description": "南部潮湿炎热的雨林", 
            "essence": Essence(density={
                EssenceType.WOOD: 9, 
                EssenceType.WATER: 7, 
                EssenceType.FIRE: 5, 
                EssenceType.EARTH: 3, 
                EssenceType.GOLD: 2
            }), 
            "tiles": rainforest_tiles
        })
    if river_tiles:
        regions_cfg.append({
            "name": "大河", 
            "description": "发源内陆，奔流入海", 
            "essence": Essence(density={
                EssenceType.WATER: 8, 
                EssenceType.EARTH: 4, 
                EssenceType.WOOD: 3, 
                EssenceType.GOLD: 2, 
                EssenceType.FIRE: 1
            }), 
            "tiles": river_tiles
        })

    # 添加山脉region（提高金属性灵气）
    if mountain_tiles:
        regions_cfg.append({
            "name": "中央山脉", 
            "description": "横贯大陆的中央山脉，蕴含丰富的金属性灵气", 
            "essence": Essence(density={
                EssenceType.GOLD: 10,  # 提高金属性灵气
                EssenceType.EARTH: 9, 
                EssenceType.FIRE: 5, 
                EssenceType.WATER: 3, 
                EssenceType.WOOD: 2
            }), 
            "tiles": mountain_tiles
        })
    
    # 添加雪山region
    if snow_mountain_tiles:
        regions_cfg.append({
            "name": "北境雪山", 
            "description": "北部终年积雪的高山地带", 
            "essence": Essence(density={
                EssenceType.WATER: 9, 
                EssenceType.EARTH: 8, 
                EssenceType.GOLD: 6, 
                EssenceType.FIRE: 2, 
                EssenceType.WOOD: 1
            }), 
            "tiles": snow_mountain_tiles
        })
    
    # 添加冰川region
    if glacier_tiles:
        regions_cfg.append({
            "name": "极地冰川", 
            "description": "北部极寒的冰川地带", 
            "essence": Essence(density={
                EssenceType.WATER: 10, 
                EssenceType.EARTH: 7, 
                EssenceType.GOLD: 5, 
                EssenceType.FIRE: 1, 
                EssenceType.WOOD: 1
            }), 
            "tiles": glacier_tiles
        })
    
    # 添加火山region（火属性灵气最高）
    if volcano_tiles:
        regions_cfg.append({
            "name": "火山", 
            "description": "活跃的火山地带，火属性灵气极其浓郁", 
            "essence": Essence(density={
                EssenceType.FIRE: 10,  # 火属性灵气最高
                EssenceType.EARTH: 8, 
                EssenceType.GOLD: 6, 
                EssenceType.WATER: 2, 
                EssenceType.WOOD: 1
            }), 
            "tiles": volcano_tiles
        })
    
    # 添加草原region
    if grassland_tiles:
        regions_cfg.append({
            "name": "青青草原", 
            "description": "广阔的草原地带，适合放牧和修炼", 
            "essence": Essence(density={
                EssenceType.WOOD: 7, 
                EssenceType.EARTH: 6, 
                EssenceType.WATER: 5, 
                EssenceType.FIRE: 3, 
                EssenceType.GOLD: 2
            }), 
            "tiles": grassland_tiles
        })
    
    # 添加沼泽region
    if swamp_tiles:
        regions_cfg.append({
            "name": "迷雾沼泽", 
            "description": "危险的沼泽地带，瘴气弥漫但蕴含特殊灵药", 
            "essence": Essence(density={
                EssenceType.WATER: 8, 
                EssenceType.WOOD: 6, 
                EssenceType.EARTH: 5, 
                EssenceType.FIRE: 3, 
                EssenceType.GOLD: 2
            }), 
            "tiles": swamp_tiles
        })
    
    # 添加洞穴region
    if cave_tiles:
        regions_cfg.append({
            "name": "神秘洞穴", 
            "description": "隐藏在山脉中的神秘洞穴，可能藏有宝物", 
            "essence": Essence(density={
                EssenceType.EARTH: 9, 
                EssenceType.GOLD: 8, 
                EssenceType.FIRE: 4, 
                EssenceType.WATER: 3, 
                EssenceType.WOOD: 2
            }), 
            "tiles": cave_tiles
        })
    
    # 添加遗迹region
    if ruins_tiles:
        regions_cfg.append({
            "name": "古代遗迹", 
            "description": "上古时代留下的神秘遗迹，蕴含古老的力量", 
            "essence": Essence(density={
                EssenceType.GOLD: 9, 
                EssenceType.EARTH: 7, 
                EssenceType.FIRE: 6, 
                EssenceType.WATER: 5, 
                EssenceType.WOOD: 4
            }), 
            "tiles": ruins_tiles
        })
    
    # 添加农田region
    if farm_tiles:
        regions_cfg.append({
            "name": "良田", 
            "description": "肥沃的农田，为城市提供粮食", 
            "essence": Essence(density={
                EssenceType.WOOD: 8, 
                EssenceType.EARTH: 7, 
                EssenceType.WATER: 6, 
                EssenceType.FIRE: 3, 
                EssenceType.GOLD: 2
            }), 
            "tiles": farm_tiles
        })
    
    # 添加城市region
    if city_tiles:
        # 为每个城市创建单独的region
        city_names = ["长安", "洛阳", "建康", "临安", "大都", "金陵", "燕京", "成都"]
        city_name_index = 0
        
        # 按城市位置分组
        city_groups = []
        used_positions = set()
        
        for city_x, city_y in city_positions:
            if (city_x, city_y) not in used_positions:
                # 收集这个2x2城市的所有格子
                city_group = []
                for dx in range(2):
                    for dy in range(2):
                        nx, ny = city_x + dx, city_y + dy
                        city_group.append((nx, ny))
                        used_positions.add((nx, ny))
                city_groups.append(city_group)
        
        # 为每个城市创建region
        for i, city_group in enumerate(city_groups):
            if i < len(city_names):
                city_name = city_names[i]
            else:
                city_name = f"城市{i+1}"
            
            regions_cfg.append({
                "name": city_name, 
                "description": f"繁华的都市，人口密集，商业繁荣", 
                "essence": Essence(density={
                    EssenceType.GOLD: 9,  # 城市金属性灵气最高
                    EssenceType.FIRE: 8,  # 火属性（人气）也很高
                    EssenceType.EARTH: 7, 
                    EssenceType.WOOD: 6, 
                    EssenceType.WATER: 5
                }), 
                "tiles": city_group
            })

    for i, comp in enumerate(sorted(mountain_clusters, key=len, reverse=True), start=1):
        regions_cfg.append({
            "name": f"高山{i}", 
            "description": "山脉与高峰地带", 
            "essence": Essence(density={
                EssenceType.EARTH: 9, 
                EssenceType.GOLD: 7, 
                EssenceType.FIRE: 4, 
                EssenceType.WATER: 3, 
                EssenceType.WOOD: 2
            }), 
            "tiles": comp
        })
    for i, comp in enumerate(sorted(forest_clusters, key=len, reverse=True), start=1):
        regions_cfg.append({
            "name": f"大林{i}", 
            "description": "茂密幽深的森林", 
            "essence": Essence(density={
                EssenceType.WOOD: 8, 
                EssenceType.EARTH: 5, 
                EssenceType.WATER: 4, 
                EssenceType.FIRE: 2, 
                EssenceType.GOLD: 1
            }), 
            "tiles": comp
        })

    # 应用配置创建 Region，并把配置存到 map 上，方便前端/后续逻辑使用
    for r in regions_cfg:
        game_map.create_region(r["name"], r["description"], r["essence"], r["tiles"])
    geo_config: Dict[str, Any] = {"regions": regions_cfg}
    setattr(game_map, "geo_config", geo_config)

    return game_map


def random_gender() -> Gender:
    return Gender.MALE if random.random() < 0.5 else Gender.FEMALE


def make_avatars(world: World, count: int = 12) -> dict[int, Avatar]:
    avatars: dict[int, Avatar] = {}
    width, height = world.map.width, world.map.height
    for i in range(count):
        name = f"NPC{i+1:03d}"
        birth_year = Year(random.randint(1990, 2010))
        birth_month = random.choice(list(Month))
        age_years = random.randint(16, 60)
        gender = random_gender()
        
        # 随机生成level，范围从0到120（对应四个大境界）
        level = random.randint(0, 120)
        cultivation_progress = CultivationProgress(level)
        
        # 创建Age实例，传入年龄和境界
        age = Age(age_years)

        # 找一个非海域的出生点
        for _ in range(200):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            t = world.map.get_tile(x, y)
            if t.type not in (TileType.WATER, TileType.SEA, TileType.MOUNTAIN, TileType.VOLCANO, TileType.SWAMP, TileType.CAVE, TileType.RUINS):
                break
        else:
            x, y = random.randint(0, width - 1), random.randint(0, height - 1)

        avatar = Avatar(
            world=world,
            name=name,
            id=i + 1,
            birth_month=birth_month,
            birth_year=birth_year,
            age=age,
            gender=gender,
            cultivation_progress=cultivation_progress,
            pos_x=x,
            pos_y=y,
            root=random.choice(list(Root)),  # 随机选择灵根
        )
        avatar.tile = world.map.get_tile(x, y)
        avatar.bind_action(Move)
        avatars[i] = avatar
    return avatars


def main():
    # 为了每次更丰富，使用随机种子；如需复现可将 seed 固定
    # random.seed(42)

    width, height = 50, 35  # 使用新的默认尺寸
    game_map = build_rich_random_map(width=width, height=height)
    world = World(map=game_map)

    sim = Simulator()
    sim.avatars.update(make_avatars(world, count=14))

    front = Front(
        world=world,
        simulator=sim,
        tile_size=24,  # 稍微减小tile大小以适应更大的地图
        margin=8,
        step_interval_ms=350,
        window_title="Cultivation World — Front Demo",
        sidebar_width=350,  # 新增：设置侧边栏宽度
    )
    front.run()


if __name__ == "__main__":
    main()

