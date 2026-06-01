from src.run.load_map import load_cultivation_world_map
from src.run.map_presets import list_map_presets
from src.run.map_snapshot import load_map_from_snapshot, serialize_map_snapshot
from src.classes.core.world import World
from src.server.runtime.session import GameSessionRuntime, create_default_game_state
from src.server.services.game_queries import get_world_map
from src.systems.time import Month, Year, create_month_stamp
from src.classes.language import language_manager
from src.i18n import reload_translations


def test_official_map_presets_load_with_uniform_size():
    presets = list_map_presets()
    assert [preset.id for preset in presets] == ["classic", "island_seas", "mountain_frontier"]

    region_sets = []
    for preset in presets:
        game_map = load_cultivation_world_map(preset.id)
        assert game_map.width == 84
        assert game_map.height == 60
        assert game_map.map_id == preset.id
        assert game_map.map_name == preset.name
        assert game_map.preset_version == preset.version
        assert game_map.regions
        region_sets.append(set(game_map.regions))

    assert all(region_set == region_sets[0] for region_set in region_sets)


def test_map_snapshot_round_trip_restores_tiles_and_regions():
    game_map = load_cultivation_world_map("island_seas")
    snapshot = serialize_map_snapshot(game_map)

    assert snapshot["schema_version"] == 1
    assert snapshot["preset_id"] == "island_seas"
    assert snapshot["width"] == 84
    assert snapshot["height"] == 60
    assert len(snapshot["tile_rows"]) == 60
    assert len(snapshot["region_rows"]) == 60

    restored = load_map_from_snapshot(snapshot)
    assert restored.map_id == "island_seas"
    assert restored.width == game_map.width
    assert restored.height == game_map.height
    assert set(restored.regions) == set(game_map.regions)

    for y in range(game_map.height):
        for x in range(game_map.width):
            original_tile = game_map.get_tile(x, y)
            restored_tile = restored.get_tile(x, y)
            assert restored_tile.type == original_tile.type
            assert (restored_tile.region.id if restored_tile.region else -1) == (
                original_tile.region.id if original_tile.region else -1
            )


def test_public_map_data_uses_renderable_tile_types():
    for preset in list_map_presets():
        runtime = GameSessionRuntime(create_default_game_state())
        world = World(
            map=load_cultivation_world_map(preset.id),
            month_stamp=create_month_stamp(Year(1), Month.JANUARY),
        )
        runtime.update({"world": world})

        response = get_world_map(runtime, sects_by_id={}, render_config={})
        tile_types = {tile_type for row in response["data"] for tile_type in row}

        assert "CAVE" not in tile_types
        assert "RUIN" not in tile_types
        assert "SECT" not in tile_types


def test_map_presets_are_localized():
    original_language = str(language_manager)
    try:
        language_manager.set_language("en-US")
        reload_translations()
        presets = {preset.id: preset.to_dict() for preset in list_map_presets()}
        assert presets["classic"]["name"] == "Central Nine Provinces"
        assert presets["island_seas"]["name"] == "Azure Isles"
        assert presets["mountain_frontier"]["size_label"] == "Medium"
    finally:
        language_manager.set_language(original_language)
        reload_translations()
