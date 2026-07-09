from __future__ import annotations

from dataclasses import asdict
from typing import TYPE_CHECKING, Any

from src.classes.core.sect import sects_by_id, sects_by_name
from src.classes.items.auxiliary import auxiliaries_by_id, auxiliaries_by_name
from src.classes.items.registry import ItemRegistry
from src.classes.items.weapon import weapons_by_id, weapons_by_name
from src.classes.sect_metadata import sync_world_sect_metadata
from src.classes.technique import techniques_by_id, techniques_by_name

if TYPE_CHECKING:
    from src.classes.core.world import World
    from src.systems.world_lore_rewrite.models import WorldLoreRewriteConfig, WorldLoreRewriteDraft


def build_world_lore_snapshot(
    world: "World",
    *,
    lore_text: str | None = None,
    draft: "WorldLoreRewriteDraft | None" = None,
    rewrite_config: "WorldLoreRewriteConfig | None" = None,
) -> dict[str, Any]:
    game_map = getattr(world, "map", None)
    snapshot: dict[str, Any] = {
        "schema_version": 2,
        "lore_text": str(lore_text if lore_text is not None else getattr(world.world_lore, "text", "") or ""),
        "map_id": str(getattr(game_map, "map_id", "") or ""),
        "map_name": str(getattr(game_map, "map_name", "") or ""),
        "preset_version": int(getattr(game_map, "preset_version", 0) or 0),
        "rewrite_config": _config_to_snapshot(rewrite_config),
        "stats": _stats_to_snapshot(draft),
        "regions": _build_regions_snapshot(world),
        "sects": _build_named_snapshot(sects_by_id),
        "techniques": _build_named_snapshot(techniques_by_id),
        "weapons": _build_named_snapshot(weapons_by_id),
        "auxiliaries": _build_named_snapshot(auxiliaries_by_id),
    }
    return snapshot


def apply_world_lore_snapshot(world: "World", snapshot: dict[str, Any] | None) -> None:
    if not isinstance(snapshot, dict) or not snapshot:
        return
    if int(snapshot.get("schema_version", 0) or 0) != 2:
        return

    _apply_regions_snapshot(world, snapshot.get("regions"))
    _apply_named_snapshot(snapshot.get("sects"), sects_by_id, sects_by_name)
    _apply_named_snapshot(snapshot.get("techniques"), techniques_by_id, techniques_by_name)
    _apply_items_snapshot(snapshot.get("weapons"), weapons_by_id, weapons_by_name)
    _apply_items_snapshot(snapshot.get("auxiliaries"), auxiliaries_by_id, auxiliaries_by_name)
    sync_world_sect_metadata(world)


def _config_to_snapshot(rewrite_config: "WorldLoreRewriteConfig | None") -> dict[str, Any]:
    if rewrite_config is None:
        return {}
    data = asdict(rewrite_config)
    return {
        "rewrite_items": data.get("rewrite_items", True),
        "total_timeout_seconds": data.get("total_timeout_seconds"),
        "task_timeout_seconds": data.get("task_timeout_seconds"),
        "max_parse_retries": data.get("max_parse_retries"),
        "chunk_size": {
            "regions": data.get("chunk_size_regions"),
            "sect_groups": data.get("chunk_size_sect_groups"),
            "techniques": data.get("chunk_size_techniques"),
            "weapons": data.get("chunk_size_weapons"),
            "auxiliaries": data.get("chunk_size_auxiliaries"),
        },
    }


def _stats_to_snapshot(draft: "WorldLoreRewriteDraft | None") -> dict[str, Any]:
    if draft is None:
        return {}
    return {
        "llm_count": int(getattr(draft, "llm_count", 0) or 0),
        "fallback_count": int(getattr(draft, "fallback_count", 0) or 0),
        "elapsed_seconds": float(getattr(draft, "elapsed_seconds", 0.0) or 0.0),
    }


def _build_regions_snapshot(world: "World") -> dict[str, dict[str, str]]:
    regions = getattr(getattr(world, "map", None), "regions", {}) or {}
    return {
        str(region_id): _snapshot_payload(region)
        for region_id, region in regions.items()
    }


def _build_named_snapshot(objects_by_id: dict[int, Any]) -> dict[str, dict[str, str]]:
    return {
        str(obj_id): _snapshot_payload(obj)
        for obj_id, obj in objects_by_id.items()
    }


def _snapshot_payload(obj: Any) -> dict[str, str]:
    return {
        "name": str(getattr(obj, "name", "") or ""),
        "desc": str(getattr(obj, "desc", "") or ""),
    }


def _apply_regions_snapshot(world: "World", snapshot: Any) -> None:
    if not isinstance(snapshot, dict):
        return

    regions = getattr(getattr(world, "map", None), "regions", {}) or {}
    for obj_id_str, payload in snapshot.items():
        obj = _lookup_by_str_id(obj_id_str, regions)
        if obj is None:
            continue
        _apply_payload(obj, payload)


def _apply_named_snapshot(
    snapshot: Any,
    objects_by_id: dict[int, Any],
    objects_by_name: dict[str, Any],
) -> None:
    if not isinstance(snapshot, dict):
        return

    for obj_id_str, payload in snapshot.items():
        obj = _lookup_by_str_id(obj_id_str, objects_by_id)
        if obj is None:
            continue
        old_name = str(getattr(obj, "name", "") or "")
        _apply_payload(obj, payload)
        new_name = str(getattr(obj, "name", "") or "")
        if new_name and new_name != old_name:
            objects_by_name.pop(old_name, None)
            objects_by_name[new_name] = obj


def _apply_items_snapshot(
    snapshot: Any,
    objects_by_id: dict[int, Any],
    objects_by_name: dict[str, Any],
) -> None:
    _apply_named_snapshot(snapshot, objects_by_id, objects_by_name)
    if not isinstance(snapshot, dict):
        return

    for obj_id_str in snapshot:
        obj = _lookup_by_str_id(obj_id_str, objects_by_id)
        if obj is not None:
            ItemRegistry.register(int(getattr(obj, "id")), obj)


def _lookup_by_str_id(obj_id_str: Any, mapping: dict[int, Any]) -> Any | None:
    try:
        return mapping.get(int(obj_id_str))
    except (TypeError, ValueError):
        return None


def _apply_payload(obj: Any, payload: Any) -> None:
    if not isinstance(payload, dict):
        return
    if "name" in payload:
        obj.name = str(payload.get("name") or "")
    if "desc" in payload:
        obj.desc = str(payload.get("desc") or "")
