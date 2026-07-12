from __future__ import annotations

from pathlib import Path
from typing import Any

from src.classes.custom_content import CustomContentRegistry
from src.config import get_settings_service

from .base import LoadContext
from .save_sections import _model_to_dict


def restore_loaded_game(context: LoadContext) -> tuple[Any, Any, list[Any]]:
    from src.classes.core.avatar import Avatar
    from src.classes.core.dynasty import Dynasty
    from src.classes.core.sect import sects_by_id
    from src.classes.event import Event
    from src.classes.relation.relation import RelationState
    from src.classes.world_lore_snapshot import apply_world_lore_snapshot
    from src.run.load_map import load_cultivation_world_map
    from src.run.map_snapshot import load_map_from_snapshot
    from src.sim.load.load_game import get_events_db_path
    from src.sim.simulator import Simulator
    from src.systems.opportunity import load_opportunities
    from src.systems.time import MonthStamp
    from src.systems.world_secret import load_world_secret_from_save, sync_public_world_secret_for_all

    save_data = context.save_data
    run_config_snapshot = save_data.get(
        "run_config",
        _model_to_dict(get_settings_service().get_default_run_config()),
    )
    context.run_config_snapshot = run_config_snapshot

    world_data = save_data.get("world", {})
    map_snapshot = world_data.get("map_snapshot")
    if map_snapshot:
        game_map = load_map_from_snapshot(map_snapshot)
    else:
        game_map = load_cultivation_world_map(run_config_snapshot.get("map_id", "classic"))
    context.game_map = game_map

    from src.classes.core.world import World

    world = World.create_with_db(
        map=game_map,
        month_stamp=MonthStamp(world_data["month_stamp"]),
        events_db_path=get_events_db_path(Path(context.save_path)),
        start_year=world_data.get("start_year", 100),
    )
    context.world = world

    CustomContentRegistry.load_from_dict(save_data.get("custom_content"))
    dynasty_data = world_data.get("dynasty")
    if dynasty_data is not None:
        world.dynasty = Dynasty.from_dict(dynasty_data)

    meta = save_data.get("meta", {})
    if "playthrough_id" in meta:
        world.playthrough_id = meta["playthrough_id"]

    world_lore_data = world_data.get("world_lore", {})
    world.world_lore.text = world_lore_data.get("text", "")
    world.world_lore_snapshot = world_data.get("world_lore_snapshot", {}) or {}
    apply_world_lore_snapshot(world, world.world_lore_snapshot)
    load_world_secret_from_save(world, world_data.get("world_secret"))

    from src.classes.celestial_phenomenon import celestial_phenomena_by_id

    phenomenon_id = world_data.get("current_phenomenon_id")
    if phenomenon_id is not None and phenomenon_id in celestial_phenomena_by_id:
        world.current_phenomenon = celestial_phenomena_by_id[phenomenon_id]
        world.phenomenon_start_year = world_data.get("phenomenon_start_year", 0)

    world.circulation.load_from_dict(world_data.get("circulation", {}))

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

    avatars_data = save_data.get("avatars", [])
    all_avatars = {}
    living_avatars = {}
    dead_avatars = {}
    for avatar_data in avatars_data:
        avatar = Avatar.from_save_dict(avatar_data, world)
        all_avatars[avatar.id] = avatar
        if avatar.is_dead:
            dead_avatars[avatar.id] = avatar
        else:
            living_avatars[avatar.id] = avatar
    context.all_avatars = all_avatars

    for avatar_data in avatars_data:
        avatar_id = avatar_data["id"]
        avatar = all_avatars[avatar_id]
        for other_id, relation_state_data in avatar_data.get("relations", {}).items():
            if other_id in all_avatars:
                avatar.relations[all_avatars[other_id]] = RelationState.from_save_dict(relation_state_data)
        for other_id, relation_state_data in avatar_data.get("archived_relations", {}).items():
            if other_id in all_avatars:
                avatar.archived_relations[all_avatars[other_id]] = RelationState.from_save_dict(relation_state_data)

    world.avatar_manager.avatars = living_avatars
    world.avatar_manager.dead_avatars = dead_avatars
    if getattr(world.world_secret, "public_revealed", False):
        sync_public_world_secret_for_all(world)

    from src.classes.environment.region import CityRegion, CultivateRegion

    for rid_str, avatar_id in world_data.get("cultivate_regions_hosts", {}).items():
        rid = int(rid_str)
        if rid in game_map.regions:
            region = game_map.regions[rid]
            if isinstance(region, CultivateRegion) and avatar_id in all_avatars:
                all_avatars[avatar_id].occupy_region(region)

    for rid_str, status in world_data.get("regions_status", {}).items():
        rid = int(rid_str)
        if rid in game_map.regions:
            region = game_map.regions[rid]
            if isinstance(region, CityRegion):
                region.population = status.get("population", region.population)

    region_formations = {}
    for rid_str, formation in (world_data.get("region_formations", {}) or {}).items():
        try:
            rid = int(rid_str)
        except (TypeError, ValueError):
            continue
        if rid not in game_map.regions or not isinstance(formation, dict):
            continue
        region_formations[rid] = dict(formation)
    game_map.region_formations = region_formations
    from src.systems.formation import cleanup_expired_region_formations

    cleanup_expired_region_formations(world, int(world.month_stamp))

    from src.classes.technique import techniques_by_name

    for avatar in all_avatars.values():
        if avatar.sect:
            avatar.sect.add_member(avatar)

    for sect in existed_sects:
        if not sect.techniques and sect.technique_names:
            sect.techniques = [
                techniques_by_name[t_name]
                for t_name in sect.technique_names
                if t_name in techniques_by_name
            ]

    world.existed_sects = existed_sects
    world.sect_context.from_existed_sects(existed_sects)

    db_event_count = world.event_manager.count()
    events_data = save_data.get("events", [])
    if db_event_count == 0 and len(events_data) > 0:
        print(f"Migrating {len(events_data)} events from JSON to SQLite...")
        for event_data in events_data:
            world.event_manager.add_event(Event.from_dict(event_data))
        print("Event migration completed")
    else:
        print(f"Loaded {db_event_count} events from SQLite")

    simulator_data = save_data.get("simulator", {})
    world.run_config_snapshot = run_config_snapshot
    simulator = Simulator(world)
    simulator.awakening_rate = simulator_data.get(
        "awakening_rate",
        simulator_data.get(
            "birth_rate",
            run_config_snapshot.get("npc_awakening_rate_per_month", 0.01),
        ),
    )
    context.simulator = simulator
    return world, simulator, existed_sects
