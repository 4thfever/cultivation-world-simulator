from unittest.mock import AsyncMock, patch

import pytest

from src.classes.world_secret import (
    DISCLOSURE_SHARE_ALL,
    WORLD_SECRET_NONE_ID,
)
from src.run.load_map import load_cultivation_world_map
from src.sim.load.load_game import load_game
from src.sim.save.save_game import save_game
from src.sim.simulator import Simulator
from src.systems.single_choice import ChoiceSource, SingleChoiceDecision, SingleChoiceOutcome
from src.systems.time import Month, Year, create_month_stamp
from src.systems.world_secret import (
    TRIGGER_KIND_REGION,
    avatar_knows_full_secret,
    build_avatar_world_secret_ai_context,
    build_world_secret_overview,
    get_avatar_secret_knowledge,
    get_world_secret_definition,
    get_world_secret_options,
    initialize_world_secret,
    load_world_secret_definitions,
    sync_avatar_public_world_secret_knowledge,
    try_discover_world_secret_fragments,
)


def test_world_secret_loader_includes_none_random_and_fragments():
    definitions = load_world_secret_definitions()
    options = get_world_secret_options()

    assert WORLD_SECRET_NONE_ID in definitions
    assert options[0] == {"id": "none", "title": "无"}
    assert options[1] == {"id": "random", "title": "随机"}
    assert "fake_sky" in definitions
    assert len(definitions["fake_sky"].fragments) == 6
    assert {fragment.trigger_kind for fragment in definitions["fake_sky"].fragments} >= {"region", "city", "insight"}


def test_world_secret_content_uses_localized_game_config_overrides():
    import csv
    from pathlib import Path

    checks = {
        "en-US": ("This World's Sky Is False", "Misaligned Stars"),
        "zh-TW": ("本世界的天空是虛假的", "星辰錯位"),
        "ja-JP": ("この世界の空は偽物である", "星辰のずれ"),
        "vi-VN": ("Bầu trời của thế giới này là giả", "Sao trời lệch vị"),
        "fr-FR": ("Le ciel de ce monde est faux", "Étoiles décalées"),
    }
    locales_dir = Path("static/locales")

    for locale, (expected_title, expected_angle) in checks.items():
        secret_path = locales_dir / locale / "game_configs" / "world_secret.csv"
        fragment_path = locales_dir / locale / "game_configs" / "world_secret_fragment.csv"
        secret_rows = list(csv.DictReader(secret_path.open(encoding="utf-8", newline="")))
        fragment_rows = list(csv.DictReader(fragment_path.open(encoding="utf-8", newline="")))
        secret_by_id = {row["id"]: row for row in secret_rows}
        fragment_by_id = {row["id"]: row for row in fragment_rows}

        assert len(secret_rows) == 14
        assert len(fragment_rows) == 73
        assert secret_by_id["fake_sky"]["title"] == expected_title
        assert fragment_by_id["fake_sky_1"]["angle"] == expected_angle
        if locale in {"ja-JP", "vi-VN", "fr-FR"}:
            assert secret_by_id["fake_sky"]["title"] != "This World's Sky Is False"
        if locale == "zh-TW":
            assert "虚" not in secret_by_id["fake_sky"]["title"]
            assert "错" not in fragment_by_id["fake_sky_1"]["angle"]


def test_world_secret_runtime_text_is_localized(dummy_avatar):
    from src.classes.language import language_manager
    from src.systems.world_secret import WorldSecretDisclosureScenario
    from src.utils.df import reload_game_configs

    world = _world_with_classic_map()
    avatar = dummy_avatar
    avatar.world = world
    avatar.weapon = None
    world.avatar_manager.avatars[avatar.id] = avatar

    try:
        language_manager.set_language("fr-FR")
        reload_game_configs()
        runtime = initialize_world_secret(world, "fake_sky")
        definition = get_world_secret_definition("fake_sky")
        fragment = next(item for item in definition.fragments if item.trigger_kind == TRIGGER_KIND_REGION)
        region = world.map.regions[runtime.trigger_bindings[fragment.id].region_id]
        avatar.pos_x, avatar.pos_y = region.center_loc
        avatar.tile = world.map.get_tile(avatar.pos_x, avatar.pos_y)

        event = __import__("src.systems.world_secret", fromlist=["_build_discovery_event"])._build_discovery_event(
            world, avatar, fragment
        )
        request = WorldSecretDisclosureScenario(world, avatar, definition).build_request()

        assert "a remarqué un indice inhabituel" in event.content
        assert "察觉" not in event.content
        assert request.title == "Révéler le secret du monde ?"
        assert request.options[0].title == "Le dire à tous"
        assert request.options[1].title == "Le porter en silence"
        assert "是否公开" not in request.title
    finally:
        language_manager.set_language("zh-CN")
        reload_game_configs()


def test_initialize_world_secret_none_and_specific_bindings():
    world = _world_with_classic_map()

    runtime = initialize_world_secret(world, "none")
    assert runtime.selected_secret_id == "none"
    assert runtime.trigger_bindings == {}

    runtime = initialize_world_secret(world, "fake_sky")
    definition = get_world_secret_definition("fake_sky")

    assert runtime.selected_secret_id == "fake_sky"
    assert definition is not None
    assert set(runtime.trigger_bindings) == {fragment.id for fragment in definition.fragments}
    for fragment in definition.fragments:
        binding = runtime.trigger_bindings[fragment.id]
        if fragment.trigger_kind == "city":
            assert binding.city_region_id is not None
        if fragment.trigger_kind == "region":
            assert binding.region_id is not None


