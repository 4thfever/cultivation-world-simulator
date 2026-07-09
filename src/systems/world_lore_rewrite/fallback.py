from __future__ import annotations

from typing import Any

from .models import EntityRewrite, RewriteJob, WorldLoreRewriteDraft
from .validation import ValidatedJobResult, draft_from_validated_job, validate_job_result


def build_fallback_style_guide(lore_text: str) -> dict[str, Any]:
    tone = _tone_prefix(lore_text)
    return {
        "world_tone": tone or "本局世界观",
        "naming_rules": ["名称应转译世界观气质，而不是把关键词直接贴到旧名上", "避免重复使用同一词根"],
        "forbidden_patterns": ["不要写数值加成", "不要写系统机制", "不要机械前缀化"],
        "description_style": "简洁、具体、有画面感",
    }


def fallback_job(job: RewriteJob) -> WorldLoreRewriteDraft:
    result: dict[str, Any] = {
        job.result_field: [_fallback_entity(entity, job.entity_label, job.lore_text) for entity in job.entities],
    }
    if job.paired_entities:
        result[job.paired_result_field] = [
            _fallback_entity(entity, job.paired_entity_label, job.lore_text)
            for entity in job.paired_entities
        ]
    validated = validate_job_result(job, result, source="fallback")
    return draft_from_validated_job(job, validated)


def _fallback_entity(entity: dict[str, Any], label: str, lore_text: str) -> dict[str, Any]:
    entity_id = int(entity["id"])
    old_name = str(entity.get("name") or f"{label}{entity_id}").strip()
    motif = _fallback_motif(lore_text, entity_id)
    name = _blend_name(old_name, motif)
    if len(name) > 36:
        name = name[:36]

    desc = (
        f"{name}仍保留旧日的形貌与用途，却被新的时代秩序悄然改写。"
        f"当地传闻将它与{motif}相连，使原本熟悉的来历多了一层压抑而具体的气息。"
    )
    return {
        "id": entity_id,
        "name": name,
        "desc": desc,
    }


def _tone_prefix(lore_text: str) -> str:
    text = str(lore_text or "").strip()
    for char in "，。；、,.!?！？\n\r\t ":
        text = text.replace(char, " ")
    for part in text.split(" "):
        part = part.strip()
        if 2 <= len(part) <= 4:
            return part
    return "新世"


def _fallback_motif(lore_text: str, entity_id: int) -> str:
    text = str(lore_text or "")
    if "加班" in text or "班" in text:
        motifs = ["更漏", "灯牍", "夜签", "催檄", "疲钟", "案牍"]
        return motifs[entity_id % len(motifs)]
    if "末法" in text:
        motifs = ["残灵", "灰脉", "断霞", "枯潮", "废炉", "冷星"]
        return motifs[entity_id % len(motifs)]
    if "妖" in text:
        motifs = ["异纹", "兽月", "灵蜕", "荒血", "百骸", "伏鳞"]
        return motifs[entity_id % len(motifs)]
    return _tone_prefix(text)


def _blend_name(old_name: str, motif: str) -> str:
    if not motif:
        return old_name
    if len(old_name) <= 2:
        return f"{motif}{old_name}"
    midpoint = max(1, len(old_name) // 2)
    return f"{old_name[:midpoint]}{motif}{old_name[midpoint:]}"
