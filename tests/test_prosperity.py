import pytest
from unittest.mock import MagicMock
from src.classes.environment.region import CityRegion
from src.classes.action.help_people import HelpPeople
from src.classes.action.plunder_people import PlunderPeople
from src.classes.action.devour_people import DevourPeople
from src.sim.simulator import Simulator
from src.classes.alignment import Alignment
from src.classes.items.auxiliary import Auxiliary
from src.systems.time import MonthStamp, Year, Month

class TestProsperity:
    def test_region_initial_prosperity(self):
        """测试城市区域初始繁荣度"""
        region = CityRegion(id=1, name="TestCity", desc="Test")
        assert region.prosperity == 50

    def test_change_prosperity_bounds(self):
        """测试繁荣度修改的边界限制"""
        region = CityRegion(id=1, name="TestCity", desc="Test")
        
        # 增加测试
        region.change_prosperity(10)
        assert region.prosperity == 60
        
        # 上限测试
        region.change_prosperity(100)
        assert region.prosperity == 100
        
        # 减少测试
        region.change_prosperity(-50)
        assert region.prosperity == 50
        
        # 下限测试
        region.change_prosperity(-100)
        assert region.prosperity == 0

    def test_help_people_increases_prosperity(self, avatar_in_city):
        """测试救济百姓增加繁荣度"""
        region = avatar_in_city.tile.region
        initial_prosperity = region.prosperity
        avatar_in_city.magic_stone = 100  # 确保有钱
        
        action = HelpPeople(avatar_in_city, avatar_in_city.world)
        action._execute()
        
        assert region.prosperity == initial_prosperity + 3

    def test_plunder_people_decreases_prosperity(self, avatar_in_city):
        """测试搜刮民脂减少繁荣度，且收益固定"""
        region = avatar_in_city.tile.region
        initial_prosperity = region.prosperity
        initial_stone = avatar_in_city.magic_stone
        
        # 确保是邪恶阵营以符合逻辑（虽然单元测试里直接调用_execute不检查can_start）
        avatar_in_city.alignment = Alignment.EVIL
        
        action = PlunderPeople(avatar_in_city, avatar_in_city.world)
        action._execute()
        
        # 检查繁荣度减少
        assert region.prosperity == initial_prosperity - 5
        
        # 检查收益 (GAIN = 20)
        # 即使繁荣度变化，收益应该是固定的 20 (无倍率加成)
        assert avatar_in_city.magic_stone == initial_stone + 20

    def test_devour_people_decreases_prosperity(self, avatar_in_city):
        """测试吞噬生灵大幅减少繁荣度"""
        region = avatar_in_city.tile.region
        initial_prosperity = region.prosperity
        
        # 给予万魂幡
        aux = Auxiliary(id=999, name="万魂幡", realm=None, desc="Test")
        aux.special_data = {"devoured_souls": 0}
        avatar_in_city.auxiliary = aux
        
        action = DevourPeople(avatar_in_city, avatar_in_city.world)
        action._execute()
        
        assert region.prosperity == initial_prosperity - 15

    def test_simulator_auto_recovery(self, base_world):
        """测试模拟器每月自动恢复繁荣度"""
        sim = Simulator(base_world)
        
        # 创建一个繁荣度不满的城市
        city = CityRegion(id=1, name="TestCity", desc="Test")
        city.prosperity = 40
        
        # 注入到地图
        from src.classes.environment.tile import Tile, TileType
        tile = Tile(0, 0, TileType.CITY)
        tile.region = city
        base_world.map.tiles[(0, 0)] = tile
        base_world.map.regions[1] = city
        
        # 执行恢复步骤
        sim._phase_update_region_prosperity()
        
        assert city.prosperity == 41

        # 再次执行，确保不溢出
        city.prosperity = 100
        sim._phase_update_region_prosperity()
        assert city.prosperity == 100
