from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from fastapi import HTTPException

from src.classes.custom_content import CustomContentRegistry, is_custom_content_id
from src.classes.language import language_manager
from src.classes.effect import (
    ALL_EFFECTS,
    LEGAL_ACTIONS,
    get_effect_prompt_meta,
    get_effect_prompt_meta_map,
    format_effects_to_text,
)
from src.classes.effect.desc import get_effect_desc
from src.classes.items.auxiliary import Auxiliary, auxiliaries_by_id
from src.classes.items.weapon import Weapon, weapons_by_id
from src.classes.technique import (
    Technique,
    TechniqueAttribute,
    TechniqueGrade,
    techniques_by_id,
)
from src.classes.weapon_type import WeaponType
from src.i18n import t
from src.i18n.locale_registry import get_fallback_locale, get_source_locale, normalize_locale_code
from src.systems.cultivation import Realm
from src.utils.config import CONFIG
from src.utils.llm.client import call_llm_with_task_name


CustomCategory = Literal["technique", "weapon", "auxiliary"]
FORBIDDEN_EFFECT_KEYS = {
    LEGAL_ACTIONS,
}

_EXAMPLE_VALUES = {
    "extra_battle_strength_points": 3,
    "extra_max_hp": 30,
    "extra_observation_radius": 1,
    "extra_appearance": 1,
    "extra_respire_exp": 20,
    "extra_respire_exp_multiplier": 0.2,
    "respire_duration_reduction": 0.1,
    "temper_duration_reduction": 0.1,
    "extra_breakthrough_success_rate": 0.1,
    "extra_retreat_success_rate": 0.1,
    "extra_dual_cultivation_exp": 50,
    "extra_harvest_materials": 1,
    "extra_hunt_materials": 1,
    "extra_mine_materials": 1,
    "extra_plant_income": 20,
    "extra_move_step": 1,
    "extra_catch_success_rate": 0.1,
    "extra_escape_success_rate": 0.1,
    "extra_assassinate_success_rate": 0.1,
    "extra_luck": 2,
    "extra_fortune_probability": 0.1,
    "extra_misfortune_probability": -0.1,
    "extra_cast_success_rate": 0.1,
    "extra_refine_success_rate": 0.1,
    "extra_sect_mission_success_rate": 0.1,
    "extra_weapon_proficiency_gain": 0.2,
    "extra_weapon_upgrade_chance": 0.1,
    "extra_max_lifespan": 10,
    "extra_hp_recovery_rate": 0.2,
    "damage_reduction": 0.1,
    "realm_suppression_bonus": 0.05,
    "extra_item_sell_price_multiplier": 0.2,
    "shop_buy_price_reduction": 0.1,
    "extra_plunder_multiplier": 0.5,
    "extra_hidden_domain_drop_prob": 0.1,
    "extra_hidden_domain_danger_prob": -0.1,
    "extra_epiphany_probability": 0.05,
}

_REFERENCE_LABEL_DISPLAY = {
    "small": "small",
    "medium": "medium",
    "large": "large",
    "cap": "cap",
    "very_high": "very high",
    "base_chance": "base chance",
    "base_value": "base value",
    "ordinary": "ordinary",
    "fortunate": "fortunate",
    "protagonist_tier": "protagonist-tier",
    "unlucky": "unlucky",
    "tanky": "tanky",
    "profit_focused": "profit-focused",
    "safer": "safer",
    "riskier": "riskier",
    "talent_tier": "talent-tier",
}

_CONSTRAINT_DISPLAY = {
    "final_multiplier_floor_1_0": "final multiplier >= 1.0",
}

_CATEGORY_LABEL_MSGIDS = {
    "technique": "custom_content.category.technique",
    "weapon": "custom_content.category.weapon",
    "auxiliary": "custom_content.category.auxiliary_equipment",
}

_PROMPT_TEXT_MSGIDS = {
    "name": "custom_content.label.name",
    "desc": "custom_content.label.description",
    "attribute": "custom_content.label.attribute",
    "grade": "custom_content.label.grade",
    "weapon_type": "custom_content.label.weapon_type",
    "realm": "custom_content.label.realm",
    "effect_desc": "custom_content.label.effect_summary",
    "effects": "custom_content.label.effects",
    "value_type": "custom_content.label.value_type",
    "example": "custom_content.label.example",
    "magnitude_guidance": "custom_content.label.magnitude_guidance",
    "same_type_reference": "custom_content.reference.same_category",
    "same_type_same_realm_reference": "custom_content.reference.same_category_realm",
    "scope_without_realm": "custom_content.scope.without_realm",
    "scope_with_realm": "custom_content.scope.with_realm",
}

def _get_prompt_locale() -> str:
    return normalize_locale_code(str(language_manager.current))


def _prompt_text(key: str) -> str:
    return t(_PROMPT_TEXT_MSGIDS[key])


