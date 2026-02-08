
import pytest
from unittest.mock import MagicMock, patch
from src.classes.event import Event
from src.sim.simulator import Simulator
from src.systems.time import create_month_stamp, Year, Month

class TestEventLogic:
    
    @pytest.fixture
    def avatar_a(self, dummy_avatar):
        dummy_avatar.id = "avatar_a"
        dummy_avatar.name = "角色A"
        # 重置交互状态
        dummy_avatar.relation_interaction_states.clear()
        return dummy_avatar

    @pytest.fixture
    def avatar_b(self, base_world):
        from src.classes.core.avatar.core import Avatar, Gender
        from src.classes.age import Age
        from src.systems.cultivation import Realm
        from src.classes.root import Root
        from src.classes.alignment import Alignment
        
        av = Avatar(
            world=base_world,
            name="角色B",
            id="avatar_b",
            birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
            age=Age(20, Realm.Qi_Refinement),
            gender=Gender.FEMALE,
            pos_x=0,
            pos_y=0,
            root=Root.WATER,
            personas=[],
            alignment=Alignment.RIGHTEOUS
        )
        av.relation_interaction_states.clear()
        return av

    def test_process_interaction_from_event(self, avatar_a, avatar_b):
        """测试 Avatar.process_interaction_from_event 是否正确增加计数"""
        month_stamp = avatar_a.world.month_stamp
        event = Event(
            month_stamp=month_stamp,
            content="A与B发生了互动",
            related_avatars=[avatar_a.id, avatar_b.id]
        )
        
        # 初始计数应为 0
        assert avatar_a.relation_interaction_states[avatar_b.id]["count"] == 0
        assert avatar_b.relation_interaction_states[avatar_a.id]["count"] == 0
        
        # 处理事件
        avatar_a.process_interaction_from_event(event)
        avatar_b.process_interaction_from_event(event)
        
        # 计数应增加
        assert avatar_a.relation_interaction_states[avatar_b.id]["count"] == 1
        assert avatar_b.relation_interaction_states[avatar_a.id]["count"] == 1

    def test_process_interaction_self_exclusion(self, avatar_a):
        """测试交互计数是否排除了自身"""
        month_stamp = avatar_a.world.month_stamp
        event = Event(
            month_stamp=month_stamp,
            content="A自己做了某事",
            related_avatars=[avatar_a.id]
        )
        
        avatar_a.process_interaction_from_event(event)
        
        # 不应该有自己的交互记录
        assert avatar_a.id not in avatar_a.relation_interaction_states

    def test_simulator_phase_handle_interactions(self, base_world, avatar_a, avatar_b):
        """测试 Simulator._phase_handle_interactions 的增量处理逻辑"""
        # 注册角色
        base_world.avatar_manager.register_avatar(avatar_a)
        base_world.avatar_manager.register_avatar(avatar_b)
        
        sim = Simulator(base_world)
        processed_ids = set()
        
        event1 = Event(base_world.month_stamp, "事件1", related_avatars=[avatar_a.id, avatar_b.id])
        event2 = Event(base_world.month_stamp, "事件2", related_avatars=[avatar_a.id, avatar_b.id])
        
        # 1. 处理第一批事件
        sim._phase_handle_interactions([event1], processed_ids)
        assert avatar_a.relation_interaction_states[avatar_b.id]["count"] == 1
        assert event1.id in processed_ids
        
        # 2. 再次处理相同的事件（模拟 Phase 14 补漏但去重）
        sim._phase_handle_interactions([event1, event2], processed_ids)
        # event1 应该被跳过，event2 应该被处理
        assert avatar_a.relation_interaction_states[avatar_b.id]["count"] == 2
        assert event2.id in processed_ids

    @pytest.mark.asyncio
    async def test_simulator_full_step_interaction_counting(self, base_world, avatar_a, avatar_b, mock_llm_managers):
        """测试 Simulator.step 完整流程中的交互计数统计"""
        # 将角色注册到世界
        base_world.avatar_manager.register_avatar(avatar_a)
        base_world.avatar_manager.register_avatar(avatar_b)
        
        # Mock 一个返回事件的阶段，例如 Action 执行
        # 我们直接手动模拟 events 列表的变化
        
        sim = Simulator(base_world)
        
        # 构造一个交互事件
        interaction_event = Event(
            base_world.month_stamp, 
            "发生了某种跨阶段的交互", 
            related_avatars=[avatar_a.id, avatar_b.id]
        )
        
        # 我们通过 patch 让某些阶段返回这个事件
        with patch.object(Simulator, "_phase_execute_actions", return_value=[interaction_event]):
            # 执行一步
            await sim.step()
            
        # 验证交互计数是否正确增加
        # 注意：由于我们在 step 中有两个 Phase (7 和 14) 调用了 _phase_handle_interactions，
        # 且通过 processed_event_ids 去重，所以最终计数应该是 1 而不是 2。
        assert avatar_a.relation_interaction_states[avatar_b.id]["count"] == 1
        assert avatar_b.relation_interaction_states[avatar_a.id]["count"] == 1

    @pytest.mark.asyncio
    async def test_simulator_relation_evolution_trigger(self, base_world, avatar_a, avatar_b, mock_llm_managers):
        """测试交互计数达到阈值时触发关系演化并重置计数"""
        from src.utils.config import CONFIG
        threshold = CONFIG.social.relation_check_threshold
        
        # 1. 注册角色并人工设置高计数
        base_world.avatar_manager.register_avatar(avatar_a)
        base_world.avatar_manager.register_avatar(avatar_b)
        
        avatar_a.relation_interaction_states[avatar_b.id]["count"] = threshold
        avatar_b.relation_interaction_states[avatar_a.id]["count"] = threshold
        
        sim = Simulator(base_world)
        
        # 2. 模拟 LLM 返回关系变化
        mock_llm_managers["rr"].return_value = [Event(base_world.month_stamp, "关系进化了", related_avatars=[avatar_a.id, avatar_b.id])]
        
        # 3. 执行关系演化阶段
        living_avatars = base_world.avatar_manager.get_living_avatars()
        events = await sim._phase_evolve_relations(living_avatars)
        
        # 4. 验证
        assert len(events) == 1
        assert "关系进化了" in events[0].content
        # 计数器应该被重置
        assert avatar_a.relation_interaction_states[avatar_b.id]["count"] == 0
        assert avatar_b.relation_interaction_states[avatar_a.id]["count"] == 0
        # 检查次数应该增加
        assert avatar_a.relation_interaction_states[avatar_b.id]["checked_times"] == 1
        assert avatar_b.relation_interaction_states[avatar_a.id]["checked_times"] == 1

    def test_event_helper_push_pair_no_longer_calls_target_add_event(self, avatar_a, avatar_b):
        """测试 EventHelper.push_pair 是否已移除冗余的 target.add_event 调用"""
        from src.classes.action.event_helper import EventHelper
        
        event = Event(avatar_a.world.month_stamp, "测试事件", related_avatars=[avatar_a.id, avatar_b.id])
        
        # 重置 mock 或记录
        avatar_a._pending_events = []
        avatar_b._pending_events = []
        
        EventHelper.push_pair(event, initiator=avatar_a, target=avatar_b)
        
        # 应该只有发起者收到了事件（进入待处理队列）
        assert len(avatar_a._pending_events) == 1
        assert len(avatar_b._pending_events) == 0
        
        # 验证交互计数没有在这里被增加（因为现在由 Simulator 统一处理）
        assert avatar_a.relation_interaction_states[avatar_b.id]["count"] == 0
