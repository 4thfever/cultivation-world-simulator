import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from src.classes.history import HistoryManager
from src.classes.region import CityRegion, NormalRegion, CultivateRegion
from src.classes.technique import Technique, TechniqueAttribute, TechniqueGrade
from src.classes.weapon import Weapon, WeaponType
from src.classes.auxiliary import Auxiliary
from src.classes.cultivation import Realm
from src.classes.item_registry import ItemRegistry

# 假设这些全局字典在模块层级
from src.classes import technique as technique_module
from src.classes import weapon as weapon_module
# auxiliary 模块没有导出全局字典，所以这里不需要特别处理它的全局字典，只需要处理 ItemRegistry

@pytest.mark.asyncio
async def test_history_influence(base_world):
    # --- Setup Test Data ---
    
    # 1. Regions
    city_region = CityRegion(id=1, name="OldCity", desc="Old Desc")
    normal_region = NormalRegion(id=2, name="OldWild", desc="Old Wild Desc")
    cult_region = CultivateRegion(id=3, name="OldCave", desc="Old Cave Desc")
    
    base_world.map.regions = {
        1: city_region,
        2: normal_region,
        3: cult_region
    }
    
    # 2. Techniques
    tech = Technique(
        id=101,
        name="OldTech",
        attribute=TechniqueAttribute.GOLD,
        grade=TechniqueGrade.LOWER,
        desc="Old Tech Desc",
        weight=1.0,
        condition=""
    )
    
    # 3. Weapons & Auxiliaries
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
    # 使用 patch.dict 来隔离对全局字典的修改
    with patch.dict(technique_module.techniques_by_id, {101: tech}, clear=True), \
         patch.dict(technique_module.techniques_by_name, {"OldTech": tech}, clear=True), \
         patch.dict(weapon_module.weapons_by_name, {"OldSword": weapon}, clear=True), \
         patch.object(ItemRegistry, "_items_by_id", {201: weapon, 301: aux}): # ItemRegistry 是类属性
         
        # --- Prepare LLM Mock Response ---
        mock_response = {
            "city_regions_change": {
                "1": {"name": "NewCity", "desc": "New Desc"}
            },
            "normal_regions_change": {
                "2": {"name": "NewWild", "desc": "New Wild Desc"}
            },
            "cultivate_regions_change": {
                "3": {"name": "NewCave", "desc": "New Cave Desc"}
            },
            "techniques_change": {
                "101": {"name": "NewTech", "desc": "New Tech Desc"}
            },
            "weapons_change": {
                "201": {"name": "NewSword", "desc": "New Sword Desc"}
            },
            "auxiliarys_change": {
                "301": {"name": "NewOrb", "desc": "New Orb Desc"}
            }
        }

        # --- Instantiate Manager & Mock Internal Methods ---
        manager = HistoryManager(base_world)
        
        # Mock _read_csv to return dummy string
        manager._read_csv = MagicMock(return_value="dummy,csv,content")
        
        # Mock call_llm_with_template
        with patch("src.classes.history.call_llm_with_template", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response
            
            # --- Execute ---
            await manager.apply_history_influence("Some history text")
            
            # --- Assertions ---
            
            # 1. LLM Called
            mock_llm.assert_called_once()
            
            # 2. Regions Updated
            assert city_region.name == "NewCity"
            assert city_region.desc == "New Desc"
            assert normal_region.name == "NewWild"
            assert normal_region.desc == "New Wild Desc"
            assert cult_region.name == "NewCave"
            assert cult_region.desc == "New Cave Desc"
            
            # 3. Technique Updated & Index Synced
            assert tech.name == "NewTech"
            assert tech.desc == "New Tech Desc"
            assert "NewTech" in technique_module.techniques_by_name
            assert "OldTech" not in technique_module.techniques_by_name
            assert technique_module.techniques_by_name["NewTech"] == tech
            
            # 4. Weapon Updated & Index Synced
            assert weapon.name == "NewSword"
            assert weapon.desc == "New Sword Desc"
            assert "NewSword" in weapon_module.weapons_by_name
            assert "OldSword" not in weapon_module.weapons_by_name
            assert weapon_module.weapons_by_name["NewSword"] == weapon
            
            # 5. Auxiliary Updated
            assert aux.name == "NewOrb"
            assert aux.desc == "New Orb Desc"

