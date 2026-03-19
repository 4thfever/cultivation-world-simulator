from unittest.mock import patch

import pytest

from src.classes.action.breakthrough import Breakthrough
from src.classes.action.retreat import Retreat
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
