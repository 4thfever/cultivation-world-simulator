import pytest
from unittest.mock import AsyncMock, patch

from src.classes.age import Age
from src.classes.core.avatar import Avatar, Gender
from src.classes.event import Event
from src.classes.goldfinger import goldfingers_by_id
from src.classes.root import Root
from src.classes.alignment import Alignment
from src.systems.cultivation import Realm
from src.systems.random_minor_event import try_trigger_random_minor_event
from src.systems.random_minor_event_loader import load_minor_event_types
from src.systems.random_minor_event_types import (
    MinorEventCategory,
    MinorEventParticipants,
    MinorEventRelationHint,
    MinorEventTone,
    MinorEventType,
)
from src.systems.time import Month, Year, create_month_stamp
from src.utils.id_generator import get_avatar_id


def _make_event_type(
    *,
    event_key: str,
    participants: MinorEventParticipants,
    tone: MinorEventTone = MinorEventTone.NEUTRAL,
    relation_hint: MinorEventRelationHint = MinorEventRelationHint.NONE,
    category: MinorEventCategory | None = None,
) -> MinorEventType:
    final_category = category
    if final_category is None:
        final_category = (
            MinorEventCategory.PAIR_SOCIAL
            if participants == MinorEventParticipants.PAIR
            else MinorEventCategory.SOLO_DAILY
        )
    return MinorEventType(
        event_key=event_key,
        category=final_category,
        participants=participants,
        tone=tone,
        relation_hint=relation_hint,
        weight=1.0,
        desc_id=f"{event_key}_desc",
    )


def _find_goldfinger_by_key(key: str):
    for goldfinger in goldfingers_by_id.values():
        if goldfinger.key == key:
            return goldfinger
    raise AssertionError(f"Goldfinger not found: {key}")


def _register_other_avatar(base_world, dummy_avatar: Avatar) -> Avatar:
    other_avatar = Avatar(
        world=base_world,
        name="Other",
        id=get_avatar_id(),
        birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
        age=Age(20, Realm.Qi_Refinement),
        gender=Gender.FEMALE,
        pos_x=dummy_avatar.pos_x,
        pos_y=dummy_avatar.pos_y,
        root=Root.WOOD,
        personas=[],
        alignment=Alignment.RIGHTEOUS,
    )
    other_avatar.personas = []
    other_avatar.recalc_effects()
    base_world.avatar_manager.register_avatar(other_avatar)
    return other_avatar


@pytest.mark.asyncio
async def test_try_trigger_random_minor_event_single_returns_single_event(dummy_avatar: Avatar):
    solo_type = _make_event_type(event_key="daily_practice", participants=MinorEventParticipants.SOLO)
    dummy_avatar.goldfinger = _find_goldfinger_by_key("OLD_GRANDPA")
    with (
        patch("src.systems.random_minor_event.RandomMinorEventService.should_trigger", return_value=True),
        patch("src.systems.random_minor_event_service.load_minor_event_types", return_value=[solo_type]),
        patch("src.systems.random_minor_event_service.random.choices", return_value=[solo_type]),
        patch("src.systems.random_minor_event_service.call_llm_with_task_name", new_callable=AsyncMock) as mock_call,
        patch("src.systems.random_minor_event_service.RelationDeltaService.resolve_event_text_delta", new_callable=AsyncMock) as mock_delta,
    ):
        mock_call.return_value = {"event_text": "TestDummy拂去袖上尘土，又默默运转了一周天。"}
        events = await try_trigger_random_minor_event(dummy_avatar, dummy_avatar.world)

    assert len(events) == 1
    event = events[0]
    assert event.content == "TestDummy拂去袖上尘土，又默默运转了一周天。"
    assert event.is_story is False
    assert event.is_major is False
    assert event.related_avatars == [dummy_avatar.id]
    infos = mock_call.await_args.kwargs["infos"]
    assert "随身老爷爷" in infos["world_info"]
    assert dummy_avatar.goldfinger.story_prompt in infos["world_info"]
    mock_delta.assert_not_called()


