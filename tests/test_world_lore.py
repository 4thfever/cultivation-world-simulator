from unittest.mock import AsyncMock, patch

import pytest

from src.classes.alignment import Alignment
from src.classes.language import language_manager
from src.classes.core.sect import Sect
from src.classes.items.weapon import Weapon, WeaponType
from src.classes.technique import Technique, TechniqueAttribute, TechniqueGrade
from src.i18n import reload_translations, t
from src.classes.world_lore import WorldLore, WorldLoreManager
from src.classes.world_lore_snapshot import apply_world_lore_snapshot, build_world_lore_snapshot
from src.classes.items.auxiliary import auxiliaries_by_id
from src.classes.items.weapon import weapons_by_id
from src.classes.core.sect import sects_by_id
from src.classes.core.world import World
from src.run.load_map import load_cultivation_world_map
from src.run.data_loader import reload_all_static_data
from src.sim.load.load_game import load_game
from src.sim.save.save_game import save_game
from src.sim.simulator import Simulator
from src.systems.time import Month, Year, create_month_stamp
from src.systems.cultivation import Realm
from src.classes.technique import techniques_by_id

import src.classes.core.sect as sect_module
import src.classes.items.weapon as weapon_module
import src.classes.technique as technique_module

_real_apply_world_lore = WorldLoreManager.apply_world_lore


def test_world_lore_structure(base_world):
    assert isinstance(base_world.world_lore, WorldLore)
    assert base_world.world_lore.text == ""

    lore_text = "这是一个宗门林立、正邪对峙的修仙世界。"
    base_world.set_world_lore(lore_text)
    assert base_world.world_lore.text == lore_text
    assert t("World lore and history") not in base_world.static_info
    assert lore_text not in str(base_world.get_info())


def test_world_lore_static_info_key_is_localized(base_world):
    original_lang = str(language_manager)
    try:
        language_manager._current = "en-US"
        reload_translations()
        base_world.set_world_lore("Sects rise and fall under rewritten heavens.")
        assert "World lore and history" not in base_world.static_info
    finally:
        language_manager._current = original_lang
        reload_translations()


def test_world_lore_manager_updates_indexes(base_world):
    sect = Sect(
        id=1,
        name="旧宗门",
        desc="旧描述",
        member_act_style="",
        alignment=Alignment.RIGHTEOUS,
        headquarter=None,
        technique_names=[],
    )
    technique = Technique(
        id=1,
        name="旧功法",
        attribute=TechniqueAttribute.GOLD,
        grade=TechniqueGrade.LOWER,
        desc="旧功法描述",
        weight=1.0,
        condition="",
    )
    weapon = Weapon(
        id=101,
        name="旧灵剑",
        weapon_type=WeaponType.SWORD,
        realm=Realm.Qi_Refinement,
        desc="旧武器描述",
    )

    manager = WorldLoreManager(base_world)

    with patch.dict(sect_module.sects_by_id, {1: sect}, clear=True), \
         patch.dict(sect_module.sects_by_name, {"旧宗门": sect}, clear=True), \
         patch.dict(technique_module.techniques_by_id, {1: technique}, clear=True), \
         patch.dict(technique_module.techniques_by_name, {"旧功法": technique}, clear=True), \
         patch("src.classes.world_lore.ItemRegistry.get", return_value=weapon), \
         patch.dict(weapon_module.weapons_by_name, {"旧灵剑": weapon}, clear=True):
        manager._apply_sect_lore_changes({"sects_change": {"1": {"name": "新宗门", "desc": "新描述"}}})
        manager._apply_item_lore_changes(
            {
                "techniques_change": {"1": {"name": "新功法", "desc": "新功法描述"}},
                "weapons_change": {"101": {"name": "新灵剑", "desc": "新武器描述"}},
            }
        )

        assert sect.name == "新宗门"
        assert sect.desc == "新描述"
        assert "旧宗门" not in sect_module.sects_by_name
        assert sect_module.sects_by_name["新宗门"] is sect

        assert technique.name == "新功法"
        assert technique.desc == "新功法描述"
        assert "旧功法" not in technique_module.techniques_by_name
        assert technique_module.techniques_by_name["新功法"] is technique

        assert weapon.name == "新灵剑"
        assert weapon.desc == "新武器描述"
        assert "旧灵剑" not in weapon_module.weapons_by_name
        assert weapon_module.weapons_by_name["新灵剑"] is weapon


