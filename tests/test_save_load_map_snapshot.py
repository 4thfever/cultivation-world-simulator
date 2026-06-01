import json

from src.classes.core.world import World
from src.sim.load.load_game import load_game
from src.sim.save.save_game import save_game
from src.sim.simulator import Simulator
from src.systems.time import Month, Year, create_month_stamp
from src.run.load_map import load_cultivation_world_map


def test_save_writes_full_map_snapshot(tmp_path):
    game_map = load_cultivation_world_map("mountain_frontier")
    world = World.create_with_db(
        map=game_map,
        month_stamp=create_month_stamp(Year(1), Month.JANUARY),
        events_db_path=tmp_path / "map_snapshot_events.db",
    )
    world.run_config_snapshot = {
        "content_locale": "zh-CN",
        "map_id": "mountain_frontier",
        "init_npc_num": 0,
        "sect_num": 0,
        "npc_awakening_rate_per_month": 0.01,
        "world_lore": "",
    }
    sim = Simulator(world)

    save_path = tmp_path / "map_snapshot.json"
    success, _ = save_game(world, sim, [], save_path=save_path)
    assert success

    with open(save_path, "r", encoding="utf-8") as f:
        save_data = json.load(f)

    snapshot = save_data["world"]["map_snapshot"]
    assert save_data["run_config"]["map_id"] == "mountain_frontier"
    assert save_data["meta"]["map_id"] == "mountain_frontier"
    assert snapshot["preset_id"] == "mountain_frontier"
    assert snapshot["width"] == 84
    assert snapshot["height"] == 60
    assert snapshot["schema_version"] == 2
    assert snapshot["wilderness_tile"] == "plain"
    assert len(snapshot["region_rows"]) == 60
    assert snapshot["landmarks"]


def test_load_prefers_map_snapshot_over_run_config_map_id(tmp_path):
    game_map = load_cultivation_world_map("island_seas")
    world = World.create_with_db(
        map=game_map,
        month_stamp=create_month_stamp(Year(1), Month.JANUARY),
        events_db_path=tmp_path / "load_snapshot_events.db",
    )
    world.run_config_snapshot = {
        "content_locale": "zh-CN",
        "map_id": "classic",
        "init_npc_num": 0,
        "sect_num": 0,
        "npc_awakening_rate_per_month": 0.01,
        "world_lore": "",
    }
    sim = Simulator(world)

    save_path = tmp_path / "load_snapshot.json"
    success, _ = save_game(world, sim, [], save_path=save_path)
    assert success

    loaded_world, loaded_sim, loaded_sects = load_game(save_path)
    assert loaded_world.map.map_id == "island_seas"
    assert loaded_world.map.width == 84
    assert loaded_world.map.height == 60
    assert loaded_world.run_config_snapshot["map_id"] == "classic"
    assert loaded_sim is not None
    assert loaded_sects == []
