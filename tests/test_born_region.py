import pytest
from unittest.mock import MagicMock

from src.classes.core.world import World
from src.classes.core.avatar import Avatar, Gender
from src.classes.environment.map import Map
from src.classes.environment.region import CityRegion, Region
from src.classes.environment.sect_region import SectRegion
from src.classes.core.sect import Sect
from src.classes.environment.tile import Tile, TileType
from src.utils.born_region import get_born_region_id
from src.classes.core.avatar.info_presenter import get_avatar_info, get_avatar_structured_info

@pytest.fixture
def mock_world():
    """创建一个包含城市和宗门驻地的世界"""
    game_map = Map(width=10, height=10)
    
    # 创建几个区域
    city1 = CityRegion(id=1, name="CityA", desc="City A")
    city2 = CityRegion(id=2, name="CityB", desc="City B")
    sect_region = SectRegion(id=3, name="SectBase", desc="Sect HQ", sect_id=1, sect_name="TestSect")
    
    # 注入到 Map
    game_map.regions[1] = city1
    game_map.regions[2] = city2
    game_map.regions[3] = sect_region
    game_map.update_sect_regions() # 更新 sect_regions 字典
    
    # 设置中心点
    city1.center_loc = (0, 0)
    city2.center_loc = (9, 9)
    sect_region.center_loc = (5, 5)

    world = MagicMock(spec=World)
    world.map = game_map
    return world

def test_born_region_priority_sect(mock_world):
    """测试优先级1：宗门驻地"""
    # 模拟一个宗门
    sect = MagicMock(spec=Sect)
    sect.id = 1
    sect.name = "TestSect"
    
    # 父母属于该宗门
    parent = MagicMock(spec=Avatar)
    parent.sect = sect
    
    # 预期：返回 SectRegion (id=3)
    born_id = get_born_region_id(mock_world, parents=[parent])
    assert born_id == 3

def test_born_region_priority_nearest_city(mock_world):
    """测试优先级2：最近城市"""
    # 父母无宗门
    parent = MagicMock(spec=Avatar)
    parent.sect = None
    
    # 父母位于 (1, 1)，靠近 CityA (0,0)
    parent.tile = MagicMock(spec=Tile)
    parent.tile.coordinate = (1, 1)
    
    # 预期：返回 CityA (id=1)
    born_id = get_born_region_id(mock_world, parents=[parent])
    assert born_id == 1
    
    # 父母位于 (8, 8)，靠近 CityB (9,9)
    parent.tile.coordinate = (8, 8)
    born_id = get_born_region_id(mock_world, parents=[parent])
    assert born_id == 2

def test_born_region_priority_random_city(mock_world):
    """测试优先级3：随机城市"""
    # 无父母，无宗门
    born_id = get_born_region_id(mock_world, parents=[], sect=None)
    assert born_id in [1, 2] # 只能是两个城市之一

def test_info_presenter_integration(mock_world):
    """测试展示层集成"""
    # 创建一个具有出身的角色
    avatar = MagicMock(spec=Avatar)
    avatar.name = "TestAvatar"
    avatar.gender = Gender.MALE
    avatar.age = MagicMock()
    avatar.age.__str__.return_value = "20"
    avatar.age.age = 20
    avatar.cultivation_progress = MagicMock()
    avatar.cultivation_progress.get_info.return_value = "Qi Refinement"
    avatar.world = mock_world
    avatar.world.ranking_manager = MagicMock()
    avatar.world.ranking_manager.get_avatar_rank.return_value = None
    
    # 设置出身为 CityA
    avatar.born_region_id = 1
    
    # Mock necessary attributes for get_avatar_info
    avatar.tile = None
    avatar.relations = {}
    avatar.magic_stone = 100
    avatar.weapon = None
    avatar.auxiliary = None
    avatar.sect = None
    avatar.alignment = None
    avatar.root = MagicMock()
    avatar.root.get_info.return_value = "Gold"
    avatar.technique = None
    avatar.personas = []
    avatar.materials = {}
    avatar.appearance = MagicMock()
    avatar.appearance.get_info.return_value = "Handsome"
    avatar.spirit_animal = None
    avatar.emotion = MagicMock()
    avatar.emotion.value = "Calm"
    avatar.long_term_objective = None
    avatar.short_term_objective = ""
    avatar.nickname = None
    avatar.hp = MagicMock()
    avatar.hp.__str__.return_value = "100/100"
    avatar.id = 1
    avatar.orthodoxy = None
    avatar.emotion = MagicMock()
    avatar.emotion.value = "calm"

    # 测试 info_dict
    from src.classes.core.avatar.info_presenter import get_avatar_info
    info = get_avatar_info(avatar, detailed=False)
    
    # 注意：这里会用到 i18n，因为 conftest 中强制了 zh-CN
    # 但我们 mock 的 Region.name 是 "CityA"
    # 期望看到 "出身" 这个 key，且值为 "CityA"
    assert "出身" in info
    assert info["出身"] == "CityA"
