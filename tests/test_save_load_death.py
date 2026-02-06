import pytest
import os
from pathlib import Path
from src.sim.save.save_game import save_game
from src.sim.load.load_game import load_game
from src.classes.avatar import Avatar
from src.classes.death_reason import DeathReason, DeathType
from src.classes.calendar import MonthStamp

def test_dead_avatar_stays_dead_after_load(base_world, dummy_avatar):
    """
    测试死亡的角色在读档后是否仍然被正确归类为死者，
    而不是复活出现在活人列表中。
    """
    # 1. 准备环境
    # 移除 mock 武器以支持 JSON 序列化
    dummy_avatar.weapon = None
    
    # 将角色注册到 avatar_manager (dummy_avatar 默认未注册)
    base_world.avatar_manager.register_avatar(dummy_avatar)
    
    # 确认角色是活的
    assert dummy_avatar.id in base_world.avatar_manager.avatars
    assert dummy_avatar.id not in base_world.avatar_manager.dead_avatars
    assert not dummy_avatar.is_dead
    
    # 2. 杀死角色
    # 使用 set_dead 标记死亡
    death_time = base_world.month_stamp
    dummy_avatar.set_dead("Test Death", death_time)
    
    # 使用 handle_death 将其移动到 dead_avatars
    base_world.avatar_manager.handle_death(dummy_avatar.id)
    
    # 验证死亡状态
    assert dummy_avatar.is_dead
    assert dummy_avatar.id not in base_world.avatar_manager.avatars
    assert dummy_avatar.id in base_world.avatar_manager.dead_avatars
    
    # 3. 保存游戏
    # 构造一个模拟器对象 (save_game 需要)
    from src.sim.simulator import Simulator
    simulator = Simulator(base_world)
    
    # 保存
    success, save_filename = save_game(base_world, simulator, existed_sects=[])
    assert success
    assert save_filename is not None
    
    # 获取存档完整路径
    from src.utils.config import CONFIG
    save_path = CONFIG.paths.saves / save_filename
    
    # 4. 读取游戏
    loaded_world, loaded_sim, _ = load_game(save_path)
    
    # 5. 验证读档后的状态
    loaded_avatar = loaded_world.avatar_manager.get_avatar(dummy_avatar.id)
    assert loaded_avatar is not None
    assert loaded_avatar.is_dead
    
    # 关键验证：死者不应该在活人列表中
    # 在 Bug 修复前，这里预期会失败，因为所有角色都被放进了 avatars
    assert loaded_avatar.id not in loaded_world.avatar_manager.avatars, "死者不应出现在活人列表 avatars 中"
    assert loaded_avatar.id in loaded_world.avatar_manager.dead_avatars, "死者应该出现在死者列表 dead_avatars 中"
    
    # 验证 get_living_avatars 不包含该角色
    living_ids = [a.id for a in loaded_world.avatar_manager.get_living_avatars()]
    assert loaded_avatar.id not in living_ids, "死者不应被 get_living_avatars() 返回"
