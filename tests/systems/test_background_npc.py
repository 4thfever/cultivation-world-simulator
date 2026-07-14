from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from src.classes.action import InstantAction
from src.classes.action_runtime import ActionInstance
from src.classes.alignment import Alignment
from src.classes.core.avatar import Avatar
from src.classes.environment.region import CityRegion
from src.systems.background_npc import BackgroundNpcService
from src.systems.background_npc.loader import (
    load_background_npc_event_types,
    load_background_npc_profiles,
    load_background_npc_region_bindings,
)
from src.systems.background_npc.models import BACKGROUND_NPC_EVENT_TYPE
from src.systems.cultivation import CultivationProgress
from src.utils.df import reload_game_configs


def _profile_rows():
    return [
        {
            "id": "1",
            "profile_key": "herb_vendor",
            "role_label_id": "BACKGROUND_NPC_ROLE_HERB_VENDOR",
            "category": "city_market",
            "default_scene_tags": "city_market;medicine",
        }
    ]


def _event_rows():
    return [
        {
            "id": "1",
            "event_key": "market_argument",
            "profile_key": "herb_vendor",
            "trigger_kind": "region_tick",
            "region_types": "city",
            "required_tags": "medicine",
            "excluded_tags": "",
            "map_ids": "",
            "avatar_filters": "",
            "action_keys": "",
            "weight": "1.0",
            "cooldown_months": "0",
            "max_per_month": "1",
            "text_id": "BACKGROUND_NPC_EVENT_HERB_VENDOR_MARKET_ARGUMENT",
        },
        {
            "id": "2",
            "event_key": "yao_market",
            "profile_key": "herb_vendor",
            "trigger_kind": "avatar_witness",
            "region_types": "city",
            "required_tags": "city_market",
            "excluded_tags": "",
            "map_ids": "",
            "avatar_filters": "race=yao",
            "action_keys": "",
            "weight": "1.0",
            "cooldown_months": "0",
            "max_per_month": "1",
            "text_id": "BACKGROUND_NPC_EVENT_MARKET_REACTS_TO_YAO",
        },
        {
            "id": "3",
            "event_key": "buy_echo",
            "profile_key": "herb_vendor",
            "trigger_kind": "action_echo",
            "region_types": "city",
            "required_tags": "medicine",
            "excluded_tags": "",
            "map_ids": "",
            "avatar_filters": "",
            "action_keys": "Buy",
            "weight": "1.0",
            "cooldown_months": "0",
            "max_per_month": "1",
            "text_id": "BACKGROUND_NPC_EVENT_HERB_VENDOR_AVATAR_BUY_ECHO",
        },
        {
            "id": "4",
            "event_key": "generic_medicine_inquiry",
            "profile_key": "herb_vendor",
            "trigger_kind": "avatar_witness",
            "region_types": "city",
            "required_tags": "medicine",
            "excluded_tags": "",
            "map_ids": "",
            "avatar_filters": "",
            "action_keys": "",
            "weight": "1.0",
            "cooldown_months": "0",
            "max_per_month": "1",
            "text_id": "BACKGROUND_NPC_EVENT_MEDICINE_ASSISTANT_AVATAR_INQUIRY",
        },
    ]


def _binding_rows():
    return [
        {
            "id": "1",
            "map_id": "classic",
            "region_id": "301",
            "scene_tags": "city_market;medicine",
        }
    ]


def _patch_configs(*, events=None):
    data = {
        "background_npc_profile": _profile_rows(),
        "background_npc_event": events or _event_rows(),
        "background_npc_region_binding": _binding_rows(),
    }
    return patch("src.systems.background_npc.loader.game_configs", data)


def _config(
    *,
    region_tick_prob=1.0,
    avatar_witness_prob=1.0,
    action_echo_prob=1.0,
    max_region_tick_per_month=1,
    max_avatar_witness_per_month=2,
    max_action_echo_per_month=2,
):
    return SimpleNamespace(
        enabled=True,
        region_tick_prob=region_tick_prob,
        avatar_witness_prob=avatar_witness_prob,
        action_echo_prob=action_echo_prob,
        max_region_tick_per_month=max_region_tick_per_month,
        max_avatar_witness_per_month=max_avatar_witness_per_month,
        max_action_echo_per_month=max_action_echo_per_month,
    )


