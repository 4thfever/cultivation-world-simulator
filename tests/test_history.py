import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path
from src.classes.history import HistoryManager
from src.classes.region import CityRegion, NormalRegion, CultivateRegion, Region
from src.classes.sect_region import SectRegion
from src.classes.technique import Technique, TechniqueAttribute, TechniqueGrade
from src.classes.weapon import Weapon, WeaponType
from src.classes.auxiliary import Auxiliary
from src.classes.cultivation import Realm
from src.classes.item_registry import ItemRegistry
from src.classes.sect import Sect, SectHeadQuarter
from src.classes.alignment import Alignment

# 假设这些全局字典在模块层级
from src.classes import technique as technique_module
from src.classes import weapon as weapon_module
from src.classes import sect as sect_module

def test_world_set_history(base_world):
    """测试 world.set_history 方法和 static_info 中的历史显示"""
    # 初始状态：无历史
    assert base_world.history == ""
    static_info = base_world.static_info
    assert "历史" not in static_info
    
    # 设置历史
    history_text = "这是一段测试历史文本：修仙界曾发生大战，许多宗门覆灭。"
    base_world.set_history(history_text)
    
    # 验证历史已设置
    assert base_world.history == history_text
    
    # 验证 static_info 包含历史
    static_info = base_world.static_info
    assert "历史" in static_info
    assert static_info["历史"] == history_text

@pytest.mark.asyncio
async def test_history_influence(base_world):
    # --- Setup Test Data ---
    
    # 1. Regions
    city_region = CityRegion(id=1, name="OldCity", desc="Old Desc")
    normal_region = NormalRegion(id=2, name="OldWild", desc="Old Wild Desc")
    cult_region = CultivateRegion(id=3, name="OldCave", desc="Old Cave Desc")
    # 假设 ID 4 是宗门驻地在地图上的区域对象
    sect_region_obj = SectRegion(id=4, name="OldSectHQ", desc="Old Sect HQ Desc", sect_name="OldSect", sect_id=1)
    
    base_world.map.regions = {
        1: city_region,
        2: normal_region,
        3: cult_region,
        4: sect_region_obj
    }
    
    # 2. Sects
    sect = Sect(
        id=1,
        name="OldSect",
        desc="Old Sect Desc",
        member_act_style="Old Style",
        alignment=Alignment.RIGHTEOUS,
        headquarter=SectHeadQuarter(name="OldHQ", desc="Old HQ Desc", image=None),
        technique_names=[]
    )

    # 3. Techniques
    tech = Technique(
        id=101,
        name="OldTech",
        attribute=TechniqueAttribute.GOLD,
        grade=TechniqueGrade.LOWER,
        desc="Old Tech Desc",
        weight=1.0,
        condition=""
    )
    
    # 4. Weapons & Auxiliaries
    weapon = Weapon(
        id=201, 
        name="OldSword", 
        weapon_type=WeaponType.SWORD, 
        realm=Realm.Qi_Refinement, 
        desc="Old Sword Desc"
    )
    aux = Auxiliary(
        id=301,
        name="OldOrb",
        realm=Realm.Qi_Refinement,
        desc="Old Orb Desc"
    )

    # --- Patch Global Registries ---
    with patch.dict(technique_module.techniques_by_id, {101: tech}, clear=True), \
         patch.dict(technique_module.techniques_by_name, {"OldTech": tech}, clear=True), \
         patch.dict(weapon_module.weapons_by_name, {"OldSword": weapon}, clear=True), \
         patch.dict(sect_module.sects_by_id, {1: sect}, clear=True), \
         patch.dict(sect_module.sects_by_name, {"OldSect": sect}, clear=True), \
         patch.object(ItemRegistry, "_items_by_id", {201: weapon, 301: aux}): 
         
        # --- Prepare LLM Mock Responses ---
        # Map Task Response
        map_response = {
            "city_regions_change": {"1": {"name": "NewCity", "desc": "New Desc"}},
            "normal_regions_change": {"2": {"name": "NewWild", "desc": "New Wild Desc"}},
            "cultivate_regions_change": {"3": {"name": "NewCave", "desc": "New Cave Desc"}}
        }
        
        # Sect Task Response
        sect_response = {
            "sects_change": {"1": {"name": "NewSect", "desc": "New Sect Desc"}},
            "sect_regions_change": {"4": {"name": "NewSectHQ", "desc": "New Sect HQ Desc"}}
        }
        
        # Item Task Response
        item_response = {
            "techniques_change": {"101": {"name": "NewTech", "desc": "New Tech Desc"}},
            "weapons_change": {"201": {"name": "NewSword", "desc": "New Sword Desc"}},
            "auxiliarys_change": {"301": {"name": "NewOrb", "desc": "New Orb Desc"}}
        }

        def side_effect(**kwargs):
            task_name = kwargs.get("task_name")
            if task_name == "history_influence_map":
                return map_response
            elif task_name == "history_influence_sect":
                return sect_response
            elif task_name == "history_influence_item":
                return item_response
            return {}

        # --- Instantiate Manager & Mock Internal Methods ---
        manager = HistoryManager(base_world)
        manager._read_csv = MagicMock(return_value="dummy,csv,content")
        
        # Mock call_llm_with_task_name
        with patch("src.classes.history.call_llm_with_task_name", new_callable=AsyncMock) as mock_llm:
            mock_llm.side_effect = side_effect
            
            # --- Execute ---
            history_text = "Some history text"
            await manager.apply_history_influence(history_text)
            
            # --- Assertions ---
            
            # 0. World history 未自动设置（需要外部调用 set_history）
            # 注意：apply_history_influence 只应用影响，不设置 history 属性
            # history 属性应该在调用前由外部设置
            
            # 1. LLM Called 3 times
            assert mock_llm.call_count == 3
            
            # 2. Map Regions Updated
            assert city_region.name == "NewCity"
            assert city_region.desc == "New Desc"
            assert normal_region.name == "NewWild"
            assert normal_region.desc == "New Wild Desc"
            assert cult_region.name == "NewCave"
            assert cult_region.desc == "New Cave Desc"
            
            # 3. Sect & Sect Region Updated
            assert sect.name == "NewSect"
            assert sect.desc == "New Sect Desc"
            assert sect_region_obj.name == "NewSectHQ" # 地图上的对象被更新
            assert sect_region_obj.desc == "New Sect HQ Desc"
            
            # 4. Sect Index Synced
            assert "NewSect" in sect_module.sects_by_name
            assert "OldSect" not in sect_module.sects_by_name
            assert sect_module.sects_by_name["NewSect"] == sect

            # 5. Technique Updated & Index Synced
            assert tech.name == "NewTech"
            assert tech.desc == "New Tech Desc"
            assert "NewTech" in technique_module.techniques_by_name
            assert "OldTech" not in technique_module.techniques_by_name
            assert technique_module.techniques_by_name["NewTech"] == tech
            
            # 6. Weapon Updated & Index Synced
            assert weapon.name == "NewSword"
            assert weapon.desc == "New Sword Desc"
            assert "NewSword" in weapon_module.weapons_by_name
            assert "OldSword" not in weapon_module.weapons_by_name
            assert weapon_module.weapons_by_name["NewSword"] == weapon
            
            # 7. Auxiliary Updated
            assert aux.name == "NewOrb"
            assert aux.desc == "New Orb Desc"

