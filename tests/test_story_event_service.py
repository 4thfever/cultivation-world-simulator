import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.classes.story_event_service import StoryEventKind, StoryEventService
from src.classes.goldfinger import goldfingers_by_id


def _find_goldfinger_by_key(key: str):
    for goldfinger in goldfingers_by_id.values():
        if goldfinger.key == key:
            return goldfinger
    raise AssertionError(f"Goldfinger not found: {key}")


@pytest.mark.asyncio
async def test_gathering_story_always_triggers(dummy_avatar):
    with patch("src.classes.story_event_service.StoryTeller.tell_gathering_story", new_callable=AsyncMock) as mock_tell:
        mock_tell.return_value = "Gathering story"

        event = await StoryEventService.maybe_create_gathering_story(
            month_stamp=dummy_avatar.world.month_stamp,
            gathering_info="Gathering info",
            events_text="Event text",
            details_text="Detail text",
            related_avatars=[dummy_avatar],
        )

    assert event is not None
    assert event.is_story is True
    assert event.content == "Gathering story"


@pytest.mark.asyncio
async def test_story_not_created_when_probability_misses(dummy_avatar):
    with patch("src.classes.story_event_service.StoryEventService.should_trigger", return_value=False), \
         patch("src.classes.story_event_service.StoryTeller.tell_story", new_callable=AsyncMock) as mock_tell:
        event = await StoryEventService.maybe_create_story(
            kind=StoryEventKind.DAILY_SOCIAL,
            month_stamp=dummy_avatar.world.month_stamp,
            start_text="Start",
            result_text="Result",
            actors=[dummy_avatar],
            related_avatar_ids=[dummy_avatar.id],
        )

    assert event is None
    mock_tell.assert_not_called()


@pytest.mark.asyncio
async def test_story_created_when_probability_hits(dummy_avatar):
    with patch("src.classes.story_event_service.StoryEventService.should_trigger", return_value=True), \
         patch("src.classes.story_event_service.StoryTeller.tell_story", new_callable=AsyncMock) as mock_tell:
        mock_tell.return_value = "Story body"

        event = await StoryEventService.maybe_create_story(
            kind=StoryEventKind.CRAFTING,
            month_stamp=dummy_avatar.world.month_stamp,
            start_text="Start",
            result_text="Result",
            actors=[dummy_avatar],
            related_avatar_ids=[dummy_avatar.id],
        )

    assert event is not None
    assert event.is_story is True
    assert event.content == "Story body"
    mock_tell.assert_awaited_once()


@pytest.mark.asyncio
async def test_story_service_merges_goldfinger_prompt(dummy_avatar):
    dummy_avatar.goldfinger = _find_goldfinger_by_key("REINCARNATOR")

    with patch("src.classes.story_event_service.StoryEventService.should_trigger", return_value=True), \
         patch("src.classes.story_event_service.StoryTeller.tell_story", new_callable=AsyncMock) as mock_tell:
        mock_tell.return_value = "Story body"

        await StoryEventService.maybe_create_story(
            kind=StoryEventKind.DAILY_SOCIAL,
            month_stamp=dummy_avatar.world.month_stamp,
            start_text="Start",
            result_text="Result",
            actors=[dummy_avatar],
            related_avatar_ids=[dummy_avatar.id],
            prompt="原始提示",
        )

    prompt = mock_tell.await_args.kwargs["prompt"]
    assert "原始提示" in prompt
    assert "外挂相关重点" in prompt
    assert "重生者" in prompt
    assert dummy_avatar.goldfinger.story_prompt in prompt


@pytest.mark.asyncio
async def test_gathering_story_merges_goldfinger_prompt(dummy_avatar):
    dummy_avatar.goldfinger = _find_goldfinger_by_key("OLD_GRANDPA")

    with patch("src.classes.story_event_service.StoryTeller.tell_gathering_story", new_callable=AsyncMock) as mock_tell:
        mock_tell.return_value = "Gathering story"

        await StoryEventService.maybe_create_gathering_story(
            month_stamp=dummy_avatar.world.month_stamp,
            gathering_info="Gathering info",
            events_text="Event text",
            details_text="Detail text",
            related_avatars=[dummy_avatar],
            prompt="聚会提示",
        )

    prompt = mock_tell.await_args.kwargs["prompt"]
    assert "聚会提示" in prompt
    assert "外挂相关重点" in prompt
    assert "随身老爷爷" in prompt
    assert dummy_avatar.goldfinger.story_prompt in prompt
