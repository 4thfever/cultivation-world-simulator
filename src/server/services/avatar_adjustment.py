from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException

from src.classes.items.auxiliary import auxiliaries_by_id
from src.classes.custom_content import is_custom_content_id
from src.classes.goldfinger import goldfingers_by_id
from src.classes.items.weapon import weapons_by_id
from src.classes.persona import personas_by_id
from src.classes.technique import techniques_by_id

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar


VALID_AVATAR_ADJUSTMENT_CATEGORIES = ("technique", "weapon", "auxiliary", "personas", "goldfinger")


def build_avatar_adjust_options() -> dict:
    return {
        "techniques": [
            _build_option_from_structured(technique.get_structured_info())
            for technique in techniques_by_id.values()
        ],
        "weapons": [
            _build_option_from_structured(weapon.get_structured_info())
            for weapon in weapons_by_id.values()
        ],
        "auxiliaries": [
            _build_option_from_structured(auxiliary.get_structured_info())
            for auxiliary in auxiliaries_by_id.values()
        ],
        "personas": [
            _build_option_from_structured(persona.get_structured_info())
            for persona in personas_by_id.values()
        ],
        "goldfingers": [
            _build_option_from_structured(goldfinger.get_structured_info())
            for goldfinger in goldfingers_by_id.values()
        ],
    }


def apply_avatar_adjustment(
    avatar: "Avatar",
    *,
    category: str,
    target_id: int | None = None,
    persona_ids: list[int] | None = None,
) -> None:
    if category == "technique":
        avatar.technique = None if target_id is None else _get_existing(techniques_by_id, target_id, "Technique")
        avatar.recalc_effects()
        return

    if category == "weapon":
        new_weapon = None if target_id is None else _get_existing(weapons_by_id, target_id, "Weapon").instantiate()
        avatar.change_weapon(new_weapon)
        return

    if category == "auxiliary":
        new_auxiliary = None if target_id is None else _get_existing(auxiliaries_by_id, target_id, "Auxiliary").instantiate()
        avatar.change_auxiliary(new_auxiliary)
        return

    if category == "personas":
        if persona_ids is None:
            raise HTTPException(status_code=400, detail="persona_ids is required for personas adjustment")
        if len(set(persona_ids)) != len(persona_ids):
            raise HTTPException(status_code=400, detail="persona_ids contains duplicate values")

        avatar.personas = [_get_existing(personas_by_id, persona_id, "Persona") for persona_id in persona_ids]
        avatar.recalc_effects()
        return

    if category == "goldfinger":
        avatar.goldfinger = None if target_id is None else _get_existing(goldfingers_by_id, target_id, "Goldfinger")
        if target_id is None:
            avatar.goldfinger_state = {}
        avatar.recalc_effects()
        return

    raise HTTPException(status_code=400, detail=f"Unsupported adjustment category: {category}")


def _build_option_from_structured(raw: dict) -> dict:
    option = dict(raw)
    if "id" in option:
        option["id"] = int(option["id"])
        option["is_custom"] = is_custom_content_id(option["id"])
    return option


def _get_existing(mapping: dict[int, object], item_id: int, item_name: str):
    item = mapping.get(item_id)
    if item is None:
        raise HTTPException(status_code=400, detail=f"{item_name} not found")
    return item
