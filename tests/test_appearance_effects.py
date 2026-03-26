import copy

from src.classes.appearance import get_appearance_by_level
from src.classes.effect.desc import format_effects_to_text
from src.classes.items.elixir import elixirs_by_id
from src.classes.persona import personas_by_id


def test_avatar_appearance_uses_base_plus_extra(dummy_avatar):
    dummy_avatar.base_appearance = get_appearance_by_level(6)
    dummy_avatar.add_persistent_effect("appearance_test", {"extra_appearance": 1})

    assert dummy_avatar.base_appearance.level == 6
    assert dummy_avatar.appearance.level == 7
    assert dummy_avatar.appearance.get_info().endswith("(7)")


def test_avatar_appearance_is_clamped(dummy_avatar):
    dummy_avatar.base_appearance = get_appearance_by_level(10)
    dummy_avatar.add_persistent_effect("too_pretty", {"extra_appearance": 5})
    assert dummy_avatar.appearance.level == 10

    dummy_avatar.persistent_effects = [{"source": "too_ugly", "effects": {"extra_appearance": -99}}]
    dummy_avatar.recalc_effects()
    assert dummy_avatar.appearance.level == 1


def test_appearance_effect_survives_save_and_load(base_world, dummy_avatar):
    dummy_avatar.base_appearance = get_appearance_by_level(5)
    dummy_avatar.add_persistent_effect("appearance_test", {"extra_appearance": 1})

    saved = dummy_avatar.to_save_dict()
    loaded = dummy_avatar.__class__.from_save_dict(copy.deepcopy(saved), base_world)

    assert loaded.base_appearance.level == 5
    assert loaded.appearance.level == 6
    assert loaded.effects.get("extra_appearance") == 1


def test_new_personas_loaded():
    love_beauty = personas_by_id[1012]
    appearance_obsessed = personas_by_id[1013]

    assert love_beauty.name == "爱美"
    assert love_beauty.effects == {}
    assert appearance_obsessed.name == "悦己"
    assert appearance_obsessed.effects["extra_appearance"] == 1


def test_new_beauty_elixirs_loaded():
    qi_elixir = elixirs_by_id[3017]
    nascent_elixir = elixirs_by_id[3020]

    assert qi_elixir.name == "练气驻颜丹"
    assert qi_elixir.effects["extra_appearance"] == 1
    assert nascent_elixir.name == "元婴驻颜丹"
    assert nascent_elixir.effects["extra_appearance"] == 1


def test_consume_beauty_elixir_applies_extra_appearance(dummy_avatar):
    dummy_avatar.base_appearance = get_appearance_by_level(5)

    success = dummy_avatar.consume_elixir(elixirs_by_id[3017])

    assert success
    assert dummy_avatar.effects.get("extra_appearance") == 1
    assert dummy_avatar.appearance.level == 6


def test_format_effects_shows_appearance_in_zh_cn():
    text = format_effects_to_text({"extra_appearance": 1})
    assert text == "颜值 +1"
