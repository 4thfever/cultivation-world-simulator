import pytest
from unittest.mock import MagicMock

from src.classes.death_reason import DeathReason, DeathType
from src.classes.death import handle_death
from src.classes.relation import Relation, get_relations_strs
from src.classes.event import Event

def test_death_reason_str():
    """测试死因的字符串格式化"""
    # 战死
    reason_battle = DeathReason(DeathType.BATTLE, killer_name="张三")
    assert str(reason_battle) == "被张三杀害"
    
    # 战死（未知凶手）
    reason_battle_unknown = DeathReason(DeathType.BATTLE)
    assert str(reason_battle_unknown) == "被未知角色杀害"
    
    # 重伤
    reason_injury = DeathReason(DeathType.SERIOUS_INJURY)
    assert str(reason_injury) == "重伤不治身亡"
    
    # 老死
    reason_old = DeathReason(DeathType.OLD_AGE)
    assert str(reason_old) == "寿元耗尽而亡"

def test_handle_death(base_world, dummy_avatar):
    """测试死亡处理函数"""
    reason = DeathReason(DeathType.BATTLE, killer_name="李四")
    
    # 执行死亡处理
    handle_death(base_world, dummy_avatar, reason)
    
    # 验证状态
    assert dummy_avatar.is_dead is True
    assert dummy_avatar.death_info is not None
    assert dummy_avatar.death_info["reason"] == "被李四杀害"
    assert dummy_avatar.death_info["time"] == int(base_world.month_stamp)
    assert dummy_avatar.death_info["location"] == (dummy_avatar.pos_x, dummy_avatar.pos_y)
    
    # 验证清理工作
    assert len(dummy_avatar.planned_actions) == 0
    assert dummy_avatar.current_action is None
    assert dummy_avatar.sect is None

def test_relation_display_with_death(base_world, dummy_avatar):
    """测试关系列表中的死亡显示"""
    # 创建另一个角色作为朋友
    from src.classes.avatar import Avatar, Gender
    from src.classes.age import Age
    from src.classes.cultivation import Realm
    from src.utils.id_generator import get_avatar_id
    from src.classes.root import Root
    from src.classes.alignment import Alignment
    from src.classes.calendar import create_month_stamp, Year, Month
    
    friend = Avatar(
        world=base_world,
        name="Friend",
        id=get_avatar_id(),
        birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
        age=Age(20, Realm.Qi_Refinement),
        gender=Gender.MALE,
        pos_x=0, pos_y=0,
        root=Root.WOOD,
        alignment=Alignment.RIGHTEOUS
    )
    
    # 建立关系
    dummy_avatar.set_relation(friend, Relation.FRIEND)
    
    # 初始状态：显示正常名字
    strs_before = get_relations_strs(dummy_avatar)
    assert "朋友：Friend" in strs_before
    
    # 朋友死亡（重伤）
    reason = DeathReason(DeathType.SERIOUS_INJURY)
    handle_death(base_world, friend, reason)
    
    # 死亡后：显示带死因的名字
    strs_after = get_relations_strs(dummy_avatar)
    assert "朋友：Friend(已故：重伤不治身亡)" in strs_after

@pytest.mark.asyncio
async def test_simulator_resolve_death(base_world, dummy_avatar):
    """测试模拟器的死亡结算阶段"""
    from src.sim.simulator import Simulator
    sim = Simulator(base_world)
    base_world.avatar_manager.avatars[dummy_avatar.id] = dummy_avatar
    
    # Case 1: 重伤死亡
    dummy_avatar.hp.cur = -10
    events = sim._phase_resolve_death()
    
    assert dummy_avatar.is_dead is True
    assert dummy_avatar.death_info["reason"] == "重伤不治身亡"
    assert len(events) > 0
    assert "重伤不治身亡" in str(events[0])

@pytest.mark.asyncio
async def test_simulator_evolve_relations_filter_dead(base_world, dummy_avatar):
    """测试关系演化阶段过滤死者"""
    from src.sim.simulator import Simulator
    sim = Simulator(base_world)
    
    # 创建对手
    from src.classes.avatar import Avatar, Gender
    from src.classes.age import Age
    from src.classes.cultivation import Realm
    from src.utils.id_generator import get_avatar_id
    from src.classes.root import Root
    from src.classes.alignment import Alignment
    from src.classes.calendar import create_month_stamp, Year, Month
    
    target = Avatar(
        world=base_world,
        name="Target",
        id=get_avatar_id(),
        birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
        age=Age(20, Realm.Qi_Refinement),
        gender=Gender.MALE,
        pos_x=0, pos_y=0,
        root=Root.FIRE,
        alignment=Alignment.EVIL
    )
    
    base_world.avatar_manager.avatars[dummy_avatar.id] = dummy_avatar
    base_world.avatar_manager.avatars[target.id] = target
    
    # 设置交互状态达到阈值
    dummy_avatar.relation_interaction_states[target.id]["count"] = 100
    
    # 让 Target 死亡
    target.set_dead("测试死亡", base_world.month_stamp)
    
    # Mock RelationResolver 防止真正调用 LLM
    from unittest.mock import patch
    with patch('src.classes.relation_resolver.RelationResolver.run_batch') as mock_run:
        await sim._phase_evolve_relations()
        
        # 验证：因为 target 已死，应该不会调用 run_batch
        mock_run.assert_not_called()
        
    # 如果 Target 活着，应该会调用
    target.is_dead = False
    with patch('src.classes.relation_resolver.RelationResolver.run_batch') as mock_run:
        mock_run.return_value = []
        await sim._phase_evolve_relations()
        mock_run.assert_called_once()

