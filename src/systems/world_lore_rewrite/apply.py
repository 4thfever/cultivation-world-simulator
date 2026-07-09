from __future__ import annotations

from typing import Any

from src.classes.core.sect import sects_by_id, sects_by_name
from src.classes.items.auxiliary import auxiliaries_by_id, auxiliaries_by_name
from src.classes.items.registry import ItemRegistry
from src.classes.items.weapon import weapons_by_id, weapons_by_name
from src.classes.sect_metadata import sync_world_sect_metadata
from src.classes.technique import techniques_by_id, techniques_by_name

from .models import EntityRewrite, WorldLoreRewriteDraft


def apply_world_lore_rewrite(world: Any, draft: WorldLoreRewriteDraft) -> None:
    _apply_regions(world, draft.regions)
    _apply_named(draft.sects, sects_by_id, sects_by_name)
    _apply_named(draft.techniques, techniques_by_id, techniques_by_name)
    _apply_items(draft.weapons, weapons_by_id, weapons_by_name)
    _apply_items(draft.auxiliaries, auxiliaries_by_id, auxiliaries_by_name)
    sync_world_sect_metadata(world)


def _apply_regions(world: Any, rewrites: dict[int, EntityRewrite]) -> None:
    regions = getattr(getattr(world, "map", None), "regions", {}) or {}
    for entity_id, rewrite in rewrites.items():
        obj = regions.get(int(entity_id))
        if obj is None:
            continue
        obj.name = rewrite.name
        obj.desc = rewrite.desc


def _apply_named(
    rewrites: dict[int, EntityRewrite],
    by_id: dict[int, Any],
    by_name: dict[str, Any],
) -> None:
    for entity_id, rewrite in rewrites.items():
        obj = by_id.get(int(entity_id))
        if obj is None:
            continue
        old_name = str(getattr(obj, "name", "") or "")
        obj.name = rewrite.name
        obj.desc = rewrite.desc
        if rewrite.name != old_name:
            by_name.pop(old_name, None)
            by_name[rewrite.name] = obj


def _apply_items(
    rewrites: dict[int, EntityRewrite],
    by_id: dict[int, Any],
    by_name: dict[str, Any],
) -> None:
    _apply_named(rewrites, by_id, by_name)
    for entity_id in rewrites:
        obj = by_id.get(int(entity_id))
        if obj is not None:
            ItemRegistry.register(int(entity_id), obj)
