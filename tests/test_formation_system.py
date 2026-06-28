import json
from unittest.mock import patch

from src.classes.action.param_options import build_param_options
from src.classes.action.set_formation import SetFormation
from src.classes.age import Age
from src.classes.core.avatar import Avatar, Gender
from src.classes.environment.lode import Lode
from src.classes.environment.plant import Plant
from src.classes.environment.region import CultivateRegion, NormalRegion
from src.classes.environment.tile import Tile, TileType
from src.classes.items.auxiliary import auxiliaries_by_id
from src.classes.material import Material
from src.classes.persona import personas_by_name
from src.classes.root import Root
from src.sim.load.load_game import load_game
from src.sim.save.save_game import save_game
from src.sim.simulator import Simulator
from src.systems.battle import get_effective_strength
from src.systems.cultivation import Realm
from src.systems.formation import (
    FORMATION_BEAST_DRIVING,
    FORMATION_CLARITY,
    FORMATION_HEALING,
    FORMATION_MOUNTAIN_GUARD,
    FORMATION_SPIRIT_GATHERING,
    FORMATION_VEIN_SEEKING,
    FORMATION_WOOD_GROWTH,
    cleanup_expired_region_formations,
    get_available_formation_type_options,
)
from src.systems.time import Month, Year, create_month_stamp
from src.utils.gather import execute_gather
from src.utils.id_generator import get_avatar_id


def _equip_disk(avatar, item_id=2082):
    avatar.auxiliary = auxiliaries_by_id[item_id].instantiate()
    avatar.recalc_effects()


def _place_avatar_in_region(base_world, avatar, region, *, tile_type=TileType.PLAIN):
    tile = Tile(0, 0, tile_type)
    tile.region = region
    avatar.tile = tile
    base_world.map.tiles[(0, 0)] = tile
    base_world.map.regions[region.id] = region
    base_world.map.region_cors[region.id] = getattr(region, "cors", []) or [(0, 0)]


def test_set_formation_requires_disk_region_and_spirit_stones(dummy_avatar, base_world):
    region = CultivateRegion(id=301, name="青云洞府", desc="", cors=[(0, 0)])
    _place_avatar_in_region(base_world, dummy_avatar, region, tile_type=TileType.CAVE)
    dummy_avatar.magic_stone = 1000
    action = SetFormation(dummy_avatar, base_world)

    ok, reason = action.can_start(FORMATION_SPIRIT_GATHERING)
    assert ok is False
    assert "阵盘" in reason

    _equip_disk(dummy_avatar, 2081)
    dummy_avatar.magic_stone = 1
    ok, reason = action.can_start(FORMATION_SPIRIT_GATHERING)
    assert ok is False
    assert "灵石" in reason

    dummy_avatar.magic_stone = 1000
    ok, reason = action.can_start(FORMATION_SPIRIT_GATHERING)
    assert ok is True
    assert reason == ""


def test_formation_options_are_limited_to_current_region(dummy_avatar, base_world):
    material = Material(id=9901, name="测试矿", desc="", realm=Realm.Qi_Refinement)
    lode = Lode(id=9902, name="测试矿脉", realm=Realm.Qi_Refinement, desc="")
    lode.materials = [material]
    region = NormalRegion(id=101, name="矿山", desc="", lode_ids=[], cors=[(0, 0)])
    region.lodes = [lode]
    region.plants = []
    region.animals = []
    _place_avatar_in_region(base_world, dummy_avatar, region)
    _equip_disk(dummy_avatar)

    options = get_available_formation_type_options(dummy_avatar)

    assert {option["value"] for option in options} == {FORMATION_VEIN_SEEKING}
    assert options[0]["value"] == FORMATION_VEIN_SEEKING
    assert "cost" in options[0]
    assert "effect_desc" in options[0]

    param_options = build_param_options(SetFormation, dummy_avatar)
    assert param_options["formation_type"][0]["value"] == FORMATION_VEIN_SEEKING


def test_set_formation_places_and_replaces_region_formation(dummy_avatar, base_world):
    region = CultivateRegion(id=301, name="青云洞府", desc="", cors=[(0, 0)])
    _place_avatar_in_region(base_world, dummy_avatar, region, tile_type=TileType.CAVE)
    _equip_disk(dummy_avatar, 2082)
    dummy_avatar.magic_stone = 1000
    action = SetFormation(dummy_avatar, base_world)

    with patch("random.randint", return_value=0):
        action._execute(FORMATION_SPIRIT_GATHERING)

    first = base_world.map.region_formations[301]
    assert first["formation_type"] == FORMATION_SPIRIT_GATHERING
    assert first["duration"] == 24
    assert first["effects"]["extra_respire_exp_multiplier"] == 0.18
    assert int(dummy_avatar.magic_stone) == 688

    with patch("random.randint", return_value=0):
        action._execute(FORMATION_HEALING)

    second = base_world.map.region_formations[301]
    assert second["formation_type"] == FORMATION_HEALING
    assert FORMATION_SPIRIT_GATHERING != second["formation_type"]
    assert action._last_replaced is True


