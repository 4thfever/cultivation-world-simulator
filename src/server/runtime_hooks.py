from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Callable


def create_runtime_hooks(
    *,
    game_state: dict[str, Any],
    runtime: Any,
    manager: Any,
    avatar_assets: dict[str, Any],
    assets_path: str,
    static_data: Any,
    config: Any,
    update_init_progress_impl: Callable[..., None],
    perform_game_initialization: Callable[..., Any],
    trigger_auto_save_impl: Callable[..., Any],
    run_game_loop_forever: Callable[..., Any],
    build_avatar_updates: Callable[..., Any],
    build_tick_state: Callable[..., Any],
    should_trigger_auto_save: Callable[..., bool],
    build_auto_save_toast: Callable[..., dict],
    reset_runtime_custom_content: Callable[[], None],
    reload_all_static_data: Callable[[], None],
    scan_avatar_assets: Callable[..., dict],
    load_cultivation_world_map: Callable[..., Any],
    get_events_db_path: Callable[..., Any],
    get_runtime_run_config: Callable[..., Any],
    world_cls: type,
    create_month_stamp: Callable[..., Any],
    year_cls: type,
    month_enum: Any,
    generate_dynasty: Callable[..., Any],
    generate_emperor: Callable[..., Any],
    event_cls: type,
    translate: Callable[..., str],
    simulator_cls: type,
    model_to_dict: Callable[[Any], dict],
    world_lore_manager_cls: type,
    build_world_lore_snapshot: Callable[..., Any],
    make_random_avatars: Callable[..., Any],
    check_llm_connectivity: Callable[..., Any],
    resolve_avatar_pic_id: Callable[..., Any],
    resolve_avatar_action_emoji: Callable[..., Any],
    serialize_events_for_client: Callable[..., Any],
    serialize_phenomenon: Callable[..., Any],
    serialize_active_domains: Callable[..., Any],
    get_logger: Callable[[], Any],
) -> SimpleNamespace:
    def update_init_progress(phase: int, phase_name: str = ""):
        update_init_progress_impl(runtime=runtime, phase=phase, phase_name=phase_name)

    async def init_game_async():
        await perform_game_initialization(
            runtime=runtime,
            avatar_assets=avatar_assets,
            assets_path=assets_path,
            config=config,
            update_init_progress=update_init_progress,
            reset_runtime_custom_content=reset_runtime_custom_content,
            reload_all_static_data=reload_all_static_data,
            scan_avatar_assets=scan_avatar_assets,
            load_cultivation_world_map=load_cultivation_world_map,
            get_events_db_path=get_events_db_path,
            get_runtime_run_config=get_runtime_run_config,
            world_cls=world_cls,
            create_month_stamp=create_month_stamp,
            year_cls=year_cls,
            month_enum=month_enum,
            generate_dynasty=generate_dynasty,
            generate_emperor=generate_emperor,
            event_cls=event_cls,
            translate=translate,
            simulator_cls=simulator_cls,
            model_to_dict=model_to_dict,
            world_lore_manager_cls=world_lore_manager_cls,
            build_world_lore_snapshot=build_world_lore_snapshot,
            sects_by_id=static_data.sects_by_id,
            make_random_avatars=make_random_avatars,
            check_llm_connectivity=check_llm_connectivity,
        )

    def trigger_auto_save(world, sim):
        trigger_auto_save_impl(world=world, sim=sim, sects_by_id=static_data.sects_by_id)

    async def game_loop():
        await run_game_loop_forever(
            game_instance=game_state,
            runtime=runtime,
            manager=manager,
            build_avatar_updates=lambda: build_avatar_updates(
                world=runtime.get("world"),
                resolve_avatar_pic_id=lambda avatar: resolve_avatar_pic_id(
                    avatar_assets=avatar_assets,
                    avatar=avatar,
                ),
                resolve_avatar_action_emoji=resolve_avatar_action_emoji,
            ),
            build_tick_state=lambda avatar_updates, events, world: build_tick_state(
                world=world,
                events=events,
                avatar_updates=avatar_updates,
                serialize_events_for_client=serialize_events_for_client,
                serialize_phenomenon=serialize_phenomenon,
                serialize_active_domains=serialize_active_domains,
            ),
            should_trigger_auto_save=lambda world: should_trigger_auto_save(world=world),
            trigger_auto_save=trigger_auto_save,
            build_auto_save_toast=build_auto_save_toast,
            get_logger=get_logger,
        )

    return SimpleNamespace(
        update_init_progress=update_init_progress,
        init_game_async=init_game_async,
        trigger_auto_save=trigger_auto_save,
        game_loop=game_loop,
    )
