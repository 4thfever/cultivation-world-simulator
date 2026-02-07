import pytest
import os
from pathlib import Path
from src.sim.save.save_game import save_game
from src.sim.load.load_game import load_game
from src.classes.core.avatar import Avatar
from src.classes.death_reason import DeathReason, DeathType
from src.systems.time import MonthStamp, Month, Year, create_month_stamp

def test_dead_avatar_stays_dead_after_load(base_world, dummy_avatar):
    """
    测试死亡的角色在读档后是否仍然被正确归类为死者，
    而不是复活出现在活人列表中。
    """
    # 1. 准备环境
    dummy_avatar.weapon = None
    base_world.avatar_manager.register_avatar(dummy_avatar)
    
    assert dummy_avatar.id in base_world.avatar_manager.avatars
    assert dummy_avatar.id not in base_world.avatar_manager.dead_avatars
    assert not dummy_avatar.is_dead
    
    # 2. 杀死角色
    death_time = base_world.month_stamp
    dummy_avatar.set_dead("Test Death", death_time)
    base_world.avatar_manager.handle_death(dummy_avatar.id)
    
    assert dummy_avatar.is_dead
    assert dummy_avatar.id not in base_world.avatar_manager.avatars
    assert dummy_avatar.id in base_world.avatar_manager.dead_avatars
    
    # 3. 保存游戏
    from src.sim.simulator import Simulator
    simulator = Simulator(base_world)
    
    success, save_filename = save_game(base_world, simulator, existed_sects=[])
    assert success
    
    from src.utils.config import CONFIG
    save_path = CONFIG.paths.saves / save_filename
    
    # 4. 读取游戏
    loaded_world, loaded_sim, _ = load_game(save_path)
    
    # 5. 验证读档后的状态
    loaded_avatar = loaded_world.avatar_manager.get_avatar(dummy_avatar.id)
    assert loaded_avatar is not None
    assert loaded_avatar.is_dead
    
    assert loaded_avatar.id not in loaded_world.avatar_manager.avatars, "死者不应出现在活人列表 avatars 中"
    assert loaded_avatar.id in loaded_world.avatar_manager.dead_avatars, "死者应该出现在死者列表 dead_avatars 中"
    
    living_ids = [a.id for a in loaded_world.avatar_manager.get_living_avatars()]
    assert loaded_avatar.id not in living_ids, "死者不应被 get_living_avatars() 返回"

def test_cleanup_long_dead_avatars(base_world, dummy_avatar):
    """
    测试清理死亡超过20年的角色逻辑
    """
    # 1. 准备环境
    base_world.avatar_manager.register_avatar(dummy_avatar)
    
    # 2. 模拟角色死亡（死亡时间为 Year 1, Month 1）
    death_time = create_month_stamp(Year(1), Month.JANUARY)
    dummy_avatar.set_dead("Old Age", death_time)
    base_world.avatar_manager.handle_death(dummy_avatar.id)
    
    assert dummy_avatar.id in base_world.avatar_manager.dead_avatars
    
    # 3. 未满20年，不应清理
    # Year 20, Month 1 (经过19年)
    current_time_19y = create_month_stamp(Year(20), Month.JANUARY)
    cleaned_count = base_world.avatar_manager.cleanup_long_dead_avatars(current_time_19y, threshold_years=20)
    assert cleaned_count == 0
    assert dummy_avatar.id in base_world.avatar_manager.dead_avatars
    
    # 4. 满20年，应清理
    # Year 21, Month 1 (经过20年)
    current_time_20y = create_month_stamp(Year(21), Month.JANUARY)
    cleaned_count = base_world.avatar_manager.cleanup_long_dead_avatars(current_time_20y, threshold_years=20)
    
    assert cleaned_count == 1
    assert dummy_avatar.id not in base_world.avatar_manager.dead_avatars
    assert base_world.avatar_manager.get_avatar(dummy_avatar.id) is None
