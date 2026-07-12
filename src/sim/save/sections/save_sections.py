from __future__ import annotations

from datetime import datetime
from typing import Any

import src.utils.config as app_config
from src.classes.custom_content import CustomContentRegistry
from src.classes.language import language_manager
from src.classes.world_lore_snapshot import build_world_lore_snapshot
from src.config import get_settings_service
from src.run.map_snapshot import serialize_map_snapshot
from src.systems.opportunity import serialize_opportunities
from src.systems.world_secret import serialize_world_secret

from .base import SaveContext


def _model_to_dict(model):
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def run_config_snapshot(context: SaveContext) -> dict[str, Any]:
    snapshot = getattr(context.world, "run_config_snapshot", None)
    if snapshot:
        return snapshot
    snapshot = _model_to_dict(get_settings_service().get_default_run_config())
    snapshot["content_locale"] = str(language_manager)
    return snapshot


class MetaSection:
    key = "meta"

    def dump(self, context: SaveContext) -> dict[str, Any]:
        world = context.world
        snapshot = run_config_snapshot(context)
        alive_count = len(world.avatar_manager.avatars)
        dead_count = len(world.avatar_manager.dead_avatars)
        total_count = alive_count + dead_count
        return {
            "version": app_config.CONFIG.meta.version,
            "save_time": datetime.now().isoformat(),
            "game_time": f"{world.month_stamp.get_year()}年{world.month_stamp.get_month().value}月",
            "language": snapshot.get("content_locale", str(language_manager)),
            "events_db": str(context.events_db_path.name),
            "event_count": world.event_manager.count(),
            "avatar_count": total_count,
            "alive_count": alive_count,
            "dead_count": dead_count,
            "custom_name": context.custom_name,
            "playthrough_id": getattr(world, "playthrough_id", ""),
            "is_auto_save": context.is_auto_save,
            "map_id": snapshot.get("map_id", getattr(world.map, "map_id", "classic")),
            "map_name": getattr(world.map, "map_name", ""),
        }


class RunConfigSection:
    key = "run_config"

    def dump(self, context: SaveContext) -> dict[str, Any]:
        return run_config_snapshot(context)


class CustomContentSection:
    key = "custom_content"

    def dump(self, _context: SaveContext) -> dict[str, Any]:
        return CustomContentRegistry.to_save_dict()


class WorldSection:
    key = "world"

    def dump(self, context: SaveContext) -> dict[str, Any]:
        world = context.world
        from src.classes.environment.region import CityRegion, CultivateRegion

        cultivate_regions_hosts = {}
        regions_status = {}
        if hasattr(world.map, "regions"):
            for rid, region in world.map.regions.items():
                if isinstance(region, CultivateRegion) and region.host_avatar:
                    cultivate_regions_hosts[str(rid)] = region.host_avatar.id
                if isinstance(region, CityRegion):
                    regions_status[str(rid)] = {"population": region.population}

        sect_runtime_states = {
            str(sect.id): {
                "magic_stone": int(getattr(sect, "magic_stone", 0) or 0),
                "is_active": bool(getattr(sect, "is_active", True)),
                "periodic_thinking": str(getattr(sect, "periodic_thinking", "") or ""),
                "last_decision_summary": str(getattr(sect, "last_decision_summary", "") or ""),
                "sect_effects": dict(getattr(sect, "sect_effects", {}) or {}),
                "temporary_sect_effects": list(getattr(sect, "temporary_sect_effects", []) or []),
                "war_weariness": int(getattr(sect, "war_weariness", 0) or 0),
            }
            for sect in context.existed_sects
        }

        return {
            "month_stamp": int(world.month_stamp),
            "start_year": world.start_year,
            "map_snapshot": serialize_map_snapshot(world.map),
            "existed_sect_ids": [sect.id for sect in context.existed_sects],
            "dynasty": world.dynasty.to_dict() if getattr(world, "dynasty", None) is not None else None,
            "current_phenomenon_id": world.current_phenomenon.id if world.current_phenomenon else None,
            "phenomenon_start_year": world.phenomenon_start_year if hasattr(world, "phenomenon_start_year") else 0,
            "cultivate_regions_hosts": cultivate_regions_hosts,
            "regions_status": regions_status,
            "region_formations": {
                str(region_id): dict(formation)
                for region_id, formation in (getattr(world.map, "region_formations", {}) or {}).items()
            },
            "circulation": world.circulation.to_save_dict(),
            "world_lore": {"text": world.world_lore.text},
            "world_lore_snapshot": getattr(world, "world_lore_snapshot", None) or build_world_lore_snapshot(world),
            "world_secret": serialize_world_secret(world),
            "sect_runtime_states": sect_runtime_states,
            "sect_relation_modifiers": list(getattr(world, "sect_relation_modifiers", []) or []),
            "sect_wars": list(getattr(world, "sect_wars", []) or []),
            "opportunities": serialize_opportunities(world),
            "deceased_records": world.deceased_manager.to_save_list(),
        }


class AvatarsSection:
    key = "avatars"

    def dump(self, context: SaveContext) -> list[dict[str, Any]]:
        return [avatar.to_save_dict() for avatar in context.world.avatar_manager._iter_all_avatars()]


class EventsSection:
    key = "events"

    def dump(self, context: SaveContext) -> list[dict[str, Any]]:
        max_events = app_config.CONFIG.save.max_events_to_save
        return [
            event.to_dict()
            for event in context.world.event_manager.get_recent_events(limit=max_events)
        ]


class SimulatorSection:
    key = "simulator"

    def dump(self, context: SaveContext) -> dict[str, Any]:
        return {"awakening_rate": context.simulator.awakening_rate}
