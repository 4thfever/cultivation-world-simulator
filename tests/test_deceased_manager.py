"""DeceasedManager 单测 + 存读档 + 清理不影响 + 幂等性"""
import pytest
from src.sim.save.save_game import save_game
from src.sim.load.load_game import load_game
from src.classes.death import handle_death
from src.classes.death_reason import DeathReason, DeathType
from src.systems.time import MonthStamp, Month, Year, create_month_stamp


def test_record_death_creates_record(base_world, dummy_avatar):
    """死亡后 DeceasedManager 中有对应记录，字段值正确。"""
    base_world.avatar_manager.register_avatar(dummy_avatar)
    death_time = int(base_world.month_stamp)
    dummy_avatar.set_dead("Test Death", death_time)
    base_world.avatar_manager.handle_death(dummy_avatar.id)
    base_world.deceased_manager.record_death(dummy_avatar)

    record = base_world.deceased_manager.get_record(dummy_avatar.id)
    assert record is not None
    assert record.name == dummy_avatar.name
    assert record.realm_at_death == dummy_avatar.cultivation_progress.realm.value
    assert record.stage_at_death == dummy_avatar.cultivation_progress.stage.value
    assert record.death_reason == "Test Death"
    assert record.death_time == death_time
    assert record.gender == dummy_avatar.gender.value
    assert record.alignment_at_death == str(dummy_avatar.alignment)


def test_record_death_is_idempotent(base_world, dummy_avatar):
    """重复调用 record_death 不会产生重复记录。"""
    base_world.avatar_manager.register_avatar(dummy_avatar)
    death_time = int(base_world.month_stamp)
    dummy_avatar.set_dead("Test", death_time)
    base_world.avatar_manager.handle_death(dummy_avatar.id)

    base_world.deceased_manager.record_death(dummy_avatar)
    base_world.deceased_manager.record_death(dummy_avatar)

    records = base_world.deceased_manager.get_all_records()
    count = sum(1 for r in records if r.id == dummy_avatar.id)
    assert count == 1


def test_get_all_records_sorted_by_death_time_desc(base_world, dummy_avatar):
    """记录按死亡时间倒序排列。"""
    from src.classes.core.avatar import Avatar, Gender
    from src.classes.age import Age
    from src.classes.root import Root
    from src.classes.alignment import Alignment
    from src.systems.cultivation import Realm
    from src.utils.id_generator import get_avatar_id

    base_world.avatar_manager.register_avatar(dummy_avatar)

    # 创建第二个角色
    avatar2 = Avatar(
        world=base_world,
        name="Second",
        id=get_avatar_id(),
        birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
        age=Age(30, Realm.Qi_Refinement, innate_max_lifespan=80),
        gender=Gender.FEMALE,
        pos_x=1,
        pos_y=1,
        root=Root.WATER,
        personas=[],
        alignment=Alignment.EVIL,
    )
    avatar2.personas = []
    avatar2.weapon = None
    base_world.avatar_manager.register_avatar(avatar2)

    # 第一个角色先死
    dummy_avatar.set_dead("First Death", 100)
    base_world.avatar_manager.handle_death(dummy_avatar.id)
    base_world.deceased_manager.record_death(dummy_avatar)

    # 第二个角色后死
    avatar2.set_dead("Second Death", 200)
    base_world.avatar_manager.handle_death(avatar2.id)
    base_world.deceased_manager.record_death(avatar2)

    records = base_world.deceased_manager.get_all_records()
    assert len(records) == 2
    assert records[0].death_time > records[1].death_time


def test_to_save_list_and_load_from_list_roundtrip(base_world, dummy_avatar):
    """序列化/反序列化往返测试。"""
    base_world.avatar_manager.register_avatar(dummy_avatar)
    death_time = int(base_world.month_stamp)
    dummy_avatar.set_dead("Round Trip", death_time)
    base_world.avatar_manager.handle_death(dummy_avatar.id)
    base_world.deceased_manager.record_death(dummy_avatar)

    save_list = base_world.deceased_manager.to_save_list()
    assert len(save_list) == 1

    # 重建一个新 manager 并加载
    from src.sim.managers.deceased_manager import DeceasedManager
    new_manager = DeceasedManager()
    new_manager.load_from_list(save_list)

    loaded = new_manager.get_record(dummy_avatar.id)
    assert loaded is not None
    assert loaded.name == dummy_avatar.name
    assert loaded.realm_at_death == dummy_avatar.cultivation_progress.realm.value
    assert loaded.stage_at_death == dummy_avatar.cultivation_progress.stage.value
    assert loaded.death_reason == "Round Trip"
    assert loaded.death_time == death_time


def test_deceased_records_survive_cleanup(base_world, dummy_avatar):
    """核心业务承诺：cleanup_long_dead_avatars 后 deceased_manager 记录仍在。"""
    death_time = create_month_stamp(Year(1), Month.JANUARY)
    dummy_avatar.set_dead("Old Age", death_time)
    base_world.avatar_manager.register_avatar(dummy_avatar)
    base_world.avatar_manager.handle_death(dummy_avatar.id)
    base_world.deceased_manager.record_death(dummy_avatar)

    # 模拟 20 年后清理
    current_time = create_month_stamp(Year(21), Month.JANUARY)
    base_world.avatar_manager.cleanup_long_dead_avatars(current_time, threshold_years=20)

    # Avatar 对象已被清理
    assert base_world.avatar_manager.get_avatar(dummy_avatar.id) is None
    # 但 DeceasedManager 记录仍在
    assert base_world.deceased_manager.get_record(dummy_avatar.id) is not None
    assert base_world.deceased_manager.get_record(dummy_avatar.id).name == dummy_avatar.name


def test_deceased_records_survive_save_load(base_world, dummy_avatar):
    """存档/读档后 deceased_records 恢复完整。"""
    dummy_avatar.weapon = None
    base_world.avatar_manager.register_avatar(dummy_avatar)

    # 杀死角色
    death_time = int(base_world.month_stamp)
    dummy_avatar.set_dead("Save Load Test", death_time)
    base_world.avatar_manager.handle_death(dummy_avatar.id)
    base_world.deceased_manager.record_death(dummy_avatar)

    # 保存
    from src.sim.simulator import Simulator
    simulator = Simulator(base_world)
    success, save_filename = save_game(base_world, simulator, existed_sects=[])
    assert success

    from src.utils.config import CONFIG
    save_path = CONFIG.paths.saves / save_filename

    # 读取
    loaded_world, loaded_sim, _ = load_game(save_path)

    # 验证已故记录恢复
    record = loaded_world.deceased_manager.get_record(dummy_avatar.id)
    assert record is not None
    assert record.name == dummy_avatar.name
    assert record.death_reason == "Save Load Test"
    assert record.death_time == death_time


def test_empty_deceased_manager_returns_empty_list():
    """空 manager 返回空列表。"""
    from src.sim.managers.deceased_manager import DeceasedManager
    manager = DeceasedManager()
    assert manager.get_all_records() == []
    assert manager.to_save_list() == []
