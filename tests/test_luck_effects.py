from __future__ import annotations

import pytest

from src.classes.persona import personas_by_id


def _find_persona_by_key(key: str):
    for persona in personas_by_id.values():
        if persona.key == key:
            return persona
    raise AssertionError(f"Persona not found: {key}")


def test_default_avatar_has_zero_luck_and_no_derived_luck_effects(dummy_avatar):
    assert dummy_avatar.luck == 0
    assert dummy_avatar.effects.get("extra_luck", 0) == 0
    assert dummy_avatar.effects.get("extra_fortune_probability", 0) == 0
    assert dummy_avatar.effects.get("extra_misfortune_probability", 0) == 0


def test_child_of_fortune_is_pure_luck_source(dummy_avatar):
    dummy_avatar.personas = [_find_persona_by_key("CHILD_OF_FORTUNE")]

    assert dummy_avatar.luck == 20
    assert dummy_avatar.effects["extra_luck"] == 20
    assert dummy_avatar.effects["extra_fortune_probability"] == pytest.approx(0.02)
    assert dummy_avatar.effects["extra_misfortune_probability"] == pytest.approx(-0.01)
    assert dummy_avatar.effects["extra_hidden_domain_drop_prob"] == pytest.approx(0.2)
    assert dummy_avatar.effects["extra_hidden_domain_danger_prob"] == pytest.approx(-0.1)
    assert dummy_avatar.effects["extra_epiphany_probability"] == pytest.approx(0.05)
    assert dummy_avatar.effects["extra_breakthrough_success_rate"] == pytest.approx(0.05)
    assert dummy_avatar.effects.get("extra_battle_strength_points", 0) == 0


def test_blessed_with_good_fortune_has_moderate_luck(dummy_avatar):
    dummy_avatar.personas = [_find_persona_by_key("BLESSED_WITH_GOOD_FORTUNE")]

    assert dummy_avatar.luck == 8
    assert dummy_avatar.effects["extra_luck"] == 8
    assert dummy_avatar.effects["extra_fortune_probability"] == pytest.approx(0.008)
    assert dummy_avatar.effects["extra_misfortune_probability"] == pytest.approx(-0.004)
    assert dummy_avatar.effects["extra_epiphany_probability"] == pytest.approx(0.02)
    assert dummy_avatar.effects["extra_breakthrough_success_rate"] == pytest.approx(0.02)


def test_effect_breakdown_contains_luck_source_and_luck_derived_effects(dummy_avatar):
    dummy_avatar.personas = [_find_persona_by_key("CHILD_OF_FORTUNE")]

    breakdown = dummy_avatar.get_effect_breakdown()

    assert any("气运之子" in source and effects.get("extra_luck") == 20 for source, effects in breakdown)
    assert any(
        effects.get("extra_fortune_probability") == pytest.approx(0.02)
        and effects.get("extra_breakthrough_success_rate") == pytest.approx(0.05)
        for source, effects in breakdown
        if source in {"气运", "Luck"}
    )


def test_avatar_structured_info_exposes_luck_and_current_effects(dummy_avatar):
    dummy_avatar.personas = [_find_persona_by_key("BLESSED_WITH_GOOD_FORTUNE")]

    info = dummy_avatar.get_structured_info()

    assert info["luck"] == 8
    assert "current_effects" in info
    assert isinstance(info["current_effects"], str)
