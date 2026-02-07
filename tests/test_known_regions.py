"""
测试 Avatar._init_known_regions 的行为。

验证：
1. 无宗门的 avatar：known_regions 只包含当前位置的区域（如果有）
2. 有宗门的 avatar：known_regions 包含宗门驻地
"""
import pytest
from unittest.mock import MagicMock

from src.classes.environment.map import Map
from src.classes.environment.tile import TileType
from src.classes.core.world import World
from src.systems.time import Month, Year, create_month_stamp
from src.classes.core.avatar import Avatar, Gender
from src.classes.age import Age
from src.systems.cultivation import Realm
from src.classes.root import Root
from src.classes.alignment import Alignment
from src.classes.core.sect import sects_by_id
from src.classes.environment.sect_region import SectRegion
from src.classes.environment.region import NormalRegion
from src.utils.id_generator import get_avatar_id


@pytest.fixture
def world_with_sect_region():
    """创建一个带有宗门驻地的世界"""
    width, height = 10, 10
    game_map = Map(width=width, height=height)
    
    # 创建 tiles
    for x in range(width):
        for y in range(height):
            game_map.create_tile(x, y, TileType.PLAIN)
    
    # 获取一个真实的宗门（明心剑宗，id=1）
    sect = sects_by_id.get(1)
    assert sect is not None, "宗门 ID=1 应该存在"
    
    # 创建对应的 SectRegion
    sect_region = SectRegion(
        id=401,
        name="连霞山",
        desc="测试宗门驻地",
        cors=[(5, 5)],
        sect_name=sect.name,
        sect_id=sect.id
    )
    
    # 注册到 map
    game_map.regions[sect_region.id] = sect_region
    game_map.sect_regions[sect_region.id] = sect_region
    
    # 将区域绑定到 tile
    tile = game_map.get_tile(5, 5)
    tile.region = sect_region
    
    world = World(map=game_map, month_stamp=create_month_stamp(Year(1), Month.JANUARY))
    return world, sect, sect_region


@pytest.fixture
def world_with_normal_region():
    """创建一个带有普通区域的世界"""
    width, height = 10, 10
    game_map = Map(width=width, height=height)
    
    for x in range(width):
        for y in range(height):
            game_map.create_tile(x, y, TileType.PLAIN)
    
    # 创建普通区域
    normal_region = NormalRegion(
        id=101,
        name="测试区域",
        desc="一片普通的区域",
        cors=[(0, 0)]
    )
    
    game_map.regions[normal_region.id] = normal_region
    
    # 绑定到 tile
    tile = game_map.get_tile(0, 0)
    tile.region = normal_region
    
    world = World(map=game_map, month_stamp=create_month_stamp(Year(1), Month.JANUARY))
    return world, normal_region


class TestInitKnownRegions:
    """测试 Avatar._init_known_regions"""

    def test_avatar_without_sect_knows_current_region(self, world_with_normal_region):
        """无宗门的 avatar 应该知道当前位置的区域"""
        world, normal_region = world_with_normal_region
        
        avatar = Avatar(
            world=world,
            name="散修测试",
            id=get_avatar_id(),
            birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
            age=Age(20, Realm.Qi_Refinement),
            gender=Gender.MALE,
            pos_x=0,
            pos_y=0,
            root=Root.GOLD,
            alignment=Alignment.RIGHTEOUS,
            sect=None  # 散修
        )
        
        # 设置 tile（模拟正常初始化流程）
        avatar.tile = world.map.get_tile(0, 0)
        avatar._init_known_regions()
        
        assert normal_region.id in avatar.known_regions, (
            f"散修应该知道当前位置的区域，但 known_regions={avatar.known_regions}"
        )

    def test_avatar_with_sect_knows_headquarters(self, world_with_sect_region):
        """有宗门的 avatar 应该知道宗门驻地位置"""
        world, sect, sect_region = world_with_sect_region
        
        avatar = Avatar(
            world=world,
            name="宗门弟子测试",
            id=get_avatar_id(),
            birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
            age=Age(20, Realm.Qi_Refinement),
            gender=Gender.MALE,
            pos_x=0,
            pos_y=0,  # 不在宗门驻地
            root=Root.GOLD,
            alignment=Alignment.RIGHTEOUS,
            sect=sect  # 有宗门
        )
        
        # _init_known_regions 在 __post_init__ 中自动调用
        assert sect_region.id in avatar.known_regions, (
            f"宗门弟子应该知道宗门驻地位置，但 known_regions={avatar.known_regions}"
        )

    def test_avatar_without_sect_does_not_know_sect_region(self, world_with_sect_region):
        """无宗门的 avatar 不应该自动知道宗门驻地"""
        world, sect, sect_region = world_with_sect_region
        
        avatar = Avatar(
            world=world,
            name="散修测试",
            id=get_avatar_id(),
            birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
            age=Age(20, Realm.Qi_Refinement),
            gender=Gender.MALE,
            pos_x=0,
            pos_y=0,
            root=Root.GOLD,
            alignment=Alignment.RIGHTEOUS,
            sect=None  # 散修
        )
        
        # 散修不应该知道宗门驻地（除非在那个位置）
        assert sect_region.id not in avatar.known_regions, (
            f"散修不应该自动知道宗门驻地，但 known_regions={avatar.known_regions}"
        )

    def test_avatar_knows_only_their_sect_headquarters(self, world_with_sect_region):
        """avatar 只应该知道自己宗门的驻地，不知道其他宗门"""
        world, sect, sect_region = world_with_sect_region
        
        # 添加另一个宗门的驻地
        other_sect = sects_by_id.get(2)  # 百兽宗
        assert other_sect is not None
        
        other_sect_region = SectRegion(
            id=402,
            name="玄灵洞",
            desc="另一个宗门驻地",
            cors=[(7, 7)],
            sect_name=other_sect.name,
            sect_id=other_sect.id
        )
        world.map.regions[other_sect_region.id] = other_sect_region
        world.map.sect_regions[other_sect_region.id] = other_sect_region
        
        # 创建明心剑宗弟子
        avatar = Avatar(
            world=world,
            name="明心剑宗弟子",
            id=get_avatar_id(),
            birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
            age=Age(20, Realm.Qi_Refinement),
            gender=Gender.MALE,
            pos_x=0,
            pos_y=0,
            root=Root.GOLD,
            alignment=Alignment.RIGHTEOUS,
            sect=sect  # 明心剑宗
        )
        
        # 应该知道自己宗门的驻地
        assert sect_region.id in avatar.known_regions, (
            "应该知道自己宗门的驻地"
        )
        # 不应该知道其他宗门的驻地
        assert other_sect_region.id not in avatar.known_regions, (
            "不应该知道其他宗门的驻地"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
