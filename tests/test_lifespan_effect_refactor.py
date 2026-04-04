from unittest.mock import AsyncMock, patch

import pytest

from src.classes.action.breakthrough import Breakthrough
from src.classes.action.retreat import Retreat
from src.classes.language import language_manager
from src.i18n import t
from src.systems.cultivation import CultivationProgress, Realm


def test_breakthrough_success_increases_lifespan_via_realm_effect(dummy_avatar):
    dummy_avatar.age.age = 20
    dummy_avatar.age.innate_max_lifespan = 80
    dummy_avatar.cultivation_progress = CultivationProgress(level=30)
    dummy_avatar.recalc_effects()

    assert dummy_avatar.age.max_lifespan == 80
    assert dummy_avatar.effects.get("extra_max_lifespan", 0) == 0

    action = Breakthrough(dummy_avatar, dummy_avatar.world)
    with patch("random.random", return_value=0.0):
        action._execute()

    assert dummy_avatar.cultivation_progress.realm == Realm.Foundation_Establishment
    assert dummy_avatar.effects.get("extra_max_lifespan") == 50
    assert dummy_avatar.age.max_lifespan == 130

    breakdown = dict(dummy_avatar.get_effect_breakdown())
    assert breakdown[t("effect_source_cultivation_realm")]["extra_max_lifespan"] == 50


def test_breakthrough_failure_adds_negative_lifespan_effect(dummy_avatar):
    dummy_avatar.age.age = 76
    dummy_avatar.age.innate_max_lifespan = 80
    dummy_avatar.cultivation_progress = CultivationProgress(level=30)
    dummy_avatar.recalc_effects()

    action = Breakthrough(dummy_avatar, dummy_avatar.world)
    with patch("random.random", return_value=1.0):
        action._execute()

    assert dummy_avatar.is_dead is True
    assert len(dummy_avatar.persistent_effects) == 1
    assert dummy_avatar.persistent_effects[0]["source"] == "effect_source_breakthrough_failure"
    assert dummy_avatar.persistent_effects[0]["effects"]["extra_max_lifespan"] == -5
    assert dummy_avatar.age.max_lifespan == 75

    breakdown = dict(dummy_avatar.get_effect_breakdown())
    assert breakdown[t("effect_source_breakthrough_failure")]["extra_max_lifespan"] == -5


@pytest.mark.asyncio
async def test_retreat_failure_adds_negative_lifespan_effect(dummy_avatar):
    dummy_avatar.age.age = 79
    dummy_avatar.age.innate_max_lifespan = 80
    dummy_avatar.recalc_effects()

    action = Retreat(dummy_avatar, dummy_avatar.world)
    with patch("random.random", return_value=1.0), \
         patch("random.randint", side_effect=[12]), \
         patch("src.classes.story_teller.StoryTeller.tell_story", return_value="story"):
        await action.finish()

    assert dummy_avatar.is_dead is True
    assert len(dummy_avatar.persistent_effects) == 1
    assert dummy_avatar.persistent_effects[0]["source"] == "effect_source_retreat_failure"
    assert dummy_avatar.persistent_effects[0]["effects"]["extra_max_lifespan"] == -12
    assert dummy_avatar.age.max_lifespan == 68


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("locale", "expected_content", "unexpected_fragment"),
    [
        ("en-US", "TestDummy encountered nether prison tribulation, breakthrough succeeded", "阴狱"),
        ("zh-TW", "TestDummy 遭遇了陰獄劫難，突破成功", "阴狱"),
        ("vi-VN", "TestDummy gặp phải âm ngục, đột phá thành công", "阴狱"),
        ("ja-JP", "TestDummy は 陰獄 の劫に遭い、突破は 成功", "阴狱"),
    ],
)
async def test_breakthrough_story_event_localizes_tribulation_name_in_enabled_locales(
    dummy_avatar,
    locale,
    expected_content,
    unexpected_fragment,
):
    original_lang = str(language_manager)
    try:
        language_manager.set_language(locale)
        dummy_avatar.cultivation_progress = CultivationProgress(level=60)
        dummy_avatar.recalc_effects()

        action = Breakthrough(dummy_avatar, dummy_avatar.world)
        with patch("src.classes.action.breakthrough.TribulationSelector.choose_tribulation", return_value="阴狱"), \
             patch("src.classes.action.breakthrough.TribulationSelector.choose_related_avatar", return_value=None), \
             patch("src.classes.action.breakthrough.StoryEventService.maybe_create_story", new_callable=AsyncMock, return_value=None), \
             patch("random.random", return_value=0.0):
            action.start()
            action._execute()
            events = await action.finish()

        assert events
        assert events[0].content == expected_content
        assert unexpected_fragment not in events[0].content
    finally:
        language_manager.set_language(original_lang)
