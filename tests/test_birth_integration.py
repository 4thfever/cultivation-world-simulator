import pytest
from src.classes.core.avatar import Avatar, Gender
from src.classes.age import Age
from src.systems.cultivation import Realm, CultivationProgress
from src.utils.id_generator import get_avatar_id
from src.classes.root import Root
from src.systems.time import create_month_stamp, Year, Month

def test_register_avatar_buffer(base_world):
    """测试注册新角色时的缓冲区逻辑"""
    manager = base_world.avatar_manager
    
    # 1. 注册普通角色（非新生，例如加载存档）
    a1 = Avatar(
        world=base_world,
        name="OldGuy",
        id=get_avatar_id(),
        birth_month_stamp=create_month_stamp(Year(100), Month.JANUARY),
        age=Age(20, Realm.Qi_Refinement),
        gender=Gender.MALE
    )
    manager.register_avatar(a1, is_newly_born=False)
    
    assert a1.id in manager.avatars
    assert len(manager.pop_newly_born()) == 0
    
    # 2. 注册新生角色
    a2 = Avatar(
        world=base_world,
        name="Baby",
        id=get_avatar_id(),
        birth_month_stamp=create_month_stamp(Year(200), Month.JANUARY),
        age=Age(1, Realm.Qi_Refinement),
        gender=Gender.FEMALE
    )
    manager.register_avatar(a2, is_newly_born=True)
    
    assert a2.id in manager.avatars
    newly_born = manager.pop_newly_born()
    assert len(newly_born) == 1
    assert str(a2.id) in newly_born
    
    # 3. 再次获取应为空
    assert len(manager.pop_newly_born()) == 0

@pytest.mark.asyncio
async def test_simulator_birth_logic(base_world):
    """测试模拟器中的生子逻辑集成"""
    from src.sim.simulator import Simulator
    from unittest.mock import patch
    from src.classes.core.avatar import Avatar
    from src.classes.age import Age
    from src.systems.cultivation import Realm, CultivationProgress
    from src.classes.event import Event
    
    # 构造一个简单的模拟返回值
    mock_avatar = Avatar(
        world=base_world,
        name="MockBaby",
        id="mock_id_123",
        birth_month_stamp=base_world.month_stamp,
        age=Age(1, Realm.Qi_Refinement),
        gender=Gender.MALE
    )
    
    sim = Simulator(base_world)
    # sim.awakening_rate 不再直接控制，而是由 process_awakening 内部读取配置
    # 我们这里直接 patch process_awakening 来模拟命中
    
    def mock_process_awakening(world):
        # 模拟内部行为：注册角色并返回事件
        world.avatar_manager.register_avatar(mock_avatar, is_newly_born=True)
        return [Event(world.month_stamp, f"{mock_avatar.name} awakened", related_avatars=[mock_avatar.id])]

    # Patch process_awakening
    with patch('src.sim.simulator.process_awakening', side_effect=mock_process_awakening):
        # 执行一次更新
        living_avatars = base_world.avatar_manager.get_living_avatars()
        events = sim._phase_update_age_and_birth(living_avatars)
    
    # 验证产生了一个新角色
    newly_born = base_world.avatar_manager.pop_newly_born()
    assert len(newly_born) == 1
    assert newly_born[0] == mock_avatar.id
    
    # 验证新角色在管理器中
    avatar = base_world.avatar_manager.get_avatar(mock_avatar.id)
    assert avatar is mock_avatar
    assert mock_avatar.name in events[0].content # 确保事件也生成了