@pytest.mark.asyncio
async def test_try_trigger_random_minor_event_pair_applies_friendliness_delta(
    dummy_avatar: Avatar,
    base_world,
):
    pair_type = _make_event_type(
        event_key="small_mutual_help",
        participants=MinorEventParticipants.PAIR,
        tone=MinorEventTone.WARM,
        relation_hint=MinorEventRelationHint.MAYBE_UP,
    )
    dummy_avatar.goldfinger = _find_goldfinger_by_key("TRANSMIGRATOR")
    other_avatar = _register_other_avatar(base_world, dummy_avatar)
    other_avatar.goldfinger = _find_goldfinger_by_key("OLD_GRANDPA")
    before_a = dummy_avatar.get_friendliness(other_avatar)
    before_b = other_avatar.get_friendliness(dummy_avatar)

    with (
        patch("src.systems.random_minor_event.RandomMinorEventService.should_trigger", return_value=True),
        patch("src.systems.random_minor_event_service.load_minor_event_types", return_value=[pair_type]),
        patch("src.systems.random_minor_event_service.random.choices", return_value=[pair_type]),
        patch("src.systems.random_minor_event_service.random.choice", return_value=other_avatar),
        patch("src.systems.random_minor_event_service.call_llm_with_task_name", new_callable=AsyncMock) as mock_call,
        patch(
            "src.systems.random_minor_event_service.RelationDeltaService.resolve_event_text_delta",
            new_callable=AsyncMock,
        ) as mock_delta,
    ):
        mock_call.return_value = {"event_text": "TestDummy顺手替Other拨开路边乱枝，两人点头而过。"}
        mock_delta.return_value = (3, 1)
        events = await try_trigger_random_minor_event(dummy_avatar, base_world)

    assert len(events) == 1
    event = events[0]
    assert set(event.related_avatars) == {dummy_avatar.id, other_avatar.id}
    assert dummy_avatar.get_friendliness(other_avatar) == before_a + 3
    assert other_avatar.get_friendliness(dummy_avatar) == before_b + 1
    assert "[event_key=small_mutual_help]" in mock_delta.await_args.kwargs["event_text"]
    infos = mock_call.await_args.kwargs["infos"]
    assert "穿越者" in infos["world_info"]
    assert "随身老爷爷" in infos["world_info"]


@pytest.mark.asyncio
async def test_pair_event_without_target_falls_back_to_solo(dummy_avatar: Avatar):
    pair_type = _make_event_type(
        event_key="social_friction",
        participants=MinorEventParticipants.PAIR,
        tone=MinorEventTone.TENSE,
        relation_hint=MinorEventRelationHint.MAYBE_DOWN,
    )
    solo_type = _make_event_type(event_key="comic_incident", participants=MinorEventParticipants.SOLO)

    with (
        patch("src.systems.random_minor_event.RandomMinorEventService.should_trigger", return_value=True),
        patch("src.systems.random_minor_event_service.load_minor_event_types", return_value=[pair_type, solo_type]),
        patch("src.systems.random_minor_event_service.random.choices", side_effect=[[pair_type], [solo_type]]),
        patch("src.systems.random_minor_event_service.call_llm_with_task_name", new_callable=AsyncMock) as mock_call,
        patch("src.systems.random_minor_event_service.RelationDeltaService.resolve_event_text_delta", new_callable=AsyncMock) as mock_delta,
    ):
        mock_call.return_value = {"event_text": "TestDummy抬手掸落肩头枯叶，自己都觉得有些好笑。"}
        events = await try_trigger_random_minor_event(dummy_avatar, dummy_avatar.world)

    assert len(events) == 1
    assert events[0].related_avatars == [dummy_avatar.id]
    mock_delta.assert_not_called()


@pytest.mark.asyncio
async def test_try_trigger_random_minor_event_returns_empty_when_llm_fails(dummy_avatar: Avatar):
    solo_type = _make_event_type(event_key="sect_errand", participants=MinorEventParticipants.SOLO)
    with (
        patch("src.systems.random_minor_event.RandomMinorEventService.should_trigger", return_value=True),
        patch("src.systems.random_minor_event_service.load_minor_event_types", return_value=[solo_type]),
        patch("src.systems.random_minor_event_service.random.choices", return_value=[solo_type]),
        patch("src.systems.random_minor_event_service.call_llm_with_task_name", new_callable=AsyncMock) as mock_call,
    ):
        mock_call.side_effect = Exception("llm boom")
        events = await try_trigger_random_minor_event(dummy_avatar, dummy_avatar.world)

    assert events == []


def test_load_minor_event_types_parses_new_schema():
    with patch("src.systems.random_minor_event_loader.game_configs") as mock_configs:
        mock_configs.get.return_value = [
            {
                "event_key": "passing_interaction",
                "category": "pair_social",
                "participants": "pair",
                "tone": "neutral",
                "relation_hint": "mixed",
                "weight": "1.2",
                "desc_id": "路过时短暂发生的一次照面互动",
            }
        ]

        event_types = load_minor_event_types()

    assert len(event_types) == 1
    event_type = event_types[0]
    assert event_type.event_key == "passing_interaction"
    assert event_type.category == MinorEventCategory.PAIR_SOCIAL
    assert event_type.participants == MinorEventParticipants.PAIR
    assert event_type.tone == MinorEventTone.NEUTRAL
    assert event_type.relation_hint == MinorEventRelationHint.MIXED
    assert event_type.weight == 1.2


@pytest.mark.asyncio
async def test_phase_random_minor_events_flattens_event_lists(base_world, dummy_avatar: Avatar):
    base_world.avatar_manager.register_avatar(dummy_avatar)
    events_to_return = [
        Event(base_world.month_stamp, "甲的小事", related_avatars=[dummy_avatar.id]),
        Event(base_world.month_stamp, "乙的小事", related_avatars=[dummy_avatar.id]),
    ]
    with patch(
        "src.sim.simulator_engine.phases.world.try_trigger_random_minor_event",
        new_callable=AsyncMock,
        return_value=events_to_return,
    ):
        from src.sim.simulator_engine.phases.world import phase_random_minor_events

        events = await phase_random_minor_events(base_world, [dummy_avatar])

    assert [event.content for event in events] == ["甲的小事", "乙的小事"]