def test_world_lore_syncs_sect_region_metadata():
    world = World(
        map=load_cultivation_world_map(),
        month_stamp=create_month_stamp(Year(1), Month.JANUARY),
    )
    manager = WorldLoreManager(world)
    sect = next(iter(sects_by_id.values()))
    region = next(r for r in world.map.sect_regions.values() if getattr(r, "sect_id", None) == sect.id)

    manager._apply_sect_lore_changes(
        {
            "sects_change": {str(sect.id): {"name": "太虚宗", "desc": "新的宗门描述"}},
            "sect_regions_change": {str(region.id): {"name": "太虚天宫", "desc": "新的驻地描述"}},
        }
    )

    assert sect.name == "太虚宗"
    assert region.name == "太虚天宫"
    assert region.sect_name == "太虚宗"
    assert sect.headquarter.name == "太虚天宫"
    assert sect.headquarter.desc == "新的驻地描述"
    reload_all_static_data()


@pytest.mark.asyncio
async def test_apply_world_lore_uses_world_lore_tasks(base_world):
    manager = WorldLoreManager(base_world)
    base_world.set_world_lore("旧有 lore 不应混入 world_info")

    async def fake_call(**kwargs):
        task_name = kwargs["task_name"]
        infos = kwargs["infos"]
        assert infos["world_lore"] == "强调门规与正邪格局的世界观"
        assert "旧有 lore 不应混入 world_info" not in infos["world_info"]
        if task_name == "world_lore_map":
            return {"city_regions_change": {}, "normal_regions_change": {}, "cultivate_regions_change": {}}
        if task_name == "world_lore_sect":
            return {"sects_change": {}, "sect_regions_change": {}}
        if task_name == "world_lore_item":
            return {"techniques_change": {}, "weapons_change": {}, "auxiliarys_change": {}}
        raise AssertionError(f"unexpected task: {task_name}")

    with patch("src.classes.world_lore.call_llm_with_task_name", new_callable=AsyncMock) as mock_llm:
        mock_llm.side_effect = fake_call
        with patch.object(WorldLoreManager, "apply_world_lore", new=_real_apply_world_lore):
            await manager.apply_world_lore("强调门规与正邪格局的世界观")

    called_task_names = [call.kwargs["task_name"] for call in mock_llm.await_args_list]
    assert called_task_names == ["world_lore_map", "world_lore_sect", "world_lore_item"]


def test_save_load_preserves_world_lore(base_world, tmp_path):
    base_world.set_world_lore("上古大战后，宗门秩序被重写。")
    simulator = Simulator(base_world)
    save_path = tmp_path / "world_lore_save.json"

    ok, _ = save_game(base_world, simulator, [], save_path)
    assert ok is True

    loaded_world, _, _ = load_game(save_path)
    assert loaded_world.world_lore.text == "上古大战后，宗门秩序被重写。"


def test_world_lore_snapshot_reapplies_static_changes():
    world = World(
        map=load_cultivation_world_map(),
        month_stamp=create_month_stamp(Year(1), Month.JANUARY),
    )
    region_id = next(iter(world.map.regions))
    sect_id = next(iter(sects_by_id))
    technique_id = next(iter(techniques_by_id))
    weapon_id = next(iter(weapons_by_id))
    auxiliary_id = next(iter(auxiliaries_by_id))

    world.map.regions[region_id].name = "太虚古城"
    world.map.regions[region_id].desc = "被改写后的区域描述"
    sects_by_id[sect_id].name = "太虚宗"
    sects_by_id[sect_id].desc = "被改写后的宗门描述"
    techniques_by_id[technique_id].name = "太虚玄功"
    techniques_by_id[technique_id].desc = "被改写后的功法描述"
    weapons_by_id[weapon_id].name = "太虚剑"
    weapons_by_id[weapon_id].desc = "被改写后的兵器描述"
    auxiliaries_by_id[auxiliary_id].name = "太虚佩"
    auxiliaries_by_id[auxiliary_id].desc = "被改写后的辅助装备描述"

    snapshot = build_world_lore_snapshot(world)

    reload_all_static_data()
    fresh_world = World(
        map=load_cultivation_world_map(),
        month_stamp=create_month_stamp(Year(1), Month.JANUARY),
    )
    apply_world_lore_snapshot(fresh_world, snapshot)

    assert fresh_world.map.regions[region_id].name == "太虚古城"
    assert fresh_world.map.regions[region_id].desc == "被改写后的区域描述"
    assert sects_by_id[sect_id].name == "太虚宗"
    assert sects_by_id[sect_id].desc == "被改写后的宗门描述"
    assert techniques_by_id[technique_id].name == "太虚玄功"
    assert weapons_by_id[weapon_id].name == "太虚剑"
    assert auxiliaries_by_id[auxiliary_id].name == "太虚佩"


