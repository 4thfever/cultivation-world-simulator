from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import HTTPException

from src.classes.custom_content import CustomContentRegistry
from src.classes.effect import format_effects_to_text
from src.classes.goldfinger import Goldfinger
from src.classes.language import language_manager
from src.classes.rarity import get_rarity_from_str
from src.i18n.template_resolver import resolve_locale_template_path
from src.utils.config import CONFIG
from src.utils.llm.client import call_llm_with_task_name

from .custom_content_service import build_allowed_effects_text, validate_custom_effects


def _resolve_template_path(filename: str) -> Path:
    return resolve_locale_template_path(
        filename,
        current_locale=str(language_manager.current),
        preferred_dir=CONFIG.paths.templates,
    )


def normalize_custom_goldfinger_draft(draft: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(draft, dict):
        raise HTTPException(status_code=400, detail="draft must be an object")

    name = str(draft.get("name", "") or "").strip()
    desc = str(draft.get("desc", "") or "").strip()
    story_prompt = str(draft.get("story_prompt", "") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="name is required")

    effects = validate_custom_effects(draft.get("effects"))
    normalized_desc = desc or f"{name}会持续影响角色命数与发展。"
    normalized_story_prompt = story_prompt or f"若角色拥有“{name}”外挂，请围绕其外挂特征展开故事，并突出其超规格之处。"
    rarity_raw = str(draft.get("rarity", "SSR") or "SSR").strip().upper()
    normalized_rarity = rarity_raw if rarity_raw in {"SR", "SSR"} else "SSR"

    return {
        "category": "goldfinger",
        "name": name,
        "desc": normalized_desc,
        "story_prompt": normalized_story_prompt,
        "effects": effects,
        "effect_desc": format_effects_to_text(effects),
        "mechanism_type": "effect_only",
        "rarity": normalized_rarity,
        "is_custom": True,
    }


async def generate_custom_goldfinger_draft(user_prompt: str) -> dict[str, Any]:
    prompt = str(user_prompt or "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="user_prompt is required")

    template_path = _resolve_template_path("custom_goldfinger.txt")
    result = await call_llm_with_task_name(
        task_name="custom_content_generation",
        template_path=template_path,
        infos={
            "allowed_effects": build_allowed_effects_text(),
            "user_prompt": prompt,
        },
        max_retries=2,
    )
    if not isinstance(result, dict):
        raise HTTPException(status_code=500, detail="LLM draft result is invalid")
    return normalize_custom_goldfinger_draft(result)


def create_custom_goldfinger_from_draft(draft: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_custom_goldfinger_draft(draft)
    allocated_id = CustomContentRegistry.allocate_id("goldfinger")
    goldfinger = Goldfinger(
        id=allocated_id,
        key=f"CUSTOM_GOLDFINGER_{allocated_id}",
        name=normalized["name"],
        desc=normalized["desc"],
        exclusion_keys=[],
        rarity=get_rarity_from_str(str(normalized.get("rarity", "SSR"))),
        condition="",
        effects=dict(normalized["effects"]),
        effect_desc=normalized["effect_desc"],
        mechanism_type="effect_only",
        story_prompt=normalized["story_prompt"],
        mechanism_config={},
    )
    CustomContentRegistry.register_goldfinger(goldfinger)

    payload = goldfinger.get_structured_info()
    payload["id"] = int(payload["id"])
    payload["is_custom"] = True
    return payload
