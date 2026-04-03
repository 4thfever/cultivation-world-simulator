from __future__ import annotations

from dataclasses import dataclass

from .consts import (
    ALL_EFFECTS,
    DAMAGE_REDUCTION,
    EXTRA_APPEARANCE,
    EXTRA_ASSASSINATE_SUCCESS_RATE,
    EXTRA_BATTLE_STRENGTH_POINTS,
    EXTRA_CAST_SUCCESS_RATE,
    EXTRA_CATCH_SUCCESS_RATE,
    EXTRA_DUAL_CULTIVATION_EXP,
    EXTRA_EPIPHANY_PROBABILITY,
    EXTRA_ESCAPE_SUCCESS_RATE,
    EXTRA_FORTUNE_PROBABILITY,
    EXTRA_HARVEST_MATERIALS,
    EXTRA_HIDDEN_DOMAIN_DANGER_PROB,
    EXTRA_HIDDEN_DOMAIN_DROP_PROB,
    EXTRA_HP_RECOVERY_RATE,
    EXTRA_HUNT_MATERIALS,
    EXTRA_ITEM_SELL_PRICE_MULTIPLIER,
    EXTRA_LUCK,
    EXTRA_MAX_HP,
    EXTRA_MAX_LIFESPAN,
    EXTRA_MINE_MATERIALS,
    EXTRA_MISFORTUNE_PROBABILITY,
    EXTRA_MOVE_STEP,
    EXTRA_OBSERVATION_RADIUS,
    EXTRA_PLANT_INCOME,
    EXTRA_PLUNDER_MULTIPLIER,
    EXTRA_REFINE_SUCCESS_RATE,
    EXTRA_RESPIRE_EXP,
    EXTRA_RESPIRE_EXP_MULTIPLIER,
    EXTRA_RETREAT_SUCCESS_RATE,
    EXTRA_SECT_MISSION_SUCCESS_RATE,
    EXTRA_WEAPON_PROFICIENCY_GAIN,
    EXTRA_WEAPON_UPGRADE_CHANCE,
    LEGAL_ACTIONS,
    REALM_SUPPRESSION_BONUS,
    RESPIRE_DURATION_REDUCTION,
    SHOP_BUY_PRICE_REDUCTION,
    TEMPER_DURATION_REDUCTION,
    EXTRA_BREAKTHROUGH_SUCCESS_RATE,
)


@dataclass(frozen=True)
class EffectReferenceLevel:
    key: str
    value: str


@dataclass(frozen=True)
class EffectPromptMeta:
    value_type: str
    example: int | float | bool
    references: tuple[EffectReferenceLevel, ...] = ()
    constraints: tuple[str, ...] = ()


def _refs(*items: tuple[str, str]) -> tuple[EffectReferenceLevel, ...]:
    return tuple(EffectReferenceLevel(key=key, value=value) for key, value in items)


