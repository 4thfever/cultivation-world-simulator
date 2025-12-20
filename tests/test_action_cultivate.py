
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from src.classes.action.cultivate import Cultivate
from src.classes.tile import TileType
from src.classes.region import CultivateRegion, NormalRegion
from src.classes.event import Event
from src.classes.root import Root
from src.classes.essence import EssenceType

class TestActionCultivate:
    
    @pytest.fixture
    def cultivation_avatar(self, dummy_avatar):
        """配置一个适合修炼的角色环境"""
        # 设置灵根
        dummy_avatar.root = Root.FIRE
        
        # 使用 patch mock 掉 effects 属性
        # 注意：这里会影响 Avatar 类，但在 fixture 作用域结束后会还原
        with patch('src.classes.avatar.Avatar.effects', new_callable=PropertyMock) as mock_effects:
            mock_effects.return_value = {}
            
            # 重置修炼进度
            dummy_avatar.cultivation_progress.exp = 0
            # 设置为 29 级
            dummy_avatar.cultivation_progress.level = 29
            dummy_avatar.cultivation_progress.max_exp = 1000 
            
            yield dummy_avatar

    def test_cultivate_in_wild(self, cultivation_avatar):
        """测试在野外（非修炼区域）修炼：低保经验"""
        # 确保当前区域不是 CultivateRegion
        tile = cultivation_avatar.tile
        tile.region = NormalRegion(id=999, name="Wild", desc="Just Wild") # 普通区域
        
        action = Cultivate(cultivation_avatar, cultivation_avatar.world)
        
        # Check
        can_start, reason = action.can_start()
        assert can_start is True
        
        # Execute
        action._execute()
        
        # Assert: 获得低保经验
        expected_exp = Cultivate.BASE_EXP_LOW_EFFICIENCY
        assert cultivation_avatar.cultivation_progress.exp == expected_exp

    def test_cultivate_in_matching_region(self, cultivation_avatar):
        """测试在匹配灵气的洞府修炼：高经验"""
        # 设置当前 Tile 为 CultivateRegion
        region = CultivateRegion(id=1, name="Fire Cave", desc="Hot", essence_type=EssenceType.FIRE, essence_density=5)
        
        cultivation_avatar.tile.region = region
        
        action = Cultivate(cultivation_avatar, cultivation_avatar.world)
        action._execute()
        
        # Assert: density(5) * base(100) = 500
        expected_exp = 5 * Cultivate.BASE_EXP_PER_DENSITY
        
        assert cultivation_avatar.cultivation_progress.exp == expected_exp

    def test_cultivate_in_mismatching_region(self, cultivation_avatar):
        """测试在不匹配灵气的洞府修炼：低保经验"""
        # 设置水灵气，角色是火灵根
        region = CultivateRegion(id=2, name="Water Cave", desc="Wet", essence_type=EssenceType.WATER, essence_density=5)
        cultivation_avatar.tile.region = region
        
        action = Cultivate(cultivation_avatar, cultivation_avatar.world)
        action._execute()
        
        # Assert: 0 * 100 -> fallback to LOW_EFFICIENCY
        expected_exp = Cultivate.BASE_EXP_LOW_EFFICIENCY
        assert cultivation_avatar.cultivation_progress.exp == expected_exp

    def test_cultivate_bottleneck(self, cultivation_avatar):
        """测试瓶颈期修炼：不增加经验"""
        # 设置为瓶颈等级
        cultivation_avatar.cultivation_progress.level = 30 
        initial_exp = cultivation_avatar.cultivation_progress.exp
        
        action = Cultivate(cultivation_avatar, cultivation_avatar.world)
        
        # Check can_start
        can_start, reason = action.can_start()
        assert can_start is False
        assert "瓶颈" in reason
        
        # Force execute (should return early)
        action._execute()
        assert cultivation_avatar.cultivation_progress.exp == initial_exp

    def test_cultivate_occupied_region(self, cultivation_avatar):
        """测试修炼区域被他人占据"""
        region = CultivateRegion(id=3, name="Occupied", desc="Full", essence_type=EssenceType.FIRE, essence_density=5)
        other_avatar = MagicMock()
        other_avatar.name = "Stranger"
        region.host_avatar = other_avatar # 占据者不是自己
        cultivation_avatar.tile.region = region
        
        action = Cultivate(cultivation_avatar, cultivation_avatar.world)
        
        can_start, reason = action.can_start()
        assert can_start is False
        assert "Stranger" in reason

