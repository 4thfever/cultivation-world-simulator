from src.classes.effect.desc import format_effects_to_text


def test_extra_max_lifespan_zero_uses_positive_sign():
    text = format_effects_to_text({"extra_max_lifespan": 0})
    assert "+0" in text
