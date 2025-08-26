import os
import sys
import random
import uuid
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
from create_map import create_cultivation_world_map


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

def random_gender() -> Gender:
    return Gender.MALE if random.random() < 0.5 else Gender.FEMALE


def make_avatars(world: World, count: int = 12, current_year: Year = Year(100)) -> dict[str, Avatar]:
    avatars: dict[str, Avatar] = {}
    width, height = world.map.width, world.map.height
    for i in range(count):
        name = f"NPC{i+1:03d}"
        # 随机生成年龄，范围从16到60岁
        age_years = random.randint(16, 60)
        # 根据当前年份和年龄计算出生年份
        birth_year = current_year - age_years
        birth_month = random.choice(list(Month))
        gender = random_gender()
        
        # 随机生成level，范围从0到120（对应四个大境界）
        level = random.randint(0, 120)
        cultivation_progress = CultivationProgress(level)
        
        # 创建Age实例，传入年龄
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
            id=str(uuid.uuid4()),
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
        avatars[avatar.id] = avatar
    return avatars


def main():
    # 为了每次更丰富，使用随机种子；如需复现可将 seed 固定

    game_map = create_cultivation_world_map()
    world = World(map=game_map)

    # 设置模拟器从第100年开始
    sim = Simulator(world)
    sim.year = Year(100)  # 设置初始年份为100年
    sim.month = Month.JANUARY  # 设置初始月份为1月
    
    # 创建角色，传入当前年份确保年龄与生日匹配
    sim.avatars.update(make_avatars(world, count=14, current_year=sim.year))

    front = Front(
        simulator=sim,
        tile_size=19,  # 减小20%的tile大小 (24 * 0.8 ≈ 19)
        margin=8,
        step_interval_ms=350,
        window_title="Cultivation World — Front Demo",
        sidebar_width=350,  # 新增：设置侧边栏宽度
    )
    front.run()


if __name__ == "__main__":
    main()

