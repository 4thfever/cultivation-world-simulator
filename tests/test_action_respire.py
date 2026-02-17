import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from src.classes.action.respire import Respire
from src.classes.environment.tile import TileType
from src.classes.environment.region import CultivateRegion, NormalRegion
from src.classes.event import Event
from src.classes.root import Root
from src.classes.essence import EssenceType

class TestActionRespire:
    
    @pytest.fixture
    def cultivation_avatar(self, dummy_avatar):
        """配置一个适合修炼的角色环境"""
        # 设置灵根
        dummy_avatar.root = Root.FIRE
        
        # 使用 patch mock 掉 effects 属性
        # 注意：这里会影响 Avatar 类，但在 fixture 作用域结束后会还原
        with patch('src.classes.core.avatar.Avatar.effects', new_callable=PropertyMock) as mock_effects:
            mock_effects.return_value = {}
            
            # 重置修炼进度
            dummy_avatar.cultivation_progress.exp = 0
            # 设置为 29 级
            dummy_avatar.cultivation_progress.level = 29
            dummy_avatar.cultivation_progress.max_exp = 1000 
            
            yield dummy_avatar

    def test_respire_in_wild(self, cultivation_avatar):
        """测试在野外（非修炼区域）吐纳：低保经验"""
        # 确保当前区域不是 CultivateRegion
        tile = cultivation_avatar.tile
        tile.region = NormalRegion(id=999, name="Wild", desc="Just Wild") # 普通区域
        
        action = Respire(cultivation_avatar, cultivation_avatar.world)
        
        # Check
        can_start, reason = action.can_start()
        assert can_start is True
        
        # Execute
        action._execute()
        
        # Assert: 获得低保经验
        expected_exp = Respire.BASE_EXP_LOW_EFFICIENCY
        assert cultivation_avatar.cultivation_progress.exp == expected_exp

    def test_respire_in_matching_region(self, cultivation_avatar):
        """测试在匹配灵气的洞府吐纳：高经验"""
        # 设置当前 Tile 为 CultivateRegion
        region = CultivateRegion(id=1, name="Fire Cave", desc="Hot", essence_type=EssenceType.FIRE, essence_density=5)
        
        cultivation_avatar.tile.region = region
        
        action = Respire(cultivation_avatar, cultivation_avatar.world)
        action._execute()
        
        # Assert: density(5) * base(100) = 500
        expected_exp = 5 * Respire.BASE_EXP_PER_DENSITY
        
        assert cultivation_avatar.cultivation_progress.exp == expected_exp

    def test_respire_in_mismatching_region(self, cultivation_avatar):
        """测试在不匹配灵气的洞府吐纳：低保经验"""
        # 设置水灵气，角色是火灵根
        region = CultivateRegion(id=2, name="Water Cave", desc="Wet", essence_type=EssenceType.WATER, essence_density=5)
        cultivation_avatar.tile.region = region
        
        action = Respire(cultivation_avatar, cultivation_avatar.world)
        action._execute()
        
        # Assert: 0 * 100 -> fallback to LOW_EFFICIENCY
        expected_exp = Respire.BASE_EXP_LOW_EFFICIENCY
        assert cultivation_avatar.cultivation_progress.exp == expected_exp

    def test_respire_bottleneck(self, cultivation_avatar):
        """测试瓶颈期吐纳：不增加经验"""
        # 设置为瓶颈等级
        cultivation_avatar.cultivation_progress.level = 30 
        initial_exp = cultivation_avatar.cultivation_progress.exp
        
        action = Respire(cultivation_avatar, cultivation_avatar.world)
        
        # Check can_start
        can_start, reason = action.can_start()
        assert can_start is False
        assert "瓶颈" in reason or "bottleneck" in reason
        
        # Force execute (should return early)
        action._execute()
        assert cultivation_avatar.cultivation_progress.exp == initial_exp

    def test_respire_occupied_region(self, cultivation_avatar):
        """测试修炼区域被他人占据"""
        region = CultivateRegion(id=3, name="Occupied", desc="Full", essence_type=EssenceType.FIRE, essence_density=5)
        other_avatar = MagicMock()
        other_avatar.name = "Stranger"
        region.host_avatar = other_avatar # 占据者不是自己
        cultivation_avatar.tile.region = region
        
        action = Respire(cultivation_avatar, cultivation_avatar.world)
        
        can_start, reason = action.can_start()
        assert can_start is False
        assert "Stranger" in reason

    def test_respire_with_multiplier(self, cultivation_avatar):
        """测试额外吐纳经验倍率的效果"""
        # 设置基础修炼环境 (匹配灵气)
        region = CultivateRegion(id=4, name="Multiplier Cave", desc="Multiplier", essence_type=EssenceType.FIRE, essence_density=5)
        cultivation_avatar.tile.region = region
        
        # 基础经验: 5 * 100 = 500
        base_exp = 5 * Respire.BASE_EXP_PER_DENSITY
        
        # Mock effects to include multiplier
        # 注意：conftest 中的 cultivation_avatar 已经 patch 了 effects，我们需要修改那个 mock 的返回值
        # 或者直接重新 patch 一次
        
        with patch.object(cultivation_avatar.__class__, 'effects', new_callable=PropertyMock) as mock_effects:
             # Case 1: 0.5 multiplier (+50%)
            mock_effects.return_value = {"extra_respire_exp_multiplier": 0.5}
            
            action = Respire(cultivation_avatar, cultivation_avatar.world)
            action._execute()
            
            expected_exp_1 = base_exp * (1 + 0.5)
            assert cultivation_avatar.cultivation_progress.exp == expected_exp_1
            
            # Reset exp
            cultivation_avatar.cultivation_progress.exp = 0
            
            # Case 2: 1.0 multiplier (+100%)
            mock_effects.return_value = {"extra_respire_exp_multiplier": 1.0}
            action._execute()
            
            expected_exp_2 = base_exp * (1 + 1.0)
            assert cultivation_avatar.cultivation_progress.exp == expected_exp_2