@pytest.mark.asyncio
async def test_history_workflow_integration(base_world):
    """测试完整的历史工作流程：设置历史 -> 应用影响"""
    # 准备测试数据
    city_region = CityRegion(id=1, name="测试城", desc="旧描述")
    base_world.map.regions = {1: city_region}
    
    # 模拟初始化时的完整流程
    history_text = "这片大陆曾经历过灵气复苏，修仙宗门林立。"
    
    # 1. 先设置 history（模拟 init_game_async 中的调用）
    base_world.set_history(history_text)
    assert base_world.history == history_text
    
    # 2. 验证 static_info 中包含历史
    static_info = base_world.static_info
    assert "历史" in static_info
    assert static_info["历史"] == history_text
    
    # 3. 应用历史影响（模拟 HistoryManager.apply_history_influence）
    manager = HistoryManager(base_world)
    manager._read_csv = MagicMock(return_value="dummy,csv,content")
    
    map_response = {
        "city_regions_change": {"1": {"name": "灵气城", "desc": "充满灵气的城市"}},
    }
    
    def side_effect(**kwargs):
        task_name = kwargs.get("task_name")
        if task_name == "history_influence_map":
            return map_response
        return {}
    
    with patch("src.classes.history.call_llm_with_task_name", new_callable=AsyncMock) as mock_llm:
        mock_llm.side_effect = side_effect
        
        await manager.apply_history_influence(history_text)
        
        # 4. 验证影响已应用
        assert city_region.name == "灵气城"
        assert city_region.desc == "充满灵气的城市"
        
        # 5. 验证 history 仍然保留
        assert base_world.history == history_text
        
        # 6. 验证 static_info 中仍包含历史
        static_info = base_world.static_info
        assert "历史" in static_info
        assert static_info["历史"] == history_text

def test_history_persistence_in_save_load(base_world, tmp_path):
    """测试 history 在保存和加载时的持久化"""
    from src.sim.save.save_game import save_game
    from src.sim.load.load_game import load_game
    from src.sim.simulator import Simulator
    
    # 设置历史
    history_text = "修仙界的远古历史：曾有强者飞升，留下诸多传承。"
    base_world.set_history(history_text)
    
    # 创建模拟器和宗门列表
    simulator = Simulator(base_world)
    existed_sects = []
    
    # 保存游戏
    save_path = tmp_path / "test_history_save.json"
    success, _ = save_game(base_world, simulator, existed_sects, save_path)
    assert success, "保存游戏应该成功"
    
    # 验证保存文件中包含历史
    import json
    with open(save_path, "r", encoding="utf-8") as f:
        save_data = json.load(f)
    
    world_data = save_data.get("world", {})
    assert "history" in world_data, "保存数据应该包含 history 字段"
    assert world_data["history"] == history_text, "保存的历史文本应该正确"
    
    # 加载游戏
    loaded_world, loaded_sim, loaded_sects = load_game(save_path)
    
    # 验证历史被正确恢复
    assert loaded_world.history == history_text, "加载的世界应该包含历史"
    
    # 验证 static_info 中包含历史
    static_info = loaded_world.static_info
    assert "历史" in static_info, "加载后的 static_info 应该包含历史"
    assert static_info["历史"] == history_text, "加载后的历史文本应该正确"
