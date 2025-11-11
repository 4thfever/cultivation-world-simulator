import random
import asyncio
import sys
import os
from typing import List, Tuple, Dict, Any, Sequence, Optional

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# 依赖项目内部模块
from src.front.front import Front
from src.sim.simulator import Simulator
from src.sim.new_avatar import make_avatars
from src.classes.world import World
from src.classes.map import Map
from src.classes.tile import TileType
from src.classes.avatar import Avatar, Gender
from src.classes.calendar import Month, Year, MonthStamp, create_month_stamp
from src.classes.cultivation import CultivationProgress
from src.classes.root import Root
from src.classes.age import Age
from src.run.create_map import create_cultivation_world_map, add_sect_headquarters
from src.classes.name import get_random_name, get_random_name_for_sect
from src.utils.id_generator import get_avatar_id
from src.utils.config import CONFIG
from src.classes.sect import sects_by_id
from src.classes.alignment import Alignment
from src.run.log import get_logger
from src.classes.relation import Relation
from src.classes.technique import get_technique_by_sect, attribute_to_root


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


def sample_existed_sects(all_sects: Sequence, needed_sects: int) -> list:
    """
    按权重无放回抽样本局启用的宗门；当权重和为0时退回均匀无放回抽样。
    返回长度不超过 max_sects。
    """
    if needed_sects <= 0 or not all_sects:
        return []
    k = min(needed_sects, len(all_sects))
    pool = list(all_sects)
    base_weights = [max(0.0, s.weight) for s in pool]
    if sum(base_weights) <= 0:
        random.shuffle(pool)
        return pool[:k]
    result: list = []
    for _ in range(k):
        weights = [max(0.0, s.weight) for s in pool]
        chosen = random.choices(pool, weights=weights, k=1)[0]
        result.append(chosen)
        pool.remove(chosen)
    return result

def make_avatars(world: World, count: int = 12, current_month_stamp: MonthStamp = MonthStamp(100 * 12), existed_sects: Optional[List] = None) -> dict[str, Avatar]:
    # 迁移到 src/sim/new_avatar.py
    from src.sim.new_avatar import make_avatars as _new_make
    # 在地图上添加本局宗门总部（保持原行为）
    if existed_sects:
        add_sect_headquarters(world.map, existed_sects)
    return _new_make(world, count=count, current_month_stamp=current_month_stamp, existed_sects=existed_sects)


async def main():
    # 为了每次更丰富，使用随机种子；如需复现可将 seed 固定
    
    # 初始化日志系统（会自动清理旧日志）
    logger = get_logger()
    print(f"日志系统已初始化，日志文件：{logger.log_file_path}")

    game_map = create_cultivation_world_map()
    world = World(map=game_map, month_stamp=create_month_stamp(Year(100), Month.JANUARY))

    # 创建模拟器
    sim = Simulator(world)

    # 得到本局的宗门
    all_sects = list(sects_by_id.values())
    needed_sects = int(getattr(CONFIG.game, "sect_num", 0) or 0)
    existed_sects = sample_existed_sects(all_sects, needed_sects)
    
    # 创建角色，传入当前年份确保年龄与生日匹配，使用配置文件中的NPC数量
    all_avatars = make_avatars(world, count=CONFIG.game.init_npc_num, current_month_stamp=world.month_stamp, existed_sects=existed_sects)
    world.avatar_manager.avatars.update(all_avatars)

    front = Front(
        simulator=sim,
        step_interval_ms=750,
        window_title="Cultivation World — Front Demo",
        existed_sects=existed_sects,
    )
    await front.run_async()


if __name__ == "__main__":
    asyncio.run(main())

