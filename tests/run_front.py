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


def build_rich_random_map(width: int = 30, height: int = 20, *, seed: int | None = None) -> Map:
    if seed is not None:
        random.seed(seed)

    game_map = Map(width=width, height=height)

    # 1) 底色：平原
    for y in range(height):
        for x in range(width):
            game_map.create_tile(x, y, TileType.PLAIN)

    # 2) 西部大漠（左侧宽带），先铺设便于后续北/南带覆盖
    desert_w = max(4, width // 5)
    desert_tiles: List[Tuple[int, int]] = []
    for y in range(height):
        for x in range(0, desert_w):
            game_map.create_tile(x, y, TileType.DESERT)
            desert_tiles.append((x, y))
    # 绿洲
    for _ in range(random.randint(2, 3)):
        cx = random.randint(1, max(1, desert_w - 1))
        cy = random.randint(2, height - 3)
        r = random.randint(1, 2)
        for x, y in circle_points(cx, cy, r, width, height):
            if x < desert_w:
                game_map.create_tile(x, y, TileType.WATER)

    # 3) 北部雪山与冰原（顶部宽带，覆盖整宽度）
    north_band = max(3, height // 5)
    for y in range(0, north_band):
        for x in range(width):
            game_map.create_tile(x, y, TileType.SNOW_MOUNTAIN)
    # 局部冰川簇
    for _ in range(random.randint(2, 3)):
        cx = random.randint(1, width - 2)
        cy = random.randint(0, north_band - 1)
        r = random.randint(1, 2)
        for x, y in circle_points(cx, cy, r, width, height):
            if y < north_band:
                game_map.create_tile(x, y, TileType.GLACIER)

    # 4) 南部热带雨林（底部宽带，覆盖整宽度）
    south_band = max(3, height // 5)
    rainforest_tiles: List[Tuple[int, int]] = []
    for y in range(height - south_band, height):
        for x in range(width):
            game_map.create_tile(x, y, TileType.RAINFOREST)
            rainforest_tiles.append((x, y))

    # 5) 最东海域（右侧宽带），最后铺海以覆盖前面的地形；随后在海中造岛
    sea_band_w = max(3, width // 6)
    sea_x0 = width - sea_band_w
    sea_tiles: List[Tuple[int, int]] = []
    for y in range(height):
        for x in range(sea_x0, width):
            game_map.create_tile(x, y, TileType.SEA)
            sea_tiles.append((x, y))
    # 岛屿：在海域内生成若干小岛（平原/森林）
    for _ in range(random.randint(3, 5)):
        cx = random.randint(sea_x0, width - 2)
        cy = random.randint(1, height - 2)
        r = random.randint(1, 2)
        kind = random.choice([TileType.PLAIN, TileType.FOREST])
        for x, y in circle_points(cx, cy, r, width, height):
            if x >= sea_x0:
                game_map.create_tile(x, y, kind)

    # 6) 若干湖泊（水域圆斑，限制在中部非海域）
    for _ in range(random.randint(3, 5)):
        cx = random.randint(max(2, desert_w + 1), sea_x0 - 2)
        cy = random.randint(north_band + 1, height - south_band - 2)
        r = random.randint(1, 3)
        for x, y in circle_points(cx, cy, r, width, height):
            if x < sea_x0:
                game_map.create_tile(x, y, TileType.WATER)

    # 7) 中部山脉：多条更长的链（避开海域和上下带）
    for _ in range(random.randint(6, 10)):
        length = random.randint(10, 20)
        x = random.randint(desert_w + 1, sea_x0 - 2)
        y = random.randint(north_band + 1, height - south_band - 2)
        dx, dy = random.choice([(1, 0), (1, 1), (1, -1)])
        for _ in range(length):
            if 0 <= x < sea_x0 and north_band <= y < height - south_band:
                game_map.create_tile(x, y, TileType.MOUNTAIN)
            x += dx
            y += dy

    # 8) 中部森林：几个圆斑
    for _ in range(random.randint(4, 7)):
        cx = random.randint(desert_w + 1, sea_x0 - 2)
        cy = random.randint(north_band + 1, height - south_band - 2)
        r = random.randint(2, 4)
        for x, y in circle_points(cx, cy, r, width, height):
            game_map.create_tile(x, y, TileType.FOREST)

    # 9) 城市：2~4个，尽量落在非极端地形
    cities = 0
    attempts = 0
    while cities < random.randint(2, 4) and attempts < 200:
        attempts += 1
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        t = game_map.get_tile(x, y)
        if t.type not in (TileType.WATER, TileType.SEA, TileType.MOUNTAIN, TileType.GLACIER, TileType.SNOW_MOUNTAIN, TileType.DESERT):
            game_map.create_tile(x, y, TileType.CITY)
            cities += 1

    # 10) 创建示例 Region（演示：底色可无 region；特意设立的带名字与描述）
    if desert_tiles:
        game_map.create_region("大漠", "西部荒漠地带", 40, desert_tiles)
    if sea_tiles:
        game_map.create_region("东海", "最东边的大海", 80, sea_tiles)
    if rainforest_tiles:
        game_map.create_region("南疆雨林", "南部潮湿炎热的雨林", 120, rainforest_tiles)

    # 9.5) 生成一条横贯东西的长河（允许小幅上下摆动与随机加宽）
    river_tiles: List[Tuple[int, int]] = []
    # 选一条靠近中部的基准纬线，避开极北/极南带
    base_y = clamp(height // 2 + random.randint(-2, 2), north_band + 1, height - south_band - 2)
    y = base_y
    for x in range(0, width):
        # 开凿主河道
        game_map.create_tile(x, y, TileType.WATER)
        river_tiles.append((x, y))
        # 随机加宽 1 格（上下其一）
        if random.random() < 0.45:
            wy = clamp(y + random.choice([-1, 1]), 0, height - 1)
            game_map.create_tile(x, wy, TileType.WATER)
            river_tiles.append((x, wy))
        # 轻微摆动（-1, 0, 1），并缓慢回归基准线
        drift_choices = [-1, 0, 1]
        dy = random.choice(drift_choices)
        # 回归力：偏离过大时更倾向于向 base_y 靠拢
        if y - base_y > 2:
            dy = -1 if random.random() < 0.7 else dy
        elif base_y - y > 2:
            dy = 1 if random.random() < 0.7 else dy
        y = clamp(y + dy, 1, height - 2)

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
        regions_cfg.append({"name": "大漠", "description": "西部荒漠地带", "qi": 40, "tiles": desert_tiles})
    if sea_tiles:
        regions_cfg.append({"name": "东海", "description": "最东边的大海", "qi": 80, "tiles": sea_tiles})
    if rainforest_tiles:
        regions_cfg.append({"name": "南疆雨林", "description": "南部潮湿炎热的雨林", "qi": 120, "tiles": rainforest_tiles})
    if river_tiles:
        regions_cfg.append({"name": "大河", "description": "发源内陆，奔流入海", "qi": 100, "tiles": river_tiles})

    for i, comp in enumerate(sorted(mountain_clusters, key=len, reverse=True), start=1):
        regions_cfg.append({"name": f"高山{i}", "description": "山脉与高峰地带", "qi": 110, "tiles": comp})
    for i, comp in enumerate(sorted(forest_clusters, key=len, reverse=True), start=1):
        regions_cfg.append({"name": f"大林{i}", "description": "茂密幽深的森林", "qi": 90, "tiles": comp})

    # 应用配置创建 Region，并把配置存到 map 上，方便前端/后续逻辑使用
    for r in regions_cfg:
        game_map.create_region(r["name"], r["description"], r["qi"], r["tiles"])
    geo_config: Dict[str, Any] = {"regions": regions_cfg}
    setattr(game_map, "geo_config", geo_config)

    return game_map


def random_gender() -> Gender:
    return Gender.MALE if random.random() < 0.5 else Gender.FEMALE


def make_avatars(world: World, count: int = 12) -> list[Avatar]:
    avatars: list[Avatar] = []
    width, height = world.map.width, world.map.height
    for i in range(count):
        name = f"NPC{i+1:03d}"
        birth_year = Year(random.randint(1990, 2010))
        birth_month = random.choice(list(Month))
        age = random.randint(16, 60)
        gender = random_gender()

        # 找一个非海域的出生点
        for _ in range(200):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            t = world.map.get_tile(x, y)
            if t.type not in (TileType.WATER, TileType.SEA, TileType.MOUNTAIN):
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
            pos_x=x,
            pos_y=y,
        )
        avatar.tile = world.map.get_tile(x, y)
        avatar.bind_action(Move)
        avatars.append(avatar)
    return avatars


def main():
    # 为了每次更丰富，使用随机种子；如需复现可将 seed 固定
    # random.seed(42)

    width, height = 36, 24
    game_map = build_rich_random_map(width=width, height=height)
    world = World(map=game_map)

    sim = Simulator()
    sim.avatars.extend(make_avatars(world, count=14))

    front = Front(
        world=world,
        simulator=sim,
        tile_size=28,
        margin=8,
        step_interval_ms=350,
        window_title="Cultivation World — Front Demo",
    )
    front.run()


if __name__ == "__main__":
    main()

