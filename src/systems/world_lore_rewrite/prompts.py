from __future__ import annotations

from pathlib import Path
from typing import Any

from src.classes.language import language_manager
from src.i18n.locale_registry import normalize_locale_code
from src.i18n.template_resolver import resolve_locale_template_path
from src.utils.config import CONFIG
from src.utils.strings import to_json_str_with_intent

from .models import RewriteJob


def get_prompt_locale() -> str:
    return normalize_locale_code(str(language_manager.current))


def resolve_world_lore_template(filename: str) -> Path:
    return resolve_locale_template_path(
        filename,
        current_locale=get_prompt_locale(),
        preferred_dir=CONFIG.paths.templates,
    )


def build_rewrite_infos(job: RewriteJob, *, previous_error: str = "") -> dict[str, Any]:
    payload: dict[str, Any] = {
        "world_lore": job.lore_text,
        "style_guide": to_json_str_with_intent(job.style_guide),
        "map_summary": to_json_str_with_intent(job.map_summary),
        "entity_label": job.entity_label,
        "instructions": job.instructions,
        "entities_json": to_json_str_with_intent(job.entities),
        "result_field": job.result_field,
        "previous_error": previous_error or "无",
    }
    if job.paired_entities:
        payload["paired_entity_label"] = job.paired_entity_label
        payload["paired_entities_json"] = to_json_str_with_intent(job.paired_entities)
        payload["paired_result_field"] = job.paired_result_field
    else:
        payload["paired_entity_label"] = ""
        payload["paired_entities_json"] = "[]"
        payload["paired_result_field"] = ""
    return payload


def build_style_guide_infos(lore_text: str) -> dict[str, Any]:
    return {
        "world_lore": lore_text,
    }
