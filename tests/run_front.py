import os
import sys
import random
from typing import List, Tuple

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
    for y in range(height):
        for x in range(0, desert_w):
            game_map.create_tile(x, y, TileType.DESERT)
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
    for y in range(height - south_band, height):
        for x in range(width):
            game_map.create_tile(x, y, TileType.RAINFOREST)

    # 5) 最东海域（右侧宽带），最后铺海以覆盖前面的地形；随后在海中造岛
    sea_band_w = max(3, width // 6)
    sea_x0 = width - sea_band_w
    for y in range(height):
        for x in range(sea_x0, width):
            game_map.create_tile(x, y, TileType.SEA)
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

    # 7) 中部山脉：几条短链（避开海域和上下带）
    for _ in range(random.randint(2, 4)):
        length = random.randint(6, 12)
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

