import pytest
from unittest.mock import MagicMock, AsyncMock, patch
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
            await manager.apply_history_influence("Some history text")
            
            # --- Assertions ---
            
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