def test_world_lore_snapshot_rebuilds_sect_metadata_links():
    world = World(
        map=load_cultivation_world_map(),
        month_stamp=create_month_stamp(Year(1), Month.JANUARY),
    )
    sect_id = next(iter(sects_by_id))
    region = next(r for r in world.map.sect_regions.values() if getattr(r, "sect_id", None) == sect_id)

    sects_by_id[sect_id].name = "天机阁"
    sects_by_id[sect_id].desc = "执掌天数与秘闻。"
    region.name = "观星台"
    region.desc = "高台可观九天星象。"

    snapshot = build_world_lore_snapshot(world)

    reload_all_static_data()
    fresh_world = World(
        map=load_cultivation_world_map(),
        month_stamp=create_month_stamp(Year(1), Month.JANUARY),
    )
    apply_world_lore_snapshot(fresh_world, snapshot)

    fresh_region = next(r for r in fresh_world.map.sect_regions.values() if getattr(r, "sect_id", None) == sect_id)
    assert sects_by_id[sect_id].name == "天机阁"
    assert fresh_region.sect_name == "天机阁"
    assert sects_by_id[sect_id].headquarter.name == "观星台"
    assert sects_by_id[sect_id].headquarter.desc == "高台可观九天星象。"
    reload_all_static_data()


def test_save_load_preserves_world_lore_snapshot_after_static_reload(tmp_path):
    world = World(
        map=load_cultivation_world_map(),
        month_stamp=create_month_stamp(Year(1), Month.JANUARY),
    )
    region_id = next(iter(world.map.regions))
    sect_id = next(iter(sects_by_id))
    technique_id = next(iter(techniques_by_id))
    weapon_id = next(iter(weapons_by_id))

    world.set_world_lore("天下格局被重新书写。")
    world.map.regions[region_id].name = "天机城"
    world.map.regions[region_id].desc = "城中遍布观星台。"
    sects_by_id[sect_id].name = "天机阁"
    sects_by_id[sect_id].desc = "执掌天数与秘闻。"
    techniques_by_id[technique_id].name = "天机演道诀"
    techniques_by_id[technique_id].desc = "以星象推衍大道。"
    weapons_by_id[weapon_id].name = "天机尺"
    weapons_by_id[weapon_id].desc = "可定山河方位。"
    world.world_lore_snapshot = build_world_lore_snapshot(world)

    simulator = Simulator(world)
    save_path = tmp_path / "world_lore_snapshot_save.json"
    ok, _ = save_game(world, simulator, [], save_path)
    assert ok is True

    reload_all_static_data()

    loaded_world, _, _ = load_game(save_path)
    assert loaded_world.world_lore.text == "天下格局被重新书写。"
    assert loaded_world.map.regions[region_id].name == "天机城"
    assert loaded_world.map.regions[region_id].desc == "城中遍布观星台。"
    assert sects_by_id[sect_id].name == "天机阁"
    assert sects_by_id[sect_id].desc == "执掌天数与秘闻。"
    assert techniques_by_id[technique_id].name == "天机演道诀"
    assert techniques_by_id[technique_id].desc == "以星象推衍大道。"
    assert weapons_by_id[weapon_id].name == "天机尺"
    assert weapons_by_id[weapon_id].desc == "可定山河方位。"
