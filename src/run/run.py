import random
import asyncio
import sys
import os
from typing import List, Tuple, Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# 依赖项目内部模块
from src.front.front import Front
from src.sim.simulator import Simulator
from src.classes.world import World
from src.classes.tile import Map, TileType
from src.classes.avatar import Avatar, Gender
from src.classes.calendar import Month, Year, MonthStamp, create_month_stamp
from src.classes.action import Move
from src.classes.essence import Essence, EssenceType
from src.classes.cultivation import CultivationProgress
from src.classes.root import Root
from src.classes.age import Age
from src.run.create_map import create_cultivation_world_map
from src.utils.names import get_random_name
from src.utils.id_generator import get_avatar_id


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


def make_avatars(world: World, count: int = 12, current_month_stamp: MonthStamp = MonthStamp(100 * 12)) -> dict[str, Avatar]:
    avatars: dict[str, Avatar] = {}
    width, height = world.map.width, world.map.height
    for i in range(count):
        # 随机生成年龄，范围从16到60岁
        age_years = random.randint(16, 60)
        # 根据当前时间戳和年龄计算出生时间戳
        birth_month_stamp = current_month_stamp - age_years * 12 + random.randint(0, 11)  # 在出生年内随机选择月份
        gender = random_gender()
        # 使用仙侠风格的随机名字
        name = get_random_name(gender)
        
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
            id=get_avatar_id(),
            birth_month_stamp=MonthStamp(birth_month_stamp),
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


async def main():
    # 为了每次更丰富，使用随机种子；如需复现可将 seed 固定

    game_map = create_cultivation_world_map()
    world = World(map=game_map, month_stamp=create_month_stamp(Year(100), Month.JANUARY))

    # 创建模拟器
    sim = Simulator(world)
    
    # 创建角色，传入当前年份确保年龄与生日匹配
    sim.avatars.update(make_avatars(world, count=2, current_month_stamp=world.month_stamp))

    front = Front(
        simulator=sim,
        tile_size=19,  # 减小20%的tile大小 (24 * 0.8 ≈ 19)
        margin=8,
        step_interval_ms=350,
        window_title="Cultivation World — Front Demo",
        sidebar_width=350,  # 新增：设置侧边栏宽度
    )
    await front.run_async()


if __name__ == "__main__":
    asyncio.run(main())

