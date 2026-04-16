from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.server.mounts import mount_static_apps


def create_lifespan(
    *,
    endpoint_filter,
    get_settings_view,
    apply_runtime_content_locale,
    game_instance: dict,
    language_manager,
    game_loop,
    is_dev_mode: bool,
    project_root: str,
    start_frontend_dev_server,
    stop_frontend_dev_server,
):
    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        logging.getLogger("uvicorn.access").addFilter(endpoint_filter())

        settings = get_settings_view()
        apply_runtime_content_locale(settings.new_game_defaults.content_locale)
        print(f"Current Language: {language_manager}")
        print("Server started, waiting for start game command...")

        asyncio.create_task(game_loop())

        npm_process = None
        if is_dev_mode:
            print("🚀 Starting Development Mode (Dev Mode)...")
            try:
                npm_process = start_frontend_dev_server(project_root=project_root)
            except Exception as exc:
                print(f"Failed to start frontend server: {exc}")

        yield

        stop_frontend_dev_server(npm_process)

    return lifespan


def create_llm_updated_handler(*, game_instance: dict, manager):
    async def handle_llm_updated() -> None:
        if not game_instance.get("llm_check_failed", False):
            return

        print("Detected previous LLM connection failure, resuming Simulator...")
        game_instance["llm_check_failed"] = False
        game_instance["llm_error_message"] = ""
        game_instance["is_paused"] = False
        print("Simulator resumed")
        await manager.broadcast(
            {
                "type": "game_reinitialized",
                "message": "LLM 配置成功，游戏已恢复运行",
            }
        )

    return handle_llm_updated


def create_app(*, lifespan) -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app


def configure_routes_and_mounts(
    *,
    app,
    create_websocket_router,
    manager,
    game_instance: dict,
    create_settings_router,
    model_to_dict,
    get_settings_view,
    patch_settings,
    reset_settings,
    get_llm_view,
    get_llm_runtime_config,
    get_llm_test_payload,
    test_connectivity,
    update_llm,
    on_llm_updated,
    create_public_query_router,
    build_runtime_status,
    build_world_state,
    build_world_map,
    build_current_run,
    build_events_page,
    build_rankings,
    build_sect_relations,
    build_game_data,
    build_avatar_adjust_options,
    build_avatar_meta,
    build_avatar_list,
    build_phenomena,
    build_sect_territories,
    build_mortal_overview,
    build_dynasty_overview,
    build_dynasty_detail,
    build_avatar_overview,
    build_saves,
    build_detail,
    build_deceased_list,
    build_roleplay_session,
    create_public_command_router,
    run_start_game,
    run_reinit_game,
    run_reset_game,
    trigger_process_shutdown,
    run_pause_game,
    run_resume_game,
    run_set_long_term_objective,
    run_clear_long_term_objective,
    run_create_avatar,
    run_delete_avatar,
    run_update_avatar_adjustment,
    run_update_avatar_portrait,
    run_generate_custom_content,
    run_create_custom_content,
    run_set_phenomenon,
    run_cleanup_events,
    run_save_game,
    run_delete_save,
    run_load_game,
    run_start_roleplay,
    run_stop_roleplay,
    run_submit_roleplay_decision,
    run_submit_roleplay_choice,
    assets_path: str,
    web_dist_path: str,
    is_dev_mode: bool,
):
    app.include_router(create_websocket_router(manager=manager, game_instance=game_instance))

    app.include_router(
        create_settings_router(
            model_to_dict=model_to_dict,
            get_settings_view=get_settings_view,
            patch_settings=patch_settings,
            reset_settings=reset_settings,
            get_llm_view=get_llm_view,
            get_llm_runtime_config=get_llm_runtime_config,
            get_llm_test_payload=get_llm_test_payload,
            test_connectivity=test_connectivity,
            update_llm=update_llm,
            on_llm_updated=on_llm_updated,
        )
    )

    app.include_router(
        create_public_query_router(
            build_runtime_status=build_runtime_status,
            build_world_state=build_world_state,
            build_world_map=build_world_map,
            build_current_run=build_current_run,
            build_events_page=build_events_page,
            build_rankings=build_rankings,
            build_sect_relations=build_sect_relations,
            build_game_data=build_game_data,
            build_avatar_adjust_options=build_avatar_adjust_options,
            build_avatar_meta=build_avatar_meta,
            build_avatar_list=build_avatar_list,
            build_phenomena=build_phenomena,
            build_sect_territories=build_sect_territories,
            build_mortal_overview=build_mortal_overview,
            build_dynasty_overview=build_dynasty_overview,
            build_dynasty_detail=build_dynasty_detail,
            build_avatar_overview=build_avatar_overview,
            build_saves=build_saves,
            build_detail=build_detail,
            build_deceased_list=build_deceased_list,
            build_roleplay_session=build_roleplay_session,
        )
    )

    app.include_router(
        create_public_command_router(
            run_start_game=run_start_game,
            run_reinit_game=run_reinit_game,
            run_reset_game=run_reset_game,
            trigger_process_shutdown=trigger_process_shutdown,
            run_pause_game=run_pause_game,
            run_resume_game=run_resume_game,
            run_set_long_term_objective=run_set_long_term_objective,
            run_clear_long_term_objective=run_clear_long_term_objective,
            run_create_avatar=run_create_avatar,
            run_delete_avatar=run_delete_avatar,
            run_update_avatar_adjustment=run_update_avatar_adjustment,
            run_update_avatar_portrait=run_update_avatar_portrait,
            run_generate_custom_content=run_generate_custom_content,
            run_create_custom_content=run_create_custom_content,
            run_set_phenomenon=run_set_phenomenon,
            run_cleanup_events=run_cleanup_events,
            run_save_game=run_save_game,
            run_delete_save=run_delete_save,
            run_load_game=run_load_game,
            run_start_roleplay=run_start_roleplay,
            run_stop_roleplay=run_stop_roleplay,
            run_submit_roleplay_decision=run_submit_roleplay_decision,
            run_submit_roleplay_choice=run_submit_roleplay_choice,
        )
    )

    mount_static_apps(
        app,
        assets_path=assets_path,
        web_dist_path=web_dist_path,
        is_dev_mode=is_dev_mode,
    )


def start_server(*, patch_sys_streams, resolve_server_binding, prepare_browser_target, is_dev_mode: bool, app, uvicorn_module):
    patch_sys_streams()
    import webbrowser

    host, port = resolve_server_binding()
    target_url = prepare_browser_target(is_dev_mode=is_dev_mode, host=host, port=port)

    print(f"Opening browser at {target_url}...")
    try:
        webbrowser.open(target_url)
    except Exception as exc:
        print(f"Failed to open browser: {exc}")

    uvicorn_module.run(app, host=host, port=port, log_level="info")
