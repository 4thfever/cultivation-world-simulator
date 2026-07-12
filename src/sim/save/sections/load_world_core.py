from __future__ import annotations

from pathlib import Path

from src.classes.custom_content import CustomContentRegistry

from .base import LoadContext


class WorldCoreLoadSection:
    key = "world_core"

    def load(self, context: LoadContext) -> None:
        from src.classes.core.dynasty import Dynasty
        from src.classes.core.world import World
        from src.classes.world_lore_snapshot import apply_world_lore_snapshot
        from src.run.load_map import load_cultivation_world_map
        from src.run.map_snapshot import load_map_from_snapshot
        from src.sim.load.load_game import get_events_db_path
        from src.systems.time import MonthStamp
        from src.systems.world_secret import load_world_secret_from_save

        world_data = context.world_data or {}
        run_config_snapshot = context.run_config_snapshot or {}
        map_snapshot = world_data.get("map_snapshot")
        if map_snapshot:
            game_map = load_map_from_snapshot(map_snapshot)
        else:
            game_map = load_cultivation_world_map(run_config_snapshot.get("map_id", "classic"))
        context.game_map = game_map

        world = World.create_with_db(
            map=game_map,
            month_stamp=MonthStamp(world_data["month_stamp"]),
            events_db_path=get_events_db_path(Path(context.save_path)),
            start_year=world_data.get("start_year", 100),
        )
        context.world = world

        CustomContentRegistry.load_from_dict(context.save_data.get("custom_content"))
        dynasty_data = world_data.get("dynasty")
        if dynasty_data is not None:
            world.dynasty = Dynasty.from_dict(dynasty_data)

        meta = context.save_data.get("meta", {})
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
