from __future__ import annotations

from typing import Any

from src.classes.effect.process import load_effect_from_str, _merge_effects


def load_sect_effect_from_str(value: object) -> dict[str, Any]:
    """
    Parse sect effect config from CSV text.
    """
    parsed = load_effect_from_str(value)
    if isinstance(parsed, dict):
        return parsed
    return {}


def merge_sect_effects(base: dict[str, Any], addition: dict[str, Any]) -> dict[str, Any]:
    """
    Merge sect effects with the same strategy used by avatar effects.
    """
    return _merge_effects(base or {}, addition or {})
