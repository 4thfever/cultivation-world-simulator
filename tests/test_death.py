import pytest
from unittest.mock import MagicMock

from src.classes.death_reason import DeathReason, DeathType
from src.classes.death import handle_death
from src.classes.relation.relation import Relation, get_relations_strs
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
    """测试死亡处理函数（集成测试：包含归档和缓冲）"""
    reason = DeathReason(DeathType.BATTLE, killer_name="李四")
    
    # 确保角色在管理器中
    base_world.avatar_manager.register_avatar(dummy_avatar)
    assert dummy_avatar.id in base_world.avatar_manager.avatars
    
    # 执行死亡处理
    handle_death(base_world, dummy_avatar, reason)
    
    # 1. 验证对象状态
    assert dummy_avatar.is_dead is True
    assert dummy_avatar.death_info is not None
    assert dummy_avatar.death_info["reason"] == "被李四杀害"
    assert dummy_avatar.death_info["time"] == int(base_world.month_stamp)
    
    # 2. 验证管理器状态（已归档）
    assert dummy_avatar.id not in base_world.avatar_manager.avatars
    assert dummy_avatar.id in base_world.avatar_manager.dead_avatars
    
    # 3. 验证缓冲区（用于前端推送）
    newly_dead = base_world.avatar_manager.pop_newly_dead()
    assert str(dummy_avatar.id) in newly_dead
    
    # 4. 验证缓冲区清空
    assert len(base_world.avatar_manager.pop_newly_dead()) == 0

def test_relation_display_with_death(base_world, dummy_avatar):
    """测试关系列表中的死亡显示"""
    # 创建另一个角色作为朋友
    from src.classes.core.avatar import Avatar, Gender
    from src.classes.age import Age
    from src.systems.cultivation import Realm
    from src.utils.id_generator import get_avatar_id
    from src.classes.root import Root
    from src.classes.alignment import Alignment
    from src.systems.time import create_month_stamp, Year, Month
    
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
    # 注册朋友
    base_world.avatar_manager.register_avatar(friend)
    
    # 建立关系
    dummy_avatar.make_friend_with(friend)
    
    # 初始状态：显示正常名字
    strs_before = get_relations_strs(dummy_avatar)
    assert "友好：Friend" in strs_before
    
    # 朋友死亡（重伤）
    reason = DeathReason(DeathType.SERIOUS_INJURY)
    handle_death(base_world, friend, reason)
    
    # 死亡后：显示带死因的名字
    strs_after = get_relations_strs(dummy_avatar)
    assert "友好：Friend(已故：重伤不治身亡)" in strs_after
    assert friend not in dummy_avatar.relations
    assert friend in dummy_avatar.archived_relations
    assert dummy_avatar not in friend.relations
    assert dummy_avatar in friend.archived_relations


def test_death_archives_master_relation_and_clears_active_graph(base_world, dummy_avatar):
    from src.classes.core.avatar import Avatar, Gender
    from src.classes.age import Age
    from src.systems.cultivation import Realm
    from src.utils.id_generator import get_avatar_id
    from src.classes.root import Root
    from src.classes.alignment import Alignment
    from src.systems.time import create_month_stamp, Year, Month

    master = Avatar(
        world=base_world,
        name="Master",
        id=get_avatar_id(),
        birth_month_stamp=create_month_stamp(Year(1990), Month.JANUARY),
        age=Age(50, Realm.Foundation_Establishment),
        gender=Gender.MALE,
        pos_x=1, pos_y=1,
        root=Root.WOOD,
        alignment=Alignment.RIGHTEOUS,
    )
    base_world.avatar_manager.register_avatar(master)
    dummy_avatar.acknowledge_master(master)

    assert master in dummy_avatar.relations
    handle_death(base_world, master, DeathReason(DeathType.OLD_AGE))

    assert master not in dummy_avatar.relations
    assert master in dummy_avatar.archived_relations
    assert dummy_avatar not in master.relations
    assert dummy_avatar in master.archived_relations
    assert master.sect is None
    assert master.death_info["sect_name_at_death"] == ""


def test_structured_relations_mark_archived_scope_after_death(base_world, dummy_avatar):
    from src.classes.core.avatar import Avatar, Gender
    from src.classes.age import Age
    from src.systems.cultivation import Realm
    from src.utils.id_generator import get_avatar_id
    from src.classes.root import Root
    from src.classes.alignment import Alignment
    from src.systems.time import create_month_stamp, Year, Month

    friend = Avatar(
        world=base_world,
        name="Friend",
        id=get_avatar_id(),
        birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
        age=Age(20, Realm.Qi_Refinement),
        gender=Gender.MALE,
        pos_x=0,
        pos_y=0,
        root=Root.WOOD,
        alignment=Alignment.RIGHTEOUS,
    )
    base_world.avatar_manager.register_avatar(friend)
    dummy_avatar.make_friend_with(friend)

    handle_death(base_world, friend, DeathReason(DeathType.SERIOUS_INJURY))

    relations = dummy_avatar.get_structured_info()["relations"]
    archived_entry = next(item for item in relations if item["target_id"] == friend.id)
    assert archived_entry["relation_scope"] == "archived"
    assert archived_entry["numeric_relation"] == "friend"
    assert archived_entry["is_dead"] is True


def test_avatar_manager_archive_death(base_world, dummy_avatar):
    """测试 AvatarManager 的死亡归档逻辑"""
    manager = base_world.avatar_manager
    manager.register_avatar(dummy_avatar)
    
    # 确保初始在活人表
    assert dummy_avatar.id in manager.avatars
    assert dummy_avatar.id not in manager.dead_avatars
    
    # 执行归档
    manager.handle_death(dummy_avatar.id)
    
    # 验证位置转移
    assert dummy_avatar.id not in manager.avatars
    assert dummy_avatar.id in manager.dead_avatars
    
    # 验证 get_avatar 依然能查到
    assert manager.get_avatar(dummy_avatar.id) == dummy_avatar
    
    # 验证 buffer
    assert str(dummy_avatar.id) in manager.pop_newly_dead()

@pytest.mark.asyncio
async def test_simulator_resolve_death(base_world, dummy_avatar):
    """测试模拟器的死亡结算阶段"""
    from src.sim.simulator_engine.phases.lifecycle import phase_resolve_death
    base_world.avatar_manager.register_avatar(dummy_avatar)
    
    # Case 1: 重伤死亡
    dummy_avatar.hp.cur = -10
    
    # 执行死亡结算
    events = phase_resolve_death(base_world, [dummy_avatar])
    
    # 验证
    assert dummy_avatar.is_dead is True
    assert dummy_avatar.death_info["reason"] == "重伤不治身亡"
    assert len(events) > 0
    assert "重伤不治身亡" in str(events[0])
    
    # 验证已被自动归档（因为 handle_death 现在会调用 manager.handle_death）
    assert dummy_avatar.id in base_world.avatar_manager.dead_avatars
    assert str(dummy_avatar.id) in base_world.avatar_manager.pop_newly_dead()