def _category_label(category: CustomCategory) -> str:
    return t(_CATEGORY_LABEL_MSGIDS[category])


def _iter_template_locale_codes() -> list[str]:
    ordered: list[str] = []
    for locale_code in (_get_prompt_locale(), get_fallback_locale(), get_source_locale()):
        normalized = normalize_locale_code(locale_code)
        if normalized not in ordered:
            ordered.append(normalized)
    return ordered


def _resolve_template_path(filename: str) -> Path:
    template_path = CONFIG.paths.templates / filename
    if template_path.exists():
        return template_path

    locales_dir = Path(CONFIG.paths.get("locales", Path("static/locales")))
    for locale_code in _iter_template_locale_codes():
        candidate = locales_dir / locale_code / "templates" / filename
        if candidate.exists():
            return candidate

    return template_path


def _format_effect_examples() -> str:
    lines: list[str] = []
    for effect_key in ALL_EFFECTS:
        if effect_key in FORBIDDEN_EFFECT_KEYS:
            continue
        effect_name = get_effect_desc(effect_key)
        meta = get_effect_prompt_meta(effect_key)
        example = _EXAMPLE_VALUES.get(effect_key, meta.example)
        type_name = meta.value_type
        reference_text = _format_reference_text(effect_key)
        if reference_text:
            lines.append(
                f"- {effect_key}: {effect_name}, {_prompt_text('value_type')} {type_name}, {_prompt_text('example')} {example}. {_prompt_text('magnitude_guidance')}: {reference_text}"
            )
        else:
            lines.append(f"- {effect_key}: {effect_name}, {_prompt_text('value_type')} {type_name}, {_prompt_text('example')} {example}")
    return "\n".join(lines)


@lru_cache(maxsize=1)
def _get_effect_reference_text_map() -> dict[str, str]:
    result: dict[str, str] = {}
    for effect_key, meta in get_effect_prompt_meta_map().items():
        parts = [
            f"{_REFERENCE_LABEL_DISPLAY.get(reference.key, reference.key)}: {reference.value}"
            for reference in meta.references
        ]
        parts.extend(_CONSTRAINT_DISPLAY.get(constraint, constraint) for constraint in meta.constraints)
        if parts:
            result[effect_key] = "; ".join(parts)
    return result


def _format_reference_text(effect_key: str) -> str:
    return _get_effect_reference_text_map().get(effect_key, "")


def _serialize_reference_item(item: Technique | Weapon | Auxiliary, category: CustomCategory) -> str:
    base = [
        f"{_prompt_text('name')}: {item.name}",
        f"{_prompt_text('desc')}: {item.desc}",
    ]
    if category == "technique":
        technique = item
        base.append(f"{_prompt_text('attribute')}: {technique.attribute.value}")
        base.append(f"{_prompt_text('grade')}: {technique.grade.value}")
    elif category == "weapon":
        weapon = item
        base.append(f"{_prompt_text('weapon_type')}: {weapon.weapon_type.value}")
        base.append(f"{_prompt_text('realm')}: {weapon.realm.value}")
    else:
        auxiliary = item
        base.append(f"{_prompt_text('realm')}: {auxiliary.realm.value}")

    if item.effect_desc:
        base.append(f"{_prompt_text('effect_desc')}: {item.effect_desc}")
    if item.effects:
        base.append(f"{_prompt_text('effects')}: {item.effects}")
    return "; ".join(base)


def build_reference_items_text(category: CustomCategory, realm: Realm | None, *, limit: int = 8) -> str:
    if category == "technique":
        items = list(techniques_by_id.values())
    elif category == "weapon":
        if realm is None:
            raise HTTPException(status_code=400, detail="realm is required for weapon generation")
        exact_matches = [item for item in weapons_by_id.values() if item.realm == realm]
        items = exact_matches or list(weapons_by_id.values())
    else:
        if realm is None:
            raise HTTPException(status_code=400, detail="realm is required for auxiliary generation")
        exact_matches = [item for item in auxiliaries_by_id.values() if item.realm == realm]
        items = exact_matches or list(auxiliaries_by_id.values())

    items = sorted(items, key=lambda item: (is_custom_content_id(getattr(item, "id", 0)), getattr(item, "id", 0)))
    return "\n".join(
        f"{idx}. {_serialize_reference_item(item, category)}"
        for idx, item in enumerate(items[:limit], start=1)
    )


