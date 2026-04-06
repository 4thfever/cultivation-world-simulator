from __future__ import annotations

from types import SimpleNamespace

from src.config import RunConfig, get_settings_service
from src.i18n import t


def create_command_handlers(
    *,
    runtime,
    manager,
    avatar_assets,
    assets_path: str,
    model_to_dict,
    validate_save_name,
    get_init_game_async,
    get_apply_runtime_content_locale,
    scan_avatar_assets,
    start_game_lifecycle,
    reinit_game_lifecycle,
    cleanup_events_command,
    set_world_phenomenon,
    celestial_phenomena_by_id,
    create_avatar_in_world,
    create_avatar_from_request,
    sects_by_id,
    uses_space_separated_names,
    language_manager,
    alignment_from_str,
    get_appearance_by_level,
    delete_avatar_in_world,
    update_avatar_adjustment_in_world,
    apply_avatar_adjustment,
    update_avatar_portrait_in_world,
    generate_custom_content_command,
    get_generate_custom_goldfinger_draft,
    get_generate_custom_content_draft,
    realm_from_str,
    create_custom_content_command,
    create_custom_goldfinger_from_draft,
    create_custom_content_from_draft,
    set_long_term_objective_for_avatar,
    clear_long_term_objective_for_avatar,
    set_user_long_term_objective,
    clear_user_long_term_objective,
    save_current_game,
    save_game,
    delete_save_file,
    get_config,
    get_fallback_saves_dirs,
    get_load_game_into_runtime,
    get_load_game,
    get_events_db_path,
):
    async def run_start_game(req) -> dict:
        run_config = RunConfig(**model_to_dict(req))
        return await start_game_lifecycle(
            runtime,
            run_config=run_config,
            apply_runtime_content_locale=get_apply_runtime_content_locale(),
            init_game_async=get_init_game_async(),
        )

    async def run_reinit_game() -> dict:
        return await reinit_game_lifecycle(runtime, init_game_async=get_init_game_async())

    async def run_reset_game() -> dict:
        await runtime.run_mutation(runtime.reset_to_idle)
        return {"status": "ok", "message": "Game reset to idle"}

    async def run_pause_game() -> dict:
        await runtime.run_mutation(runtime.set_paused, True)
        return {"status": "ok", "message": "Game paused"}

    async def run_resume_game() -> dict:
        await runtime.run_mutation(runtime.set_paused, False)
        return {"status": "ok", "message": "Game resumed"}

    async def run_cleanup_events(*, keep_major: bool, before_month_stamp: int | None) -> dict:
        return await runtime.run_mutation(
            cleanup_events_command,
            runtime,
            keep_major=keep_major,
            before_month_stamp=before_month_stamp,
        )

    async def run_set_phenomenon(*, phenomenon_id: int) -> dict:
        return await runtime.run_mutation(
            set_world_phenomenon,
            runtime,
            phenomenon_id=phenomenon_id,
            celestial_phenomena_by_id=celestial_phenomena_by_id,
        )

    async def run_create_avatar(req) -> dict:
        return await runtime.run_mutation(
            create_avatar_in_world,
            runtime,
            req=req,
            create_avatar_from_request=create_avatar_from_request,
            sects_by_id=sects_by_id,
            uses_space_separated_names=uses_space_separated_names,
            language_manager=language_manager,
            avatar_assets=avatar_assets,
            alignment_from_str=alignment_from_str,
            get_appearance_by_level=get_appearance_by_level,
        )

    async def run_delete_avatar(*, avatar_id: str) -> dict:
        return await runtime.run_mutation(
            delete_avatar_in_world,
            runtime,
            avatar_id=avatar_id,
        )

    async def run_update_avatar_adjustment(req) -> dict:
        return await runtime.run_mutation(
            update_avatar_adjustment_in_world,
            runtime,
            avatar_id=req.avatar_id,
            category=req.category,
            target_id=req.target_id,
            persona_ids=req.persona_ids,
            apply_avatar_adjustment=apply_avatar_adjustment,
        )

    async def run_update_avatar_portrait(*, avatar_id: str, pic_id: int) -> dict:
        return await runtime.run_mutation(
            update_avatar_portrait_in_world,
            runtime,
            avatar_id=avatar_id,
            pic_id=pic_id,
            avatar_assets=avatar_assets,
        )

    async def run_generate_custom_content(req) -> dict:
        return await generate_custom_content_command(
            category=req.category,
            realm=req.realm,
            user_prompt=req.user_prompt,
            generate_custom_goldfinger_draft=get_generate_custom_goldfinger_draft(),
            generate_custom_content_draft=get_generate_custom_content_draft(),
            realm_from_str=realm_from_str,
        )

    def run_create_custom_content(req) -> dict:
        return create_custom_content_command(
            category=req.category,
            draft=req.draft,
            create_custom_goldfinger_from_draft=create_custom_goldfinger_from_draft,
            create_custom_content_from_draft=create_custom_content_from_draft,
        )

    async def run_set_long_term_objective(req) -> dict:
        return await runtime.run_mutation(
            set_long_term_objective_for_avatar,
            runtime,
            avatar_id=req.avatar_id,
            content=req.content,
            setter=set_user_long_term_objective,
        )

    async def run_clear_long_term_objective(req) -> dict:
        return await runtime.run_mutation(
            clear_long_term_objective_for_avatar,
            runtime,
            avatar_id=req.avatar_id,
            clearer=clear_user_long_term_objective,
        )

    def run_save_game(*, custom_name: str | None) -> dict:
        return save_current_game(
            runtime,
            custom_name=custom_name,
            validate_save_name=validate_save_name,
            save_game=save_game,
            sects_by_id=sects_by_id,
        )

    def run_delete_save(*, filename: str) -> dict:
        return delete_save_file(
            filename=filename,
            saves_dir=get_config().paths.saves,
            fallback_saves_dirs=get_fallback_saves_dirs(),
            get_events_db_path=get_events_db_path,
        )

    async def run_load_game(*, filename: str) -> dict:
        from src.sim import get_save_info

        return await get_load_game_into_runtime()(
            runtime,
            filename=filename,
            saves_dir=get_config().paths.saves,
            fallback_saves_dirs=get_fallback_saves_dirs(),
            get_save_info=get_save_info,
            language_manager=language_manager,
            manager=manager,
            t=t,
            apply_runtime_content_locale=get_apply_runtime_content_locale(),
            scan_avatar_assets=lambda: avatar_assets.update(scan_avatar_assets(assets_path=assets_path)),
            load_game=get_load_game(),
            get_settings_service=get_settings_service,
            _model_to_dict=model_to_dict,
        )

    return SimpleNamespace(
        run_start_game=run_start_game,
        run_reinit_game=run_reinit_game,
        run_reset_game=run_reset_game,
        run_pause_game=run_pause_game,
        run_resume_game=run_resume_game,
        run_cleanup_events=run_cleanup_events,
        run_set_phenomenon=run_set_phenomenon,
        run_create_avatar=run_create_avatar,
        run_delete_avatar=run_delete_avatar,
        run_update_avatar_adjustment=run_update_avatar_adjustment,
        run_update_avatar_portrait=run_update_avatar_portrait,
        run_generate_custom_content=run_generate_custom_content,
        run_create_custom_content=run_create_custom_content,
        run_set_long_term_objective=run_set_long_term_objective,
        run_clear_long_term_objective=run_clear_long_term_objective,
        run_save_game=run_save_game,
        run_delete_save=run_delete_save,
        run_load_game=run_load_game,
    )