EFFECT_PROMPT_META: dict[str, EffectPromptMeta] = {
    EXTRA_BATTLE_STRENGTH_POINTS: EffectPromptMeta(
        value_type="int",
        example=3,
        references=_refs(("small", "1 to 2"), ("medium", "3 to 5"), ("large", "8+")),
    ),
    EXTRA_MAX_HP: EffectPromptMeta(
        value_type="int",
        example=30,
        references=_refs(("small", "10 to 30"), ("medium", "50 to 100"), ("large", "150+")),
    ),
    EXTRA_OBSERVATION_RADIUS: EffectPromptMeta(
        value_type="int",
        example=1,
        references=_refs(("small", "1"), ("medium", "2"), ("large", "3")),
    ),
    EXTRA_APPEARANCE: EffectPromptMeta(
        value_type="int",
        example=1,
        references=_refs(("small", "1"), ("large", "2")),
    ),
    EXTRA_RESPIRE_EXP: EffectPromptMeta(
        value_type="int",
        example=20,
        references=_refs(("small", "5 to 10"), ("medium", "20 to 50"), ("large", "100+")),
    ),
    EXTRA_RESPIRE_EXP_MULTIPLIER: EffectPromptMeta(
        value_type="float",
        example=0.2,
        references=_refs(("small", "0.1"), ("medium", "0.5"), ("large", "1.0")),
    ),
    RESPIRE_DURATION_REDUCTION: EffectPromptMeta(
        value_type="float",
        example=0.1,
        references=_refs(("small", "0.05 to 0.1"), ("medium", "0.15"), ("cap", "0.3")),
    ),
    TEMPER_DURATION_REDUCTION: EffectPromptMeta(
        value_type="float",
        example=0.1,
        references=_refs(("small", "0.05 to 0.1"), ("medium", "0.15"), ("cap", "0.3")),
    ),
    EXTRA_BREAKTHROUGH_SUCCESS_RATE: EffectPromptMeta(
        value_type="float",
        example=0.1,
        references=_refs(("small", "0.05"), ("medium", "0.1"), ("large", "0.3")),
    ),
    EXTRA_RETREAT_SUCCESS_RATE: EffectPromptMeta(
        value_type="float",
        example=0.1,
        references=_refs(("small", "0.05"), ("medium", "0.1"), ("large", "0.2")),
    ),
    EXTRA_DUAL_CULTIVATION_EXP: EffectPromptMeta(
        value_type="int",
        example=50,
        references=_refs(("small", "10 to 30"), ("medium", "50 to 100"), ("large", "150+")),
    ),
    EXTRA_HARVEST_MATERIALS: EffectPromptMeta(
        value_type="int",
        example=1,
        references=_refs(("small", "1"), ("medium", "2"), ("large", "3")),
    ),
    EXTRA_HUNT_MATERIALS: EffectPromptMeta(
        value_type="int",
        example=1,
        references=_refs(("small", "1"), ("medium", "2"), ("large", "3")),
    ),
    EXTRA_MINE_MATERIALS: EffectPromptMeta(value_type="int", example=1),
    EXTRA_PLANT_INCOME: EffectPromptMeta(value_type="int", example=20),
    EXTRA_MOVE_STEP: EffectPromptMeta(
        value_type="int",
        example=1,
        references=_refs(("medium", "1"), ("large", "2")),
    ),
    EXTRA_CATCH_SUCCESS_RATE: EffectPromptMeta(
        value_type="float",
        example=0.1,
        references=_refs(("small", "0.05 to 0.1"), ("medium", "0.2"), ("large", "0.3")),
    ),
    EXTRA_ESCAPE_SUCCESS_RATE: EffectPromptMeta(
        value_type="float",
        example=0.1,
        references=_refs(("small", "0.1"), ("medium", "0.2"), ("large", "0.3 to 0.5")),
    ),
    EXTRA_ASSASSINATE_SUCCESS_RATE: EffectPromptMeta(
        value_type="float",
        example=0.1,
        references=_refs(("small", "0.05"), ("medium", "0.1"), ("large", "0.15")),
    ),
    EXTRA_LUCK: EffectPromptMeta(
        value_type="int",
        example=2,
        references=_refs(
            ("ordinary", "0"),
            ("fortunate", "5 to 10"),
            ("protagonist_tier", "15 to 25"),
            ("unlucky", "-5 to -10"),
        ),
    ),
    EXTRA_FORTUNE_PROBABILITY: EffectPromptMeta(
        value_type="float",
        example=0.1,
        references=_refs(
            ("base_chance", "<0.01"),
            ("small", "0.001"),
            ("medium", "0.002 to 0.005"),
            ("very_high", "0.01"),
        ),
    ),
    EXTRA_MISFORTUNE_PROBABILITY: EffectPromptMeta(
        value_type="float",
        example=-0.1,
        references=_refs(
            ("base_chance", "<0.01"),
            ("small", "0.001"),
            ("medium", "0.002 to 0.005"),
            ("very_high", "0.01"),
        ),
    ),
    EXTRA_CAST_SUCCESS_RATE: EffectPromptMeta(
        value_type="float",
        example=0.1,
        references=_refs(("small", "0.05"), ("medium", "0.1"), ("large", "0.2+")),
    ),
    EXTRA_REFINE_SUCCESS_RATE: EffectPromptMeta(
        value_type="float",
        example=0.1,
        references=_refs(("small", "0.05"), ("medium", "0.1"), ("large", "0.2+")),
    ),
    EXTRA_SECT_MISSION_SUCCESS_RATE: EffectPromptMeta(
        value_type="float",
        example=0.1,
        references=_refs(("small", "0.05"), ("medium", "0.1"), ("large", "0.2+")),
    ),
    EXTRA_WEAPON_PROFICIENCY_GAIN: EffectPromptMeta(
        value_type="float",
        example=0.2,
        references=_refs(("small", "0.1 to 0.2"), ("medium", "0.5"), ("large", "1.0")),
    ),
    EXTRA_WEAPON_UPGRADE_CHANCE: EffectPromptMeta(
        value_type="float",
        example=0.1,
        references=_refs(("base_chance", "0.05"), ("small", "0.05"), ("medium", "0.1"), ("large", "0.15")),
    ),
    EXTRA_MAX_LIFESPAN: EffectPromptMeta(
        value_type="int",
        example=10,
        references=_refs(("small", "5 to 10"), ("medium", "20 to 50"), ("large", "100+")),
    ),
    EXTRA_HP_RECOVERY_RATE: EffectPromptMeta(
        value_type="float",
        example=0.2,
        references=_refs(("small", "0.1 to 0.2"), ("medium", "0.5"), ("large", "1.0")),
    ),
    DAMAGE_REDUCTION: EffectPromptMeta(
        value_type="float",
        example=0.1,
        references=_refs(("small", "0.05"), ("medium", "0.1"), ("tanky", "0.2 to 0.3")),
    ),
    REALM_SUPPRESSION_BONUS: EffectPromptMeta(
        value_type="float",
        example=0.05,
        references=_refs(("base_value", "0.0"), ("small", "0.05"), ("medium", "0.1"), ("large", "0.15")),
    ),
    EXTRA_ITEM_SELL_PRICE_MULTIPLIER: EffectPromptMeta(
        value_type="float",
        example=0.2,
        references=_refs(("small", "0.1"), ("medium", "0.2 to 0.3"), ("profit_focused", "0.5")),
    ),
    SHOP_BUY_PRICE_REDUCTION: EffectPromptMeta(
        value_type="float",
        example=0.1,
        references=_refs(("small", "0.1"), ("medium", "0.5")),
        constraints=("final_multiplier_floor_1_0",),
    ),
    EXTRA_PLUNDER_MULTIPLIER: EffectPromptMeta(
        value_type="float",
        example=0.5,
        references=_refs(("small", "0.5"), ("medium", "1.0"), ("large", "2")),
    ),
    EXTRA_HIDDEN_DOMAIN_DROP_PROB: EffectPromptMeta(
        value_type="float",
        example=0.1,
        references=_refs(("small", "0.05"), ("medium", "0.1"), ("large", "0.2")),
    ),
    EXTRA_HIDDEN_DOMAIN_DANGER_PROB: EffectPromptMeta(
        value_type="float",
        example=-0.1,
        references=_refs(("safer", "-0.1"), ("riskier", "0.1")),
    ),
    EXTRA_EPIPHANY_PROBABILITY: EffectPromptMeta(
        value_type="float",
        example=0.05,
        references=_refs(("small", "0.05"), ("medium", "0.1"), ("talent_tier", "0.2")),
    ),
    LEGAL_ACTIONS: EffectPromptMeta(value_type="list[str]", example=True),
}


def get_effect_prompt_meta(effect_key: str) -> EffectPromptMeta:
    return EFFECT_PROMPT_META[effect_key]


def get_effect_prompt_meta_map() -> dict[str, EffectPromptMeta]:
    missing = [effect_key for effect_key in ALL_EFFECTS if effect_key not in EFFECT_PROMPT_META]
    if missing:
        raise ValueError(f"Missing prompt metadata for effects: {', '.join(sorted(missing))}")
    return EFFECT_PROMPT_META
