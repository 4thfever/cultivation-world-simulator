from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.classes.core.sect import sects_by_id, sects_by_name
from src.classes.items.auxiliary import auxiliaries_by_id, auxiliaries_by_name
from src.classes.items.registry import ItemRegistry
from src.classes.sect_metadata import sync_world_sect_metadata
from src.classes.items.weapon import weapons_by_id, weapons_by_name
from src.classes.technique import techniques_by_id, techniques_by_name

if TYPE_CHECKING:
    from src.classes.core.world import World


def build_world_lore_snapshot(world: "World") -> dict[str, dict[str, dict[str, str]]]:
    return {
        "regions": _build_regions_snapshot(world),
        "sects": _build_named_snapshot(sects_by_id),
        "techniques": _build_named_snapshot(techniques_by_id),
        "weapons": _build_named_snapshot(weapons_by_id),
        "auxiliaries": _build_named_snapshot(auxiliaries_by_id),
    }


def apply_world_lore_snapshot(world: "World", snapshot: dict[str, Any] | None) -> None:
    if not isinstance(snapshot, dict) or not snapshot:
        return

    _apply_regions_snapshot(world, snapshot.get("regions"))
    _apply_named_snapshot(snapshot.get("sects"), sects_by_id, sects_by_name)
    _apply_named_snapshot(snapshot.get("techniques"), techniques_by_id, techniques_by_name)
    _apply_items_snapshot(snapshot.get("weapons"), weapons_by_id, weapons_by_name)
    _apply_items_snapshot(snapshot.get("auxiliaries"), auxiliaries_by_id, auxiliaries_by_name)
    sync_world_sect_metadata(world)


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
        if obj is None:
            continue
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
