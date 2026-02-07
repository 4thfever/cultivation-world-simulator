
import pytest
from unittest.mock import MagicMock, patch, ANY
from src.classes.action.retreat import Retreat
from src.classes.action_runtime import ActionStatus
from src.systems.cultivation import Realm
from src.i18n import t

class TestActionRetreat:
    
    @pytest.fixture
    def retreat_avatar(self, dummy_avatar):
        """配置一个适合闭关的角色环境"""
        # 设置为练气期，基础突破概率 0.5
        dummy_avatar.cultivation_progress.realm = Realm.Qi_Refinement
        
        # 确保 temporary_effects 列表存在（虽然 init 应该已经创建了）
        if not hasattr(dummy_avatar, "temporary_effects"):
            dummy_avatar.temporary_effects = []
            
        return dummy_avatar

    def test_retreat_init(self, retreat_avatar):
        """测试闭关动作初始化"""
        action = Retreat(retreat_avatar, retreat_avatar.world)
        
        # 验证持续时间范围 12-60 个月
        assert 12 <= action.duration_months <= 60
        # 验证是大事
        assert action.IS_MAJOR is True
        
        # 验证可以开始
        can_start, reason = action.can_start()
        assert can_start is True

    @pytest.mark.asyncio
    async def test_retreat_success(self, retreat_avatar):
        """测试闭关成功"""
        action = Retreat(retreat_avatar, retreat_avatar.world)
        action.duration_months = 24
        
        # Mock 随机数，使得 random.random() < success_rate (0.5)
        # calc_success_rate for Qi_Refinement is 0.5 (0.5 - 0*0.1)
        # So we need random < 0.5
        with patch('random.random', return_value=0.1), \
             patch('src.classes.story_teller.StoryTeller.tell_story', return_value="Great story"):
            
            # Start
            start_event = action.start()
            assert start_event is not None
            
            # Finish
            events = await action.finish()
            
            # 验证事件生成
            assert len(events) >= 2
            assert any("successfully" in str(e) or "成功" in str(e) for e in events)
            
            # 验证获得了临时效果
            assert len(retreat_avatar.temporary_effects) == 1
            effect = retreat_avatar.temporary_effects[0]
            assert effect["source"] == "Retreat Bonus"
            assert effect["effects"]["extra_breakthrough_success_rate"] > 0
            assert effect["duration"] == 120 # 10年
            
            # 验证属性重算（需要检查 effects 属性是否包含加成）
            # 由于 effects 是动态计算的，只要 temporary_effects 里有，且 EffectsMixin 正常工作，
            # 那么 avatar.effects 应该能读到
            
            # 这里简单验证 temporary_effects 结构正确即可，EffectsMixin 逻辑由 mixin 自身保证
            pass

    @pytest.mark.asyncio
    async def test_retreat_fail(self, retreat_avatar):
        """测试闭关失败"""
        action = Retreat(retreat_avatar, retreat_avatar.world)
        action.duration_months = 36
        
        original_lifespan = retreat_avatar.age.max_lifespan
        
        # Mock 随机数，使得 random.random() >= success_rate (0.5)
        # random.randint used for reduce_years (5, 20)
        with patch('random.random', return_value=0.9), \
             patch('random.randint', side_effect=[10]), \
             patch('src.classes.story_teller.StoryTeller.tell_story', return_value="Sad story"):
            
            # Finish
            events = await action.finish()
            
            # 验证事件
            assert len(events) >= 2
            assert any("failed" in str(e) or "失败" in str(e) for e in events)
            
            # 验证没有临时效果
            assert len(retreat_avatar.temporary_effects) == 0
            
            # 验证寿元减少 (mocked to reduce 10)
            assert retreat_avatar.age.max_lifespan == original_lifespan - 10

    def test_calc_success_rate(self, retreat_avatar):
        """测试成功率计算"""
        action = Retreat(retreat_avatar, retreat_avatar.world)
        
        # Qi Refinement: 0.5 - 0 = 0.5
        retreat_avatar.cultivation_progress.realm = Realm.Qi_Refinement
        assert action.calc_success_rate() == 0.5
        
        # Foundation: 0.5 - 0.1 = 0.4
        retreat_avatar.cultivation_progress.realm = Realm.Foundation_Establishment
        assert action.calc_success_rate() == 0.4
        
        # Core Formation: 0.5 - 0.2 = 0.3
        retreat_avatar.cultivation_progress.realm = Realm.Core_Formation
        assert action.calc_success_rate() == 0.3
        
        # Nascent Soul: 0.5 - 0.3 = 0.2
        retreat_avatar.cultivation_progress.realm = Realm.Nascent_Soul
        assert action.calc_success_rate() == pytest.approx(0.2)

    def test_retreat_isolation(self, retreat_avatar):
        """测试闭关的隔离性（不参与聚会，不触发奇遇）"""
        action = Retreat(retreat_avatar, retreat_avatar.world)
        
        # 1. 验证 Action 类属性配置
        assert action.ALLOW_GATHERING is False
        assert action.ALLOW_WORLD_EVENTS is False
        
        # 2. 验证 Avatar 状态检查
        # 模拟角色正在执行闭关动作
        from src.classes.action_runtime import ActionInstance
        retreat_avatar.current_action = ActionInstance(action=action, params={}, status="running")
        
        assert retreat_avatar.can_join_gathering is False
        assert retreat_avatar.can_trigger_world_event is False
        
        # 3. 验证解除动作后恢复正常
        retreat_avatar.current_action = None
        assert retreat_avatar.can_join_gathering is True
        assert retreat_avatar.can_trigger_world_event is True

