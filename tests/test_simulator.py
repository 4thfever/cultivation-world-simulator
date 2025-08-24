import random

from src.sim.simulator import Simulator
from src.classes.avatar import Avatar, Gender
from src.classes.calendar import Month, Year
from src.classes.world import World
from src.classes.tile import Map, TileType
from src.classes.action import Move


def test_simulator_step_moves_avatar_and_sets_tile():
    # 固定随机种子，确保决定的移动是可预测的
    random.seed(0)

    # 构建 3x3 地图并填充地块
    game_map = Map(width=3, height=3)
    for x in range(3):
        for y in range(3):
            game_map.create_tile(x, y, TileType.PLAIN)

    world = World(map=game_map)

    # 将角色放在地图中心，避免越界
    avatar = Avatar(
        world=world,
        name="Tester",
        id=1,
        birth_month=Month.JANUARY,
        birth_year=Year(2000),
        age=20,
        gender=Gender.MALE,
        pos_x=1,
        pos_y=1,
    )


    sim = Simulator()
    sim.avatars.append(avatar)

    # 执行一步模拟
    sim.step()

    # 断言位置在边界内
    assert 0 <= avatar.pos_x < game_map.width
    assert 0 <= avatar.pos_y < game_map.height

    # 断言 tile 已正确设置且与位置一致
    assert avatar.tile is not None
    assert avatar.tile.x == avatar.pos_x
    assert avatar.tile.y == avatar.pos_y

