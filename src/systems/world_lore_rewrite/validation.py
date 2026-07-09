from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import EntityRewrite, RewriteJob, WorldLoreRewriteDraft


class WorldLoreValidationError(ValueError):
    pass


_FORBIDDEN_TEXT = (
    "玩家",
    "系统",
    "游戏",
    "机制",
    "攻击力",
    "防御力",
    "加成",
    "+",
    "%",
)


@dataclass(frozen=True)
class ValidatedJobResult:
    rewrites: list[EntityRewrite]
    paired_rewrites: list[EntityRewrite]


def validate_job_result(job: RewriteJob, result: dict[str, Any], *, source: str = "llm") -> ValidatedJobResult:
    if not isinstance(result, dict):
        raise WorldLoreValidationError("LLM result must be an object")

    rewrites = _validate_entities(
        raw=result.get(job.result_field),
        expected_ids=job.expected_ids,
        field_name=job.result_field,
        source=source,
    )

    paired_rewrites: list[EntityRewrite] = []
    if job.paired_entities:
        paired_rewrites = _validate_entities(
            raw=result.get(job.paired_result_field),
            expected_ids=job.paired_expected_ids,
            field_name=job.paired_result_field,
            source=source,
        )

    return ValidatedJobResult(rewrites=rewrites, paired_rewrites=paired_rewrites)


def draft_from_validated_job(job: RewriteJob, result: ValidatedJobResult) -> WorldLoreRewriteDraft:
    draft = WorldLoreRewriteDraft()
    target = _target_for_kind(draft, job.kind)
    for rewrite in result.rewrites:
        target[rewrite.id] = rewrite

    if job.kind == "sect_group":
        for rewrite in result.paired_rewrites:
            draft.regions[rewrite.id] = rewrite

    if result.rewrites or result.paired_rewrites:
        if any(rewrite.source == "fallback" for rewrite in [*result.rewrites, *result.paired_rewrites]):
            draft.fallback_count += len(result.rewrites) + len(result.paired_rewrites)
        else:
            draft.llm_count += len(result.rewrites) + len(result.paired_rewrites)
    return draft


def _validate_entities(
    *,
    raw: Any,
    expected_ids: set[int],
    field_name: str,
    source: str,
) -> list[EntityRewrite]:
    if not isinstance(raw, list):
        raise WorldLoreValidationError(f"{field_name} must be a list")
    if len(raw) != len(expected_ids):
        raise WorldLoreValidationError(f"{field_name} count mismatch: expected {len(expected_ids)}, got {len(raw)}")

    rewrites: list[EntityRewrite] = []
    seen: set[int] = set()
    for item in raw:
        if not isinstance(item, dict):
            raise WorldLoreValidationError(f"{field_name} item must be an object")
        try:
            entity_id = int(item.get("id"))
        except (TypeError, ValueError) as exc:
            raise WorldLoreValidationError(f"{field_name} item has invalid id") from exc
        if entity_id not in expected_ids:
            raise WorldLoreValidationError(f"{field_name} has unexpected id: {entity_id}")
        if entity_id in seen:
            raise WorldLoreValidationError(f"{field_name} has duplicate id: {entity_id}")
        seen.add(entity_id)

        name = _clean_text(item.get("name"))
        desc = _clean_text(item.get("desc"))
        if not name or not desc:
            raise WorldLoreValidationError(f"{field_name} id {entity_id} requires non-empty name and desc")
        if len(name) > 40:
            raise WorldLoreValidationError(f"{field_name} id {entity_id} name is too long")
        if len(desc) > 260:
            raise WorldLoreValidationError(f"{field_name} id {entity_id} desc is too long")
        if _contains_forbidden_text(desc):
            raise WorldLoreValidationError(f"{field_name} id {entity_id} desc contains mechanics text")
        rewrites.append(EntityRewrite(id=entity_id, name=name, desc=desc, source=source))  # type: ignore[arg-type]

    if seen != expected_ids:
        missing = sorted(expected_ids - seen)
        raise WorldLoreValidationError(f"{field_name} missing ids: {missing}")
    return rewrites


def _target_for_kind(draft: WorldLoreRewriteDraft, kind: str) -> dict[int, EntityRewrite]:
    if kind == "regions":
        return draft.regions
    if kind == "sect_group":
        return draft.sects
    if kind == "techniques":
        return draft.techniques
    if kind == "weapons":
        return draft.weapons
    if kind == "auxiliaries":
        return draft.auxiliaries
    raise WorldLoreValidationError(f"unknown job kind: {kind}")


def _clean_text(value: object) -> str:
    return str(value or "").strip().replace("\r", " ").replace("\n", " ")


def _contains_forbidden_text(value: str) -> bool:
    return any(token in value for token in _FORBIDDEN_TEXT)
