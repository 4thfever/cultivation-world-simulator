from __future__ import annotations

import asyncio
from typing import Any, Callable

from src.config import get_settings_service
from src.i18n import t

AVATAR_POSITION_UPDATE_LIMIT = 50


def build_avatar_updates(
    *,
    world,
    resolve_avatar_pic_id: Callable[[Any], int],
    resolve_avatar_action_emoji: Callable[[Any], str],
) -> list[dict[str, Any]]:
    """Build a compact avatar delta payload for websocket tick messages."""
    newly_born_ids = world.avatar_manager.pop_newly_born()
    newly_dead_ids = world.avatar_manager.pop_newly_dead()

    avatar_updates: list[dict[str, Any]] = []

    for avatar_id in newly_born_ids:
        avatar = world.avatar_manager.avatars.get(avatar_id)
        if avatar is None:
            continue
        avatar_updates.append(
            {
                "id": str(avatar.id),
                "name": avatar.name,
                "x": int(getattr(avatar, "pos_x", 0)),
                "y": int(getattr(avatar, "pos_y", 0)),
                "gender": avatar.gender.value,
                "pic_id": resolve_avatar_pic_id(avatar),
                "action": avatar.current_action_name,
                "action_emoji": resolve_avatar_action_emoji(avatar),
                "is_dead": False,
            }
        )

    for avatar_id in newly_dead_ids:
        avatar = world.avatar_manager.get_avatar(avatar_id)
        if avatar is None:
            continue
        avatar_updates.append(
            {
                "id": str(avatar.id),
                "name": avatar.name,
                "is_dead": True,
                "action": "已故",
            }
        )

    count = 0
    for avatar in world.avatar_manager.get_living_avatars():
        if avatar.id in newly_born_ids:
            continue
        if count >= AVATAR_POSITION_UPDATE_LIMIT:
            break
        avatar_updates.append(
            {
                "id": str(avatar.id),
                "x": int(getattr(avatar, "pos_x", 0)),
                "y": int(getattr(avatar, "pos_y", 0)),
                "action_emoji": resolve_avatar_action_emoji(avatar),
            }
        )
        count += 1

    return avatar_updates


def build_tick_state(
    *,
    world,
    events,
    avatar_updates: list[dict[str, Any]],
    serialize_events_for_client: Callable[[list[Any]], list[dict[str, Any]]],
    serialize_phenomenon: Callable[[Any], dict[str, Any] | None],
    serialize_active_domains: Callable[[Any], list[dict[str, Any]]],
) -> dict[str, Any]:
    """Build the websocket tick payload from current runtime state."""
    return {
        "type": "tick",
        "year": int(world.month_stamp.get_year()),
        "month": world.month_stamp.get_month().value,
        "events": serialize_events_for_client(events),
        "avatars": avatar_updates,
        "phenomenon": serialize_phenomenon(world.current_phenomenon),
        "active_domains": serialize_active_domains(world),
    }


def should_trigger_auto_save(*, world) -> tuple[bool, int, int]:
    """Return whether this tick should create an auto save."""
    auto_save_enabled = get_settings_service().get_settings().simulation.auto_save_enabled
    year = int(world.month_stamp.get_year())
    month = world.month_stamp.get_month().value
    should_save = auto_save_enabled and year % 10 == 0 and month == 1 and year > world.start_year
    return should_save, year, month


def build_auto_save_toast() -> dict[str, Any]:
    return {
        "type": "toast",
        "level": "info",
        "message": t("Game automatically saved"),
    }


async def run_game_loop_forever(
    *,
    game_instance: dict,
    runtime,
    manager,
    build_avatar_updates: Callable[[], list[dict[str, Any]]],
    build_tick_state: Callable[[list[dict[str, Any]], list[Any], Any], dict[str, Any]],
    should_trigger_auto_save: Callable[[Any], tuple[bool, int, int]],
    trigger_auto_save,
    build_auto_save_toast: Callable[[], dict[str, Any]],
    get_logger,
) -> None:
    """Run the background simulation loop forever once initialization succeeds."""
    print("Background game loop started, waiting for initialization...")

    while game_instance.get("init_status") not in ("ready", "error"):
        await asyncio.sleep(0.5)

    if game_instance.get("init_status") == "error":
        print("[game_loop] Initialization failed, game loop exiting.")
        return

    print("[game_loop] Initialization completed, starting game loop.")

    while True:
        await asyncio.sleep(1.0)

        try:
            if runtime.get("is_paused", False):
                continue
            if runtime.get("init_status") != "ready":
                continue

            sim = runtime.get("sim")
            world = runtime.get("world")
            if not sim or not world:
                continue

            events = await runtime.run_mutation(sim.step)
            avatar_updates = build_avatar_updates()
            state = build_tick_state(avatar_updates, events, world)
            await manager.broadcast(state)

            should_auto_save, year, _month = should_trigger_auto_save(world)
            if should_auto_save:
                print(f"[Auto-Save] Triggering auto save for year {year}...")
                await asyncio.to_thread(trigger_auto_save, world, sim)
                await manager.broadcast(build_auto_save_toast())
                print("[Auto-Save] Auto save completed.")
        except Exception as exc:
            print(f"Game loop error: {exc}")
            get_logger().logger.error(f"Game loop error: {exc}", exc_info=True)
