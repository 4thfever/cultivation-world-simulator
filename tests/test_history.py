import pytest
import json
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path

from src.classes.history import HistoryManager, History
from src.classes.region import CityRegion, NormalRegion, CultivateRegion
from src.classes.sect_region import SectRegion
from src.classes.technique import Technique, TechniqueAttribute, TechniqueGrade
from src.classes.weapon import Weapon, WeaponType
from src.classes.auxiliary import Auxiliary
from src.classes.cultivation import Realm
from src.classes.item_registry import ItemRegistry
from src.classes.sect import Sect, SectHeadQuarter
from src.classes.alignment import Alignment
from src.sim.load.load_game import apply_history_modifications

# 假设这些全局字典在模块层级
from src.classes import technique as technique_module
from src.classes import weapon as weapon_module
from src.classes import sect as sect_module
from src.classes import auxiliary as auxiliary_module

# --- 1. 基础数据结构测试 (Plan 1) ---

def test_world_history_structure(base_world):
    """
    目标：验证 World 与 History dataclass 的交互是否符合预期。
    """
    # 初始化：验证 world.history 是否自动初始化为空的 History 对象
    assert isinstance(base_world.history, History)
    assert base_world.history.text == ""
    assert base_world.history.modifications == {}

    # 设置文本：验证 text 更新
    history_text = "修仙界风云变幻"
    base_world.set_history(history_text)
    assert base_world.history.text == history_text

    # 记录差分：验证 record_modification
    # 第一次记录
    base_world.record_modification("sects", "1", {"name": "新名字"})
    assert "sects" in base_world.history.modifications
    assert "1" in base_world.history.modifications["sects"]
    assert base_world.history.modifications["sects"]["1"]["name"] == "新名字"

    # 第二次记录：验证合并 (Merge)
    base_world.record_modification("sects", "1", {"desc": "新描述"})
    assert base_world.history.modifications["sects"]["1"]["name"] == "新名字" # 旧属性保留
    assert base_world.history.modifications["sects"]["1"]["desc"] == "新描述" # 新属性添加

    # 第三次记录：验证覆盖 (Override)
    base_world.record_modification("sects", "1", {"name": "更新的名字"})
    assert base_world.history.modifications["sects"]["1"]["name"] == "更新的名字"


# --- 2. 修改记录行为测试 (Plan 2) ---

def test_history_manager_records_changes(base_world):
    """
    目标：验证 HistoryManager 在修改对象时，是否自动产生“留痕”。
    """
    # Setup
    sect = Sect(id=1, name="OldSect", desc="OldDesc", member_act_style="", alignment=Alignment.RIGHTEOUS, headquarter=None, technique_names=[])
    manager = HistoryManager(base_world)
    
    # Execute Modification
    # 模拟 _update_obj_attrs 的调用
    changes = {"name": "NewSect", "desc": "NewDesc"}
    manager._update_obj_attrs(sect, changes, category="sects", id_str="1")

    # Verify Object Updated
    assert sect.name == "NewSect"
    assert sect.desc == "NewDesc"

    # Verify History Recorded
    assert "sects" in base_world.history.modifications
    assert "1" in base_world.history.modifications["sects"]
    recorded_change = base_world.history.modifications["sects"]["1"]
    assert recorded_change["name"] == "NewSect"
    assert recorded_change["desc"] == "NewDesc"


# --- 3. 差分回放逻辑测试 (Plan 3) ---

def test_apply_history_modifications_logic(base_world):
    """
    目标：验证 apply_history_modifications 函数能否将数据字典正确应用到静态对象上。
    """
    # Setup Objects
    sect = Sect(id=1, name="OriginalSect", desc="OriginalDesc", member_act_style="", alignment=Alignment.RIGHTEOUS, headquarter=None, technique_names=[])
    weapon = Weapon(id=101, name="OriginalSword", weapon_type=WeaponType.SWORD, realm=Realm.Qi_Refinement, desc="OriginalDesc")
    
    # Patch Global Registries
    with patch.dict(sect_module.sects_by_id, {1: sect}, clear=True), \
         patch.dict(sect_module.sects_by_name, {"OriginalSect": sect}, clear=True), \
         patch.object(ItemRegistry, "get", return_value=weapon), \
         patch.dict(weapon_module.weapons_by_name, {"OriginalSword": weapon}, clear=True):

        # Construct Modifications
        modifications = {
            "sects": {
                "1": {"name": "ReplayedSect", "desc": "ReplayedDesc"},
                "999": {"name": "GhostSect"} # 不存在的 ID，应忽略
            },
            "weapons": {
                "101": {"name": "ReplayedSword"}
            }
        }

        # Execute Replay
        apply_history_modifications(base_world, modifications)

        # Verify Sect Updated
        assert sect.name == "ReplayedSect"
        assert sect.desc == "ReplayedDesc"
        
        # Verify Sect Index Synced (Old name removed, new name added)
        assert "OriginalSect" not in sect_module.sects_by_name
        assert "ReplayedSect" in sect_module.sects_by_name
        assert sect_module.sects_by_name["ReplayedSect"] == sect

        # Verify Weapon Updated
        assert weapon.name == "ReplayedSword"
        assert weapon.desc == "OriginalDesc" # Unchanged
        
        # Verify Weapon Index Synced
        assert "OriginalSword" not in weapon_module.weapons_by_name
        assert "ReplayedSword" in weapon_module.weapons_by_name


