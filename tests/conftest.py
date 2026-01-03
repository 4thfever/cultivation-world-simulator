import pytest
from unittest.mock import MagicMock

from src.classes.map import Map
from src.classes.tile import TileType
from src.classes.world import World
from src.classes.calendar import Month, Year, create_month_stamp
from src.classes.avatar import Avatar, Gender
from src.classes.age import Age
from src.classes.cultivation import Realm
from src.utils.id_generator import get_avatar_id
from src.classes.name import get_random_name

@pytest.fixture
def base_map():
    """创建一个 10x10 的全平原地图"""
    width, height = 10, 10
    game_map = Map(width=width, height=height)
    for x in range(width):
        for y in range(height):
            game_map.create_tile(x, y, TileType.PLAIN)
    return game_map

@pytest.fixture
def base_world(base_map):
    """创建一个基于 base_map 的世界，时间为 Year 1, Jan"""
    return World(map=base_map, month_stamp=create_month_stamp(Year(1), Month.JANUARY))

from src.classes.root import Root
from src.classes.alignment import Alignment

@pytest.fixture
def dummy_avatar(base_world):
    """创建一个位于 (0,0) 的标准男性练气期角色"""
    # 确保ID生成器重置或不冲突 (get_avatar_id 是随机UUID通常没问题)
    av = Avatar(
        world=base_world,
        name="TestDummy",
        id=get_avatar_id(),
        birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
        age=Age(20, Realm.Qi_Refinement),
        gender=Gender.MALE,
        pos_x=0,
        pos_y=0,
        root=Root.GOLD, # 固定灵根
        personas=[],    # 清空特质，避免随机效果
        alignment=Alignment.RIGHTEOUS # 固定阵营
    )
    
    # 赋予一个 Mock 武器，防止 get_avatar_info 报错
    av.weapon = MagicMock()
    av.weapon.get_detailed_info.return_value = "测试木剑（练气）"
    av.weapon_proficiency = 0.0
    
    return av

