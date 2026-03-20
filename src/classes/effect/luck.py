from __future__ import annotations

from typing import Any

from .consts import (
    EXTRA_BREAKTHROUGH_SUCCESS_RATE,
    EXTRA_EPIPHANY_PROBABILITY,
    EXTRA_FORTUNE_PROBABILITY,
    EXTRA_HIDDEN_DOMAIN_DANGER_PROB,
    EXTRA_HIDDEN_DOMAIN_DROP_PROB,
    EXTRA_LUCK,
    EXTRA_MISFORTUNE_PROBABILITY,
)


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def compute_luck_value(base_luck: float, raw_effects: dict[str, Any]) -> float:
    extra_luck = raw_effects.get(EXTRA_LUCK, 0)
    try:
        return round(float(base_luck) + float(extra_luck), 4)
    except Exception:
        return float(base_luck)


def build_luck_derived_effects(luck: float) -> dict[str, float]:
    if luck == 0:
        return {}

    return {
        EXTRA_FORTUNE_PROBABILITY: _clamp(luck * 0.001, -0.01, 0.03),
        EXTRA_MISFORTUNE_PROBABILITY: _clamp(-luck * 0.0005, -0.01, 0.01),
        EXTRA_HIDDEN_DOMAIN_DROP_PROB: _clamp(luck * 0.01, -0.10, 0.20),
        EXTRA_HIDDEN_DOMAIN_DANGER_PROB: _clamp(-luck * 0.005, -0.10, 0.10),
        EXTRA_EPIPHANY_PROBABILITY: _clamp(luck * 0.0025, -0.02, 0.05),
        EXTRA_BREAKTHROUGH_SUCCESS_RATE: _clamp(luck * 0.0025, 0.0, 0.05),
    }