@pytest.mark.asyncio
async def test_fragment_discovery_adds_event_and_ai_context_hides_title(dummy_avatar):
    world = _world_with_classic_map()
    avatar = dummy_avatar
    avatar.world = world
    avatar.weapon = None
    world.avatar_manager.avatars[avatar.id] = avatar
    runtime = initialize_world_secret(world, "fake_sky")
    definition = get_world_secret_definition("fake_sky")
    fragment = next(item for item in definition.fragments if item.trigger_kind == TRIGGER_KIND_REGION)
    binding = runtime.trigger_bindings[fragment.id]
    region = world.map.regions[binding.region_id]
    avatar.pos_x, avatar.pos_y = region.center_loc
    avatar.tile = world.map.get_tile(avatar.pos_x, avatar.pos_y)

    with patch("src.systems.world_secret.random.random", return_value=0.0):
        events = await try_discover_world_secret_fragments(world, avatar)

    knowledge = get_avatar_secret_knowledge(avatar, "fake_sky")
    context = build_avatar_world_secret_ai_context(avatar)

    assert fragment.id in knowledge.known_fragment_ids
    assert any(event.event_type == "world_secret_fragment_discovered" for event in events)
    assert context is not None
    assert context["known_fragments"]
    assert "secret_title" not in context
    assert context["full_secret"] == ""


@pytest.mark.asyncio
async def test_full_secret_share_public_syncs_all_avatars(dummy_avatar):
    world = _world_with_classic_map()
    avatar = dummy_avatar
    avatar.world = world
    world.avatar_manager.avatars[avatar.id] = avatar
    other = _clone_avatar_for_world(dummy_avatar, world, "other-secret-knower")
    world.avatar_manager.avatars[other.id] = other
    initialize_world_secret(world, "fake_sky")
    definition = get_world_secret_definition("fake_sky")
    knowledge = get_avatar_secret_knowledge(avatar, "fake_sky")
    knowledge.known_fragment_ids = {fragment.id for fragment in definition.fragments}

    async def fake_resolve(_scenario):
        decision = SingleChoiceDecision(
            selected_key=DISCLOSURE_SHARE_ALL,
            thinking="公开真相",
            source=ChoiceSource.LLM,
            raw_response=None,
            used_fallback=False,
        )
        return await _scenario.apply_decision(decision)

    with patch("src.systems.world_secret.resolve_single_choice", new_callable=AsyncMock) as mock_resolve:
        mock_resolve.side_effect = fake_resolve
        events = await try_discover_world_secret_fragments(world, avatar)

    assert any(event.event_type == "world_secret_resolved" for event in events)
    assert any(event.event_type == "world_secret_public_revealed" for event in events)
    assert world.world_secret.public_revealed is True
    assert avatar_knows_full_secret(other, "fake_sky") is True
    context = build_avatar_world_secret_ai_context(other)
    assert context["secret_title"] == definition.title
    assert context["full_secret"] == definition.secret


def test_world_secret_overview_and_public_new_avatar_sync(dummy_avatar):
    world = _world_with_classic_map()
    avatar = dummy_avatar
    avatar.world = world
    world.avatar_manager.avatars[avatar.id] = avatar
    runtime = initialize_world_secret(world, "fake_sky")
    runtime.public_revealed = True
    runtime.public_revealed_by_avatar_id = avatar.id
    sync_avatar_public_world_secret_knowledge(world, avatar)

    overview = build_world_secret_overview(world)

    assert overview["active_secret"]["title"]
    assert overview["public_revealed"] is True
    assert overview["public_revealed_by"]["id"] == avatar.id
    assert overview["avatars"][0]["knows_full_secret"] is True


def test_save_load_preserves_world_secret(base_world, dummy_avatar, tmp_path):
    world = base_world
    avatar = dummy_avatar
    avatar.world = world
    avatar.weapon = None
    world.avatar_manager.avatars[avatar.id] = avatar
    initialize_world_secret(world, "fake_sky")
    knowledge = get_avatar_secret_knowledge(avatar, "fake_sky")
    knowledge.known_fragment_ids.add("fake_sky_1")
    knowledge.knows_full_secret = True
    world.world_secret.resolved_by_avatar_ids.add(avatar.id)
    world.world_secret.disclosure_decisions[avatar.id] = "keep_secret"

    save_path = tmp_path / "world_secret_save.json"
    ok, _ = save_game(world, Simulator(world), [], save_path)
    assert ok is True

    loaded_world, _, _ = load_game(save_path)
    loaded_avatar = loaded_world.avatar_manager.get_avatar(avatar.id)
    loaded_knowledge = get_avatar_secret_knowledge(loaded_avatar, "fake_sky")

    assert loaded_world.world_secret.selected_secret_id == "fake_sky"
    assert loaded_world.world_secret.disclosure_decisions[avatar.id] == "keep_secret"
    assert "fake_sky_1" in loaded_knowledge.known_fragment_ids
    assert loaded_knowledge.knows_full_secret is True


def _world_with_classic_map():
    from src.classes.core.world import World

    return World(
        map=load_cultivation_world_map("classic"),
        month_stamp=create_month_stamp(Year(1), Month.JANUARY),
    )


def _clone_avatar_for_world(source, world, avatar_id):
    from src.classes.core.avatar import Avatar

    avatar = Avatar(
        world=world,
        name=f"{source.name}二",
        id=avatar_id,
        birth_month_stamp=source.birth_month_stamp,
        age=source.age,
        gender=source.gender,
        cultivation_progress=source.cultivation_progress,
        pos_x=source.pos_x,
        pos_y=source.pos_y,
        root=source.root,
        personas=[],
        alignment=source.alignment,
    )
    avatar.tile = world.map.get_tile(avatar.pos_x, avatar.pos_y)
    avatar.weapon = source.weapon
    avatar.recalc_effects()
    return avatar
