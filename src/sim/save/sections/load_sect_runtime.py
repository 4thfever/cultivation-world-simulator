from __future__ import annotations

from .base import LoadContext


class SectRuntimeLoadSection:
    key = "sect_runtime"

    def load(self, context: LoadContext) -> None:
        from src.classes.core.sect import sects_by_id
        from src.systems.opportunity import load_opportunities

        world = context.world
        world_data = context.world_data or {}
        existed_sect_ids = world_data.get("existed_sect_ids", [])
        existed_sects = [sects_by_id[sid] for sid in existed_sect_ids if sid in sects_by_id]
        context.existed_sects = existed_sects

        world.sect_relation_modifiers = list(world_data.get("sect_relation_modifiers", []) or [])
        world.prune_expired_sect_relation_modifiers(int(world.month_stamp))
        world.sect_wars = list(world_data.get("sect_wars", []) or [])
        load_opportunities(world, world_data.get("opportunities"))
        world.deceased_manager.load_from_list(world_data.get("deceased_records", []))

        for sect in sects_by_id.values():
            sect.magic_stone = 0
            sect.is_active = True
            sect.periodic_thinking = ""
            sect.last_decision_summary = ""
            sect.sect_effects = {}
            sect.temporary_sect_effects = []
            sect.set_war_weariness(0)

        sect_runtime_states = (
            world_data.get("sect_runtime_states", {})
            or world_data.get("sect_runtime_effects", {})
        )
        for sid_key, state in (sect_runtime_states or {}).items():
            try:
                sid = int(sid_key)
            except (TypeError, ValueError):
                continue
            sect = sects_by_id.get(sid)
            if sect is None:
                continue
            state_dict = state if isinstance(state, dict) else {}
            sect.magic_stone = int(state_dict.get("magic_stone", 0) or 0)
            sect.is_active = bool(state_dict.get("is_active", True))
            sect.periodic_thinking = str(state_dict.get("periodic_thinking", "") or "")
            sect.last_decision_summary = str(state_dict.get("last_decision_summary", "") or "")
            sect.sect_effects = dict(state_dict.get("sect_effects", {}) or {})
            sect.temporary_sect_effects = list(state_dict.get("temporary_sect_effects", []) or [])
            sect.set_war_weariness(state_dict.get("war_weariness", 0))
            sect.cleanup_expired_temporary_sect_effects(int(world.month_stamp))