def test_formation_personas_modify_power_duration_and_cost(dummy_avatar, base_world):
    region = CultivateRegion(id=301, name="青云洞府", desc="", cors=[(0, 0)])
    _place_avatar_in_region(base_world, dummy_avatar, region, tile_type=TileType.CAVE)
    _equip_disk(dummy_avatar, 2081)
    dummy_avatar.personas = [personas_by_name["阵仙"]]
    dummy_avatar.recalc_effects()
    dummy_avatar.magic_stone = 1000

    action = SetFormation(dummy_avatar, base_world)
    with patch("random.randint", return_value=0):
        action._execute(FORMATION_SPIRIT_GATHERING)

    formation = base_world.map.region_formations[301]
    assert formation["duration"] == 30
    assert formation["cost"] == 94
    assert formation["effects"]["extra_respire_exp_multiplier"] == 0.135


def test_cleanup_expired_region_formations(dummy_avatar, base_world):
    region = CultivateRegion(id=301, name="青云洞府", desc="", cors=[(0, 0)])
    _place_avatar_in_region(base_world, dummy_avatar, region, tile_type=TileType.CAVE)
    base_world.map.region_formations[301] = {
        "formation_type": FORMATION_SPIRIT_GATHERING,
        "start_month": 0,
        "duration": 1,
        "effects": {},
    }

    cleanup_expired_region_formations(base_world, 1)

    assert base_world.map.region_formations == {}


def test_region_formations_affect_gather_and_battle(dummy_avatar, base_world):
    material = Material(id=9901, name="测试矿", desc="", realm=Realm.Qi_Refinement)
    lode = Lode(id=9902, name="测试矿脉", realm=Realm.Qi_Refinement, desc="")
    lode.materials = [material]
    region = NormalRegion(id=101, name="矿山", desc="", lode_ids=[], cors=[(0, 0)])
    region.lodes = [lode]
    _place_avatar_in_region(base_world, dummy_avatar, region)
    base_world.map.region_formations[101] = {
        "formation_type": FORMATION_VEIN_SEEKING,
        "start_month": int(base_world.month_stamp),
        "duration": 12,
        "effects": {"extra_mine_materials": 2},
    }

    with patch("random.choice", side_effect=[lode, material]):
        gained = execute_gather(dummy_avatar, "lodes", "extra_mine_materials")

    assert gained == {"测试矿": 3}

    opponent = Avatar(
        world=base_world,
        name="Opponent",
        id=get_avatar_id(),
        birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
        age=Age(20, Realm.Qi_Refinement),
        gender=Gender.FEMALE,
        pos_x=0,
        pos_y=0,
        root=Root.WOOD,
        personas=[],
    )
    opponent.personas = []
    opponent.recalc_effects()
    opponent.tile = dummy_avatar.tile
    base_world.map.region_formations[101] = {
        "formation_type": FORMATION_MOUNTAIN_GUARD,
        "start_month": int(base_world.month_stamp),
        "duration": 12,
        "effects": {"extra_battle_strength_points": 4},
    }

    assert get_effective_strength(dummy_avatar, opponent) == 14.0


def test_healing_formation_affects_passive_hp_recovery(dummy_avatar, base_world):
    region = CultivateRegion(id=301, name="青云洞府", desc="", cors=[(0, 0)])
    _place_avatar_in_region(base_world, dummy_avatar, region, tile_type=TileType.CAVE)
    dummy_avatar.hp.max = 200
    dummy_avatar.hp.cur = 100
    base_world.map.region_formations[301] = {
        "formation_type": FORMATION_HEALING,
        "start_month": int(base_world.month_stamp),
        "duration": 12,
        "effects": {"extra_hp_recovery_rate": 1.0},
    }

    dummy_avatar.update_time_effect()

    assert dummy_avatar.hp.cur == 104


def test_region_formations_are_saved_and_loaded(dummy_avatar, base_world, tmp_path):
    region = CultivateRegion(id=301, name="青云洞府", desc="", cors=[(0, 0)])
    _place_avatar_in_region(base_world, dummy_avatar, region, tile_type=TileType.CAVE)
    dummy_avatar.weapon = None
    dummy_avatar.auxiliary = None
    base_world.avatar_manager.register_avatar(dummy_avatar)
    base_world.map.region_formations[301] = {
        "formation_type": FORMATION_CLARITY,
        "caster_id": str(dummy_avatar.id),
        "disk_item_id": 2081,
        "start_month": int(base_world.month_stamp),
        "duration": 12,
        "effects": {"extra_breakthrough_success_rate": 0.03},
        "cost": 104,
    }
    base_world.run_config_snapshot = {
        "content_locale": "zh-CN",
        "map_id": "classic",
        "init_npc_num": 0,
        "sect_num": 0,
        "npc_awakening_rate_per_month": 0.01,
        "world_lore": "",
    }
    sim = Simulator(base_world)
    save_path = tmp_path / "formation_save.json"

    success, _ = save_game(base_world, sim, [], save_path=save_path)
    assert success
    with open(save_path, "r", encoding="utf-8") as f:
        save_data = json.load(f)
    assert save_data["world"]["region_formations"]["301"]["formation_type"] == FORMATION_CLARITY

    loaded_world, _, _ = load_game(save_path)
    assert loaded_world.map.region_formations[301]["formation_type"] == FORMATION_CLARITY