def validate_custom_effects(effects: object) -> dict[str, object]:
    if not isinstance(effects, dict) or not effects:
        raise HTTPException(status_code=400, detail="effects must be a non-empty object")

    validated: dict[str, object] = {}
    allowed_keys = set(ALL_EFFECTS) - FORBIDDEN_EFFECT_KEYS
    for key, value in effects.items():
        if key not in allowed_keys:
            raise HTTPException(status_code=400, detail=f"Unsupported custom effect: {key}")
        if key in {"when", "_desc"}:
            raise HTTPException(status_code=400, detail=f"Unsupported custom effect field: {key}")
        if isinstance(value, str):
            if "avatar." in value or value.strip().startswith("eval("):
                raise HTTPException(status_code=400, detail=f"Dynamic effect value is not allowed: {key}")
            raise HTTPException(status_code=400, detail=f"String effect value is not allowed: {key}")
        if isinstance(value, list):
            raise HTTPException(status_code=400, detail=f"List effect value is not allowed: {key}")
        if not isinstance(value, (int, float, bool)):
            raise HTTPException(status_code=400, detail=f"Unsupported effect value type: {key}")
        validated[str(key)] = value
    return validated


def normalize_custom_draft(category: CustomCategory, draft: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(draft, dict):
        raise HTTPException(status_code=400, detail="draft must be an object")

    name = str(draft.get("name", "") or "").strip()
    desc = str(draft.get("desc", "") or "").strip()
    if not name or not desc:
        raise HTTPException(status_code=400, detail="name and desc are required")

    effects = validate_custom_effects(draft.get("effects"))

    normalized: dict[str, Any] = {
        "category": category,
        "name": name,
        "desc": desc,
        "effects": effects,
        "effect_desc": format_effects_to_text(effects),
        "is_custom": True,
    }

    if category == "technique":
        try:
            normalized["attribute"] = TechniqueAttribute(str(draft.get("attribute", "GOLD"))).value
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid technique attribute") from exc
        normalized["grade"] = TechniqueGrade.from_str(str(draft.get("grade", "LOWER"))).value
    elif category == "weapon":
        realm_raw = draft.get("realm")
        if not realm_raw:
            raise HTTPException(status_code=400, detail="realm is required for weapon")
        normalized["realm"] = Realm.from_str(str(realm_raw)).value
        normalized["weapon_type"] = WeaponType.from_str(str(draft.get("weapon_type", "SWORD"))).value
    else:
        realm_raw = draft.get("realm")
        if not realm_raw:
            raise HTTPException(status_code=400, detail="realm is required for auxiliary")
        normalized["realm"] = Realm.from_str(str(realm_raw)).value

    return normalized


async def generate_custom_content_draft(category: CustomCategory, realm: Realm | None, user_prompt: str) -> dict[str, Any]:
    prompt = str(user_prompt or "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="user_prompt is required")

    template_path = _resolve_template_path("custom_content.txt")

    infos = {
        "category_label": _category_label(category),
        "scope_hint": _prompt_text("scope_with_realm").format(realm=str(realm), category_label=_category_label(category))
        if realm is not None
        else _prompt_text("scope_without_realm").format(category_label=_category_label(category)),
        "reference_hint": _prompt_text("same_type_same_realm_reference")
        if realm is not None
        else _prompt_text("same_type_reference"),
        "user_prompt": prompt,
        "reference_items": build_reference_items_text(category, realm),
        "allowed_effects": _format_effect_examples(),
    }
    result = await call_llm_with_task_name(
        task_name="custom_content_generation",
        template_path=template_path,
        infos=infos,
        max_retries=2,
    )
    if not isinstance(result, dict):
        raise HTTPException(status_code=500, detail="LLM draft result is invalid")

    if realm is not None:
        result["realm"] = realm.value
    return normalize_custom_draft(category, result)


def create_custom_content_from_draft(category: CustomCategory, draft: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_custom_draft(category, draft)
    effects = dict(normalized["effects"])
    if category == "technique":
        item = Technique(
            id=CustomContentRegistry.allocate_id("technique"),
            name=normalized["name"],
            attribute=TechniqueAttribute(str(normalized["attribute"])),
            grade=TechniqueGrade.from_str(str(normalized["grade"])),
            desc=normalized["desc"],
            weight=0.0,
            condition="",
            realm=None,
            sect_id=None,
            effects=effects,
            effect_desc=normalized["effect_desc"],
        )
        CustomContentRegistry.register_technique(item)
    elif category == "weapon":
        realm = Realm.from_str(normalized["realm"])
        item = Weapon(
            id=CustomContentRegistry.allocate_id("weapon"),
            name=normalized["name"],
            weapon_type=WeaponType.from_str(str(normalized["weapon_type"])),
            realm=realm,
            desc=normalized["desc"],
            effects=effects,
            effect_desc=normalized["effect_desc"],
        )
        CustomContentRegistry.register_weapon(item)
    else:
        realm = Realm.from_str(normalized["realm"])
        item = Auxiliary(
            id=CustomContentRegistry.allocate_id("auxiliary"),
            name=normalized["name"],
            realm=realm,
            desc=normalized["desc"],
            effects=effects,
            effect_desc=normalized["effect_desc"],
        )
        CustomContentRegistry.register_auxiliary(item)

    payload = item.get_structured_info()
    payload["id"] = int(payload["id"])
    payload["is_custom"] = True
    if "realm" in normalized:
        payload["realm"] = normalized["realm"]
    return payload