def _put_avatar_in_city(base_world, avatar: Avatar) -> CityRegion:
    region = CityRegion(id=301, name="青云城", desc="城", sell_item_ids=[])
    tile = SimpleNamespace(region=region)
    avatar.tile = tile
    avatar.pos_x = 0
    avatar.pos_y = 0
    base_world.map = SimpleNamespace(map_id="classic", regions={301: region})
    return region


def test_background_npc_loader_parses_profile_event_and_binding():
    with _patch_configs():
        profiles = load_background_npc_profiles()
        events = load_background_npc_event_types()
        bindings = load_background_npc_region_bindings()

    assert profiles[0].profile_key == "herb_vendor"
    assert profiles[0].default_scene_tags == ("city_market", "medicine")
    assert [event.event_key for event in events] == [
        "market_argument",
        "yao_market",
        "buy_echo",
        "generic_medicine_inquiry",
    ]
    assert events[1].avatar_filters == {"race": "yao"}
    assert events[2].action_keys == ("Buy",)
    assert bindings[0].scene_tags == ("city_market", "medicine")


def test_real_background_npc_csv_columns_are_aligned():
    reload_game_configs()
    events = {event.event_key: event for event in load_background_npc_event_types()}

    assert events["market_reacts_to_yao"].avatar_filters == {"race": "yao"}
    assert events["store_reacts_to_high_realm"].avatar_filters == {"realm_min": "FOUNDATION_ESTABLISHMENT"}
    assert events["yamen_reacts_to_official"].avatar_filters == {"official": "any"}
    assert events["sect_servant_reacts_to_disciple"].avatar_filters == {"sect": "any"}
    assert events["patrol_fears_evil_avatar"].avatar_filters == {"alignment": "EVIL"}
    assert events["herb_vendor_avatar_buy_echo"].action_keys == ("Buy",)
    assert events["ferryman_move_region_echo"].action_keys == ("MoveToRegion",)


def test_region_tick_creates_world_only_small_event(base_world, dummy_avatar):
    BackgroundNpcService.reset_runtime_state()
    _put_avatar_in_city(base_world, dummy_avatar)

    with (
        _patch_configs(),
        patch("src.systems.background_npc.service.CONFIG") as mock_config,
        patch("src.systems.background_npc.service.random.random", return_value=0.0),
        patch("src.systems.background_npc.service.random.choices", side_effect=lambda seq, weights, k: [seq[0]]),
    ):
        mock_config.world.background_npc = _config(avatar_witness_prob=0.0)
        events = BackgroundNpcService.create_monthly_events(base_world, [dummy_avatar])

    assert len(events) == 1
    event = events[0]
    assert event.related_avatars is None
    assert event.is_major is False
    assert event.is_story is False
    assert event.event_type == BACKGROUND_NPC_EVENT_TYPE
    assert "青云城" in event.content
    assert "药材商" in event.content
    assert event.render_params["region_name"] == "青云城"
    assert event.render_params["trigger_kind"] == "region_tick"


def test_avatar_witness_filters_by_yao_race(base_world, dummy_avatar):
    BackgroundNpcService.reset_runtime_state()
    _put_avatar_in_city(base_world, dummy_avatar)

    with (
        _patch_configs(),
        patch("src.systems.background_npc.service.CONFIG") as mock_config,
        patch("src.systems.background_npc.service.random.random", return_value=0.0),
        patch("src.systems.background_npc.service.random.choices", side_effect=lambda seq, weights, k: [seq[0]]),
    ):
        mock_config.world.background_npc = _config(region_tick_prob=0.0, max_avatar_witness_per_month=1)
        human_events = BackgroundNpcService.create_monthly_events(base_world, [dummy_avatar])
        dummy_avatar.race = "fox"
        yao_events = BackgroundNpcService.create_monthly_events(base_world, [dummy_avatar])

    assert len(human_events) == 1
    assert "青云城" in human_events[0].content
    assert dummy_avatar.id in human_events[0].related_avatars
    assert len(yao_events) == 1
    assert yao_events[0].related_avatars == [dummy_avatar.id]
    assert dummy_avatar.name in yao_events[0].content
    assert yao_events[0].render_params["region_name"] == "青云城"