# --- 4. 集成测试：存读档全流程 (Plan 4) ---

def test_save_load_integration_with_history(base_world, tmp_path):
    """
    目标：模拟真实游戏场景，验证“修改 -> 存档 -> 重置 -> 读档 -> 还原”的闭环。
    """
    from src.sim.save.save_game import save_game
    from src.sim.load.load_game import load_game
    from src.sim.simulator import Simulator
    
    # 1. Setup Initial State
    sect = Sect(id=1, name="OriginalSect", desc="OriginalDesc", member_act_style="", alignment=Alignment.RIGHTEOUS, headquarter=None, technique_names=[])
    
    # Patch 全局状态，模拟游戏运行环境
    with patch.dict(sect_module.sects_by_id, {1: sect}, clear=True), \
         patch.dict(sect_module.sects_by_name, {"OriginalSect": sect}, clear=True):
        
        # 2. Apply Changes & Record History
        history_text = "History Text"
        base_world.set_history(history_text)
        
        # 模拟 HistoryManager 的修改操作
        sect.name = "ModifiedSect"
        base_world.record_modification("sects", "1", {"name": "ModifiedSect"})
        # 此时内存中是 ModifiedSect
        
        simulator = Simulator(base_world)
        existed_sects = [sect]

        # 3. Save Game
        save_path = tmp_path / "integration_save.json"
        save_game(base_world, simulator, existed_sects, save_path)

        # 4. Reset Memory (Simulate Restart)
        # 将对象重置为原始状态，模拟重新加载配置文件的过程
        sect.name = "OriginalSect" 
        if "ModifiedSect" in sect_module.sects_by_name:
            del sect_module.sects_by_name["ModifiedSect"]
        sect_module.sects_by_name["OriginalSect"] = sect
        
        assert sect.name == "OriginalSect" # 确认重置成功

        # 5. Load Game
        # load_game 会调用 apply_history_modifications
        # 注意：load_game 内部会导入 sects_by_id，我们已经在 patch 中了，所以 load_game 会看到我们 patch 的 dict
        # 但 load_game 会重建 world，所以我们需要验证 loaded_world
        
        loaded_world, _, _ = load_game(save_path)

        # 6. Verify
        # 验证历史文本
        assert loaded_world.history.text == history_text
        
        # 验证 Modifications 数据存在
        assert "sects" in loaded_world.history.modifications
        assert loaded_world.history.modifications["sects"]["1"]["name"] == "ModifiedSect"

        # 核心验证：内存中的对象是否变回了 ModifiedSect
        # 因为我们 patch 了全局字典，load_game 回放时修改的就是这个全局字典里的 sect 对象
        assert sect.name == "ModifiedSect"
        assert "ModifiedSect" in sect_module.sects_by_name
        assert "OriginalSect" not in sect_module.sects_by_name


# --- 5. 边界情况测试 (Plan 5) ---

def test_history_boundary_cases(base_world, tmp_path):
    """
    目标：边界情况测试
    """
    from src.sim.save.save_game import save_game
    from src.sim.load.load_game import load_game
    from src.sim.simulator import Simulator

    # Case 1: Empty History
    # 保存一个没有历史修改的存档
    simulator = Simulator(base_world)
    save_path = tmp_path / "empty_history.json"
    save_game(base_world, simulator, [], save_path)
    
    # 读档应不报错
    loaded_world, _, _ = load_game(save_path)
    assert loaded_world.history.text == ""
    assert loaded_world.history.modifications == {}

    # Case 2: Corrupted/Partial Modification Data (Manual JSON edit)
    # 创建一个手动修改的 JSON，模拟数据损坏或旧版本残留
    with open(save_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # 注入一个格式奇怪的 modifications
    data["world"]["history"] = {
        "text": "Partial",
        "modifications": {
            "sects": {
                "invalid_id": {"name": "ShouldNotCrash"} # ID 不是数字，但 key 是 str
            },
            "unknown_category": { # 未知类别
                "1": {"name": "???"}
            }
        }
    }
    
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(data, f)

    # 读档应鲁棒处理，不崩溃
    loaded_world_2, _, _ = load_game(save_path)
    assert loaded_world_2.history.text == "Partial"
    
    # 确保未知类别被加载（作为数据），但在 apply 时被忽略（不报错）
    assert "unknown_category" in loaded_world_2.history.modifications

