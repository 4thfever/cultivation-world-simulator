import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from src.sim.simulator import Simulator
from src.classes.action.move_to_direction import MoveToDirection
from src.classes.environment.tile import TileType
from src.classes.action_runtime import ActionInstance

@pytest.mark.asyncio
async def test_simulator_step_moves_avatar_and_sets_tile(base_world, dummy_avatar, mock_llm_managers):
    # Set initial position
    dummy_avatar.pos_x = 1
    dummy_avatar.pos_y = 1
    # Ensure tile is updated to initial position (fixture puts it at 0,0)
    dummy_avatar.tile = base_world.map.get_tile(1, 1)

    sim = Simulator(base_world)
    base_world.avatar_manager.avatars[dummy_avatar.id] = dummy_avatar

    # Manually assign a MoveToDirection action to avoid relying on LLM
    action = MoveToDirection(dummy_avatar, base_world)
    # "East" means x + 1
    direction = "East"
    action.start(direction=direction) # Initialize start_monthstamp etc.
    
    # Wrap in ActionInstance
    dummy_avatar.current_action = ActionInstance(action=action, params={"direction": direction})

    # Mock LLM to avoid external calls or errors (Handled by mock_llm_managers fixture)
    
    print(f"DEBUG: Before step: pos_x={dummy_avatar.pos_x}")
    # Run step
    await sim.step()
    print(f"DEBUG: After step: pos_x={dummy_avatar.pos_x}")
    print(f"DEBUG: move_step_length={getattr(dummy_avatar, 'move_step_length', 'Not set')}")
    print(f"DEBUG: effects={dummy_avatar.effects}")

    # Assert moved East (x increased by move_step_length)
    # Current move step for Qi Refinement is 2
    assert dummy_avatar.pos_x == 3
    assert dummy_avatar.pos_y == 1

    # Assert tile is updated
    assert dummy_avatar.tile is not None
    assert dummy_avatar.tile.x == 3
    assert dummy_avatar.tile.y == 1

@pytest.mark.asyncio
async def test_simulator_interaction_counting(base_world, dummy_avatar, mock_llm_managers):
    """测试交互计数在 step 中被正确处理且去重"""
    from src.classes.event import Event
    from src.classes.core.avatar import Avatar, Gender
    from src.classes.age import Age
    from src.systems.cultivation import Realm
    from src.systems.time import create_month_stamp, Year, Month
    from src.classes.root import Root
    from src.classes.alignment import Alignment
    
    sim = Simulator(base_world)
    
    # 创建另一个角色用于交互
    other_avatar = Avatar(
        world=base_world,
        name="OtherAvatar",
        id="other_id",
        birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
        age=Age(20, Realm.Qi_Refinement),
        gender=Gender.FEMALE,
        pos_x=0,
        pos_y=0,
        root=Root.WOOD,
        alignment=Alignment.NEUTRAL
    )
    
    base_world.avatar_manager.register_avatar(dummy_avatar)
    base_world.avatar_manager.register_avatar(other_avatar)

    # 1. 模拟第一阶段（执行动作）产生的事件
    ev1 = Event(base_world.month_stamp, "阶段1交互", related_avatars=[dummy_avatar.id, other_avatar.id])
    
    # 2. 模拟第二阶段（被动效果/奇遇）产生的事件
    ev2 = Event(base_world.month_stamp, "阶段2交互", related_avatars=[dummy_avatar.id, other_avatar.id])

    with patch.object(sim, '_phase_execute_actions', new_callable=AsyncMock) as mock_exec, \
         patch.object(sim, '_phase_passive_effects', new_callable=AsyncMock) as mock_passive:
        
        mock_exec.return_value = [ev1]
        mock_passive.return_value = [ev2]
        
        await sim.step()
        
        # 验证交互计数是否增加了 2 (两个独立事件)
        count = dummy_avatar.relation_interaction_states[other_avatar.id]["count"]
        assert count == 2

@pytest.mark.asyncio
async def test_simulator_event_deduplication(base_world, dummy_avatar, mock_llm_managers):
    """测试事件去重逻辑：同一个事件对象在多个阶段被返回时，入库应只有一次"""
    from src.classes.event import Event
    sim = Simulator(base_world)
    base_world.avatar_manager.register_avatar(dummy_avatar)
    
    ev = Event(base_world.month_stamp, "重复事件")
    ev_id = ev.id
    
    # 模拟两个不同的阶段返回了同一个 ID 的事件对象
    with patch.object(sim, '_phase_execute_actions', new_callable=AsyncMock) as mock_exec, \
         patch.object(sim, '_phase_passive_effects', new_callable=AsyncMock) as mock_passive:
        
        mock_exec.return_value = [ev]
        mock_passive.return_value = [ev]
        
        # 拦截 event_manager.add_event
        base_world.event_manager.add_event = MagicMock()
        
        await sim.step()
        
        # 验证该 ID 的事件只被添加了一次
        # 我们过滤出 ID 匹配的调用
        target_calls = [
            call for call in base_world.event_manager.add_event.call_args_list 
            if call.args[0].id == ev_id
        ]
        assert len(target_calls) == 1