def test_action_echo_matches_action_key(base_world, dummy_avatar):
    BackgroundNpcService.reset_runtime_state()
    _put_avatar_in_city(base_world, dummy_avatar)

    with (
        _patch_configs(),
        patch("src.systems.background_npc.service.CONFIG") as mock_config,
        patch("src.systems.background_npc.service.random.random", return_value=0.0),
        patch("src.systems.background_npc.service.random.choices", side_effect=lambda seq, weights, k: [seq[0]]),
    ):
        mock_config.world.background_npc = _config()
        no_match = BackgroundNpcService.create_action_echo_events(base_world, dummy_avatar, "Sell")
        matched = BackgroundNpcService.create_action_echo_events(base_world, dummy_avatar, "Buy")

    assert no_match == []
    assert len(matched) == 1
    assert matched[0].related_avatars == [dummy_avatar.id]
    assert matched[0].event_type == BACKGROUND_NPC_EVENT_TYPE
    assert dummy_avatar.name in matched[0].content


def test_avatar_filters_support_alignment_and_realm(base_world, dummy_avatar):
    BackgroundNpcService.reset_runtime_state()
    _put_avatar_in_city(base_world, dummy_avatar)
    events = [
        {
            **_event_rows()[1],
            "event_key": "evil_high_realm",
            "avatar_filters": "alignment=EVIL;realm_min=FOUNDATION_ESTABLISHMENT",
        }
    ]

    with (
        _patch_configs(events=events),
        patch("src.systems.background_npc.service.CONFIG") as mock_config,
        patch("src.systems.background_npc.service.random.random", return_value=0.0),
        patch("src.systems.background_npc.service.random.choices", side_effect=lambda seq, weights, k: [seq[0]]),
    ):
        mock_config.world.background_npc = _config(region_tick_prob=0.0)
        dummy_avatar.alignment = Alignment.EVIL
        dummy_avatar.cultivation_progress = CultivationProgress(31)
        matched = BackgroundNpcService.create_monthly_events(base_world, [dummy_avatar])
        dummy_avatar.cultivation_progress = CultivationProgress(1)
        too_low = BackgroundNpcService.create_monthly_events(base_world, [dummy_avatar])

    assert len(matched) == 1
    assert too_low == []


def test_phase_background_npc_events_delegates(base_world, dummy_avatar):
    from src.sim.simulator_engine.phases.world import phase_background_npc_events

    event = SimpleNamespace(content="凡人场景")
    with patch(
        "src.sim.simulator_engine.phases.world.try_trigger_background_npc_events",
        return_value=[event],
    ) as mock_trigger:
        events = phase_background_npc_events(base_world, [dummy_avatar])

    assert events == [event]
    mock_trigger.assert_called_once_with(base_world, [dummy_avatar])


class _CompletedAction(InstantAction):
    ACTION_NAME_ID = "completed_action_name"
    DESC_ID = "completed_action_desc"
    REQUIREMENTS_ID = "completed_action_requirements"
    EMOJI = "✅"
    PARAMS = {}

    def _execute(self):
        return []


@pytest.mark.asyncio
async def test_avatar_tick_action_appends_background_npc_action_echo(dummy_avatar):
    echo_event = SimpleNamespace(content="动作回声")
    dummy_avatar.current_action = ActionInstance(action=_CompletedAction(dummy_avatar, dummy_avatar.world), params={})
    with patch(
        "src.systems.background_npc.try_trigger_background_npc_action_echo",
        return_value=[echo_event],
    ) as mock_echo:
        events = await dummy_avatar.tick_action()

    assert echo_event in events
    mock_echo.assert_called_once_with(dummy_avatar.world, dummy_avatar, "_CompletedAction")
