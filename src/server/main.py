import sys
import os

# ==============================================================================
# 修复 PyInstaller 打包并在非中文 Windows (如英语环境) 运行时 print 导致的崩溃问题。
# 系统默认可能回退至 cp1252 编码，此时如果 print 包含中文字符的路径就会抛出 UnicodeEncodeError。
# 我们在此强制将标准输出/错误流重置为 UTF-8，并将无法转换的字符替换掉，以防报错崩溃。
# ==============================================================================
for stream_name in ('stdout', 'stderr'):
    stream = getattr(sys, stream_name, None)
    if stream is not None:
        try:
            stream.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
# ==============================================================================

import asyncio
import uvicorn

# 确保可以导入 src 模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.sim.simulator import Simulator
from src.classes.core.world import World
from src.classes.world_lore import WorldLoreManager
from src.classes.world_lore_snapshot import build_world_lore_snapshot
from src.systems.time import Month, Year, create_month_stamp
from src.server.assemblers.sect_detail import build_sect_detail
from src.server.assemblers.mortal_overview import build_mortal_overview
from src.server.assemblers.dynasty_detail import build_dynasty_detail
from src.server.assemblers.dynasty_overview import build_dynasty_overview
from src.server.services.avatar_adjustment import apply_avatar_adjustment, build_avatar_adjust_options
from src.server.services.avatar_control import (
    clear_long_term_objective_for_avatar,
    create_avatar_in_world,
    delete_avatar_in_world,
    set_long_term_objective_for_avatar,
    update_avatar_adjustment_in_world,
    update_avatar_portrait_in_world,
)
from src.server.services.custom_content_control import (
    create_custom_content as create_custom_content_command,
    generate_custom_content as generate_custom_content_command,
)
from src.server.services.custom_content_service import (
    create_custom_content_from_draft,
    generate_custom_content_draft,
)
from src.server.services.custom_goldfinger_service import (
    create_custom_goldfinger_from_draft,
    generate_custom_goldfinger_draft,
)
from src.server.services.game_lifecycle import reinit_game_lifecycle, start_game_lifecycle
from src.server.services.game_queries import (
    get_detail as get_detail_query,
    get_deceased_list,
    get_events_page,
    get_game_data as get_game_data_query,
    get_rankings as get_rankings_query,
    get_runtime_status,
    get_avatar_assets_meta as get_avatar_assets_meta_query,
    get_sect_relations as get_sect_relations_query,
    get_sect_territories_summary as get_sect_territories_summary_query,
    get_avatar_list as get_avatar_list_query,
    get_phenomena_list as get_phenomena_list_query,
    get_mortal_overview as get_mortal_overview_query,
    get_dynasty_overview as get_dynasty_overview_query,
    get_dynasty_detail as get_dynasty_detail_query,
    get_avatar_overview as get_avatar_overview_query,
    get_world_map,
    get_world_state,
)
from src.server.services.roleplay_service import (
    end_roleplay_conversation as end_roleplay_conversation_service,
    clear_roleplay_session as clear_roleplay_session_service,
    get_roleplay_session as get_roleplay_session_query,
    start_roleplay as start_roleplay_service,
    stop_roleplay as stop_roleplay_service,
    submit_roleplay_conversation_turn as submit_roleplay_conversation_turn_service,
    submit_roleplay_choice as submit_roleplay_choice_service,
    submit_roleplay_decision as submit_roleplay_decision_service,
)
from src.server.services.event_control import cleanup_events as cleanup_events_command
from src.server.api.public_v1 import (
    create_public_command_router,
    create_public_query_router,
)
from src.server.api.public_v1.command import GameStartRequest, LoadGameRequest
from src.server.api.settings import create_settings_router
from src.server.api.websocket import create_websocket_router
from src.server.services.save_load_control import (
    delete_save_file,
    list_saves_query,
    load_game_into_runtime,
    save_current_game,
)
from src.server.services.world_control import set_world_phenomenon
from src.run.load_map import load_cultivation_world_map
from src.sim.avatar_init import make_avatars as _new_make_random, create_avatar_from_request
from src.systems.dynasty_generator import generate_dynasty, generate_emperor
from src.utils.config import CONFIG
from src.classes.core.sect import sects_by_id
from src.classes.technique import techniques_by_id
from src.classes.goldfinger import goldfingers_by_id
from src.classes.items.weapon import weapons_by_id
from src.classes.items.auxiliary import auxiliaries_by_id
from src.classes.appearance import get_appearance_by_level
from src.classes.persona import personas_by_id
from src.systems.cultivation import REALM_ORDER, Realm
from src.classes.alignment import Alignment
from src.classes.event import Event
from src.classes.celestial_phenomenon import celestial_phenomena_by_id
from src.classes.long_term_objective import set_user_long_term_objective, clear_user_long_term_objective
from src.sim import save_game, list_saves, load_game, get_events_db_path
from src.utils.llm.client import test_connectivity as _test_connectivity
from src.run.data_loader import reload_all_static_data
from src.classes.language import language_manager
from src.systems.sect_relations import compute_sect_relations
from src.i18n import t
from src.config import get_settings_service
from src.i18n.locale_registry import uses_space_separated_names
from src.utils.llm.config import LLMConfig
from src.server.runtime import DEFAULT_GAME_STATE, GameSessionRuntime
from src.server.host_runtime import (
    ConnectionManager,
    EndpointFilter,
    patch_sys_streams,
    trigger_process_shutdown,
)
from src.server.auto_save import trigger_auto_save as _trigger_auto_save
from src.server.bootstrap import prepare_browser_target, resolve_runtime_paths, resolve_server_binding
from src.server.command_handlers import create_command_handlers
from src.server.dev_runtime import start_frontend_dev_server, stop_frontend_dev_server
from src.server.host_app import (
    configure_routes_and_mounts,
    create_app,
    create_lifespan,
    create_llm_updated_handler,
    start_server,
)
from src.server.init_flow import perform_game_initialization
from src.server.init_runtime import (
    INIT_PHASE_NAMES,
    check_llm_connectivity,
    update_init_progress as _update_init_progress,
)
from src.server.loop_runtime import (
    build_auto_save_toast,
    build_avatar_updates,
    build_tick_state,
    run_game_loop_forever,
    should_trigger_auto_save,
)
from src.server.public_query_builders import create_public_query_builders
from src.server.public_helpers import (
    apply_runtime_content_locale as _apply_runtime_content_locale,
    get_runtime_run_config as _get_runtime_run_config,
    model_to_dict as _model_to_dict,
    reset_runtime_custom_content,
    resolve_avatar_action_emoji,
    resolve_avatar_pic_id,
    scan_avatar_assets,
    validate_save_name,
)
from src.server.serialization import (
    serialize_active_domains,
    serialize_events_for_client,
    serialize_phenomenon,
)

# 全局游戏实例
game_instance = dict(DEFAULT_GAME_STATE)
runtime = GameSessionRuntime(game_instance)

# Cache for avatar IDs
AVATAR_ASSETS = {
    "males": [],
    "females": []
}
# 触发配置重载的标记 (technique.csv updated)

# 简易的命令行参数检查 (不使用 argparse 以避免冲突和时序问题)
IS_DEV_MODE = "--dev" in sys.argv


def apply_runtime_content_locale(lang_code: str) -> None:
    """兼容保留：按当前主运行时切换内容语言。"""
    _apply_runtime_content_locale(
        game_instance=game_instance,
        language_manager=language_manager,
        lang_code=lang_code,
    )


def get_current_config():
    """返回当前配置模块中的最新 CONFIG，避免 reload 后持有陈旧引用。"""
    from src.utils.config import CONFIG as current_config

    return current_config


def get_fallback_saves_dirs():
    """收集可能有效的存档目录，兼容 main.CONFIG 与 reload 后的新 CONFIG。"""
    candidates = []
    seen = set()

    for config_obj in (get_current_config(), CONFIG):
        saves_dir = getattr(getattr(config_obj, "paths", None), "saves", None)
        if saves_dir is None:
            continue
        key = str(saves_dir)
        if key in seen:
            continue
        seen.add(key)
        candidates.append(saves_dir)

    return candidates


def is_idle_shutdown_enabled() -> bool:
    """Return whether the server should exit after the last client disconnects."""
    if IS_DEV_MODE:
        return False

    raw = os.environ.get("CWS_DISABLE_AUTO_SHUTDOWN", "")
    return raw.strip().lower() not in {"1", "true", "yes", "on"}

manager = ConnectionManager(runtime=runtime, is_idle_shutdown_enabled=is_idle_shutdown_enabled)

public_query_builders = create_public_query_builders(
    runtime=runtime,
    avatar_assets=AVATAR_ASSETS,
    config=CONFIG,
    model_to_dict=_model_to_dict,
    get_runtime_run_config=_get_runtime_run_config,
    resolve_avatar_action_emoji=resolve_avatar_action_emoji,
    resolve_avatar_pic_id=resolve_avatar_pic_id,
    serialize_events_for_client=serialize_events_for_client,
    serialize_active_domains=serialize_active_domains,
    serialize_phenomenon=serialize_phenomenon,
    get_world_state=get_world_state,
    get_world_map=get_world_map,
    sects_by_id=sects_by_id,
    get_runtime_status=get_runtime_status,
    get_events_page=get_events_page,
    get_game_data_query=get_game_data_query,
    personas_by_id=personas_by_id,
    realm_order=REALM_ORDER,
    techniques_by_id=techniques_by_id,
    weapons_by_id=weapons_by_id,
    auxiliaries_by_id=auxiliaries_by_id,
    alignment_enum=Alignment,
    get_detail_query=get_detail_query,
    build_sect_detail=build_sect_detail,
    language_manager=language_manager,
    build_avatar_adjust_options=build_avatar_adjust_options,
    get_avatar_assets_meta_query=get_avatar_assets_meta_query,
    get_avatar_list_query=get_avatar_list_query,
    get_phenomena_list_query=get_phenomena_list_query,
    celestial_phenomena_by_id=celestial_phenomena_by_id,
    get_sect_territories_summary_query=get_sect_territories_summary_query,
    list_saves_query=list_saves_query,
    get_list_saves=lambda: (
        lambda: next(
            (
                saves
                for saves in (
                    list_saves(saves_dir=saves_dir)
                    for saves_dir in get_fallback_saves_dirs()
                )
                if saves
            ),
            [],
        )
    ),
    get_rankings_query=get_rankings_query,
    get_sect_relations_query=get_sect_relations_query,
    compute_sect_relations=compute_sect_relations,
    get_mortal_overview_query=get_mortal_overview_query,
    build_mortal_overview=build_mortal_overview,
    get_dynasty_overview_query=get_dynasty_overview_query,
    build_dynasty_overview=build_dynasty_overview,
    get_dynasty_detail_query=get_dynasty_detail_query,
    build_dynasty_detail=build_dynasty_detail,
    get_avatar_overview_query=get_avatar_overview_query,
    get_deceased_list_query=get_deceased_list,
    get_roleplay_session_query=get_roleplay_session_query,
)

build_public_world_state = public_query_builders.build_public_world_state
build_public_world_map = public_query_builders.build_public_world_map
build_public_runtime_status = public_query_builders.build_public_runtime_status
build_public_current_run = public_query_builders.build_public_current_run
build_public_events_page = public_query_builders.build_public_events_page
build_public_game_data = public_query_builders.build_public_game_data
build_public_detail = public_query_builders.build_public_detail
build_public_avatar_adjust_options = public_query_builders.build_public_avatar_adjust_options
build_public_avatar_meta = public_query_builders.build_public_avatar_meta
build_public_avatar_list = public_query_builders.build_public_avatar_list
build_public_phenomena = public_query_builders.build_public_phenomena
build_public_sect_territories = public_query_builders.build_public_sect_territories
build_public_saves = public_query_builders.build_public_saves
build_public_rankings = public_query_builders.build_public_rankings
build_public_sect_relations = public_query_builders.build_public_sect_relations
build_public_mortal_overview = public_query_builders.build_public_mortal_overview
build_public_dynasty_overview = public_query_builders.build_public_dynasty_overview
build_public_dynasty_detail = public_query_builders.build_public_dynasty_detail
build_public_avatar_overview = public_query_builders.build_public_avatar_overview
build_public_deceased_list = public_query_builders.build_public_deceased_list
build_public_roleplay_session = public_query_builders.build_public_roleplay_session


def update_init_progress(phase: int, phase_name: str = ""):
    """兼容保留：更新初始化进度。"""
    _update_init_progress(runtime=runtime, phase=phase, phase_name=phase_name)

async def init_game_async():
    """异步初始化游戏世界，带进度更新。"""
    await perform_game_initialization(
        runtime=runtime,
        avatar_assets=AVATAR_ASSETS,
        assets_path=ASSETS_PATH,
        config=CONFIG,
        update_init_progress=update_init_progress,
        reset_runtime_custom_content=reset_runtime_custom_content,
        reload_all_static_data=reload_all_static_data,
        scan_avatar_assets=scan_avatar_assets,
        load_cultivation_world_map=load_cultivation_world_map,
        get_events_db_path=get_events_db_path,
        get_runtime_run_config=_get_runtime_run_config,
        world_cls=World,
        create_month_stamp=create_month_stamp,
        year_cls=Year,
        month_enum=Month,
        generate_dynasty=generate_dynasty,
        generate_emperor=generate_emperor,
        event_cls=Event,
        translate=t,
        simulator_cls=Simulator,
        model_to_dict=_model_to_dict,
        world_lore_manager_cls=WorldLoreManager,
        build_world_lore_snapshot=build_world_lore_snapshot,
        sects_by_id=sects_by_id,
        make_random_avatars=_new_make_random,
        check_llm_connectivity=check_llm_connectivity,
    )



def trigger_auto_save(world, sim):
    """兼容保留：触发当前对局自动存档。"""
    _trigger_auto_save(world=world, sim=sim, sects_by_id=sects_by_id)

async def game_loop():
    """后台自动运行游戏循环。"""
    from src.run.log import get_logger

    await run_game_loop_forever(
        game_instance=game_instance,
        runtime=runtime,
        manager=manager,
        build_avatar_updates=lambda: build_avatar_updates(
            world=runtime.get("world"),
            resolve_avatar_pic_id=lambda avatar: resolve_avatar_pic_id(
                avatar_assets=AVATAR_ASSETS,
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

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

lifespan = create_lifespan(
    endpoint_filter=EndpointFilter,
    get_settings_view=get_settings_service().get_settings_view,
    apply_runtime_content_locale=apply_runtime_content_locale,
    game_instance=game_instance,
    language_manager=language_manager,
    game_loop=game_loop,
    is_dev_mode=IS_DEV_MODE,
    project_root=PROJECT_ROOT,
    start_frontend_dev_server=start_frontend_dev_server,
    stop_frontend_dev_server=stop_frontend_dev_server,
)

app = create_app(lifespan=lifespan)

WEB_DIST_PATH, ASSETS_PATH = resolve_runtime_paths(
    server_file=__file__,
    is_frozen=getattr(sys, "frozen", False),
    executable=getattr(sys, "executable", None),
    meipass=getattr(sys, "_MEIPASS", None),
)

print(f"Runtime mode: {'Frozen/Packaged' if getattr(sys, 'frozen', False) else 'Development'}")
print(f"Assets path: {ASSETS_PATH}")
print(f"Web dist path: {WEB_DIST_PATH}")

command_handlers = create_command_handlers(
    runtime=runtime,
    manager=manager,
    avatar_assets=AVATAR_ASSETS,
    assets_path=ASSETS_PATH,
    model_to_dict=_model_to_dict,
    validate_save_name=validate_save_name,
    get_init_game_async=lambda: init_game_async,
    get_apply_runtime_content_locale=lambda: apply_runtime_content_locale,
    scan_avatar_assets=scan_avatar_assets,
    start_game_lifecycle=start_game_lifecycle,
    reinit_game_lifecycle=reinit_game_lifecycle,
    cleanup_events_command=cleanup_events_command,
    set_world_phenomenon=set_world_phenomenon,
    celestial_phenomena_by_id=celestial_phenomena_by_id,
    create_avatar_in_world=create_avatar_in_world,
    create_avatar_from_request=create_avatar_from_request,
    sects_by_id=sects_by_id,
    uses_space_separated_names=uses_space_separated_names,
    language_manager=language_manager,
    alignment_from_str=Alignment.from_str,
    get_appearance_by_level=get_appearance_by_level,
    delete_avatar_in_world=delete_avatar_in_world,
    update_avatar_adjustment_in_world=update_avatar_adjustment_in_world,
    apply_avatar_adjustment=apply_avatar_adjustment,
    update_avatar_portrait_in_world=update_avatar_portrait_in_world,
    generate_custom_content_command=generate_custom_content_command,
    get_generate_custom_goldfinger_draft=lambda: generate_custom_goldfinger_draft,
    get_generate_custom_content_draft=lambda: generate_custom_content_draft,
    realm_from_str=Realm.from_str,
    create_custom_content_command=create_custom_content_command,
    create_custom_goldfinger_from_draft=create_custom_goldfinger_from_draft,
    create_custom_content_from_draft=create_custom_content_from_draft,
    set_long_term_objective_for_avatar=set_long_term_objective_for_avatar,
    clear_long_term_objective_for_avatar=clear_long_term_objective_for_avatar,
    set_user_long_term_objective=set_user_long_term_objective,
    clear_user_long_term_objective=clear_user_long_term_objective,
    save_current_game=save_current_game,
    save_game=save_game,
    delete_save_file=delete_save_file,
    get_config=get_current_config,
    get_fallback_saves_dirs=get_fallback_saves_dirs,
    get_load_game_into_runtime=lambda: load_game_into_runtime,
    get_load_game=lambda: load_game,
    get_events_db_path=get_events_db_path,
    get_roleplay_session=get_roleplay_session_query,
    clear_roleplay_session=clear_roleplay_session_service,
    start_roleplay=start_roleplay_service,
    stop_roleplay=stop_roleplay_service,
    submit_roleplay_decision=submit_roleplay_decision_service,
    submit_roleplay_choice=submit_roleplay_choice_service,
    submit_roleplay_conversation_turn=submit_roleplay_conversation_turn_service,
    end_roleplay_conversation=end_roleplay_conversation_service,
)

run_start_game = command_handlers.run_start_game
run_reinit_game = command_handlers.run_reinit_game
run_reset_game = command_handlers.run_reset_game
run_pause_game = command_handlers.run_pause_game
run_resume_game = command_handlers.run_resume_game
run_cleanup_events = command_handlers.run_cleanup_events
run_set_phenomenon = command_handlers.run_set_phenomenon
run_create_avatar = command_handlers.run_create_avatar
run_delete_avatar = command_handlers.run_delete_avatar
run_update_avatar_adjustment = command_handlers.run_update_avatar_adjustment
run_update_avatar_portrait = command_handlers.run_update_avatar_portrait
run_generate_custom_content = command_handlers.run_generate_custom_content
run_create_custom_content = command_handlers.run_create_custom_content
run_set_long_term_objective = command_handlers.run_set_long_term_objective
run_clear_long_term_objective = command_handlers.run_clear_long_term_objective
run_save_game = command_handlers.run_save_game
run_delete_save = command_handlers.run_delete_save
run_load_game = command_handlers.run_load_game
run_start_roleplay = command_handlers.run_start_roleplay
run_stop_roleplay = command_handlers.run_stop_roleplay
run_submit_roleplay_decision = command_handlers.run_submit_roleplay_decision
run_submit_roleplay_choice = command_handlers.run_submit_roleplay_choice
run_send_roleplay_conversation = command_handlers.run_send_roleplay_conversation
run_end_roleplay_conversation = command_handlers.run_end_roleplay_conversation


def get_settings() -> dict:
    """兼容保留：返回当前应用设置视图。"""
    return _model_to_dict(get_settings_service().get_settings_view())


def _patch_settings_model(req):
    updated = get_settings_service().patch_settings(req)
    next_locale = str(updated.new_game_defaults.content_locale)
    current_locale = str(language_manager)

    if next_locale and next_locale != current_locale:
        apply_runtime_content_locale(next_locale)

    run_config = game_instance.get("run_config")
    if isinstance(run_config, dict):
        run_config["content_locale"] = next_locale

    return updated


def patch_settings(req) -> dict:
    """兼容保留：更新应用设置。"""
    return _model_to_dict(_patch_settings_model(req))


def _reset_settings_model():
    updated = get_settings_service().reset_settings()
    next_locale = str(updated.new_game_defaults.content_locale)
    current_locale = str(language_manager)

    if next_locale and next_locale != current_locale:
        apply_runtime_content_locale(next_locale)

    run_config = game_instance.get("run_config")
    if isinstance(run_config, dict):
        run_config["content_locale"] = next_locale

    return updated


def reset_settings() -> dict:
    """兼容保留：重置应用设置，并同步全局语言。"""
    return _model_to_dict(_reset_settings_model())


async def start_game(req: GameStartRequest) -> dict:
    """兼容保留：启动游戏初始化流程。"""
    return await run_start_game(req)


async def api_load_game(req: LoadGameRequest) -> dict:
    """兼容保留：加载指定存档。"""
    return await run_load_game(filename=req.filename)


def get_runtime_run_config() -> object:
    """兼容保留：获取当前运行配置。"""
    return _get_runtime_run_config(runtime)


def test_connectivity(config):
    """兼容保留：转发到底层 LLM 连通性测试。"""
    return _test_connectivity(config=config)


def test_llm_connection(req) -> dict:
    """兼容保留：使用当前保存的密钥测试 LLM 配置。"""
    profile, api_key = get_settings_service().get_llm_test_payload(req)
    success, error_msg = test_connectivity(
        config=LLMConfig(
            base_url=profile.base_url,
            api_key=api_key,
            model_name=profile.model_name,
            api_format=profile.api_format,
        )
    )
    if success:
        return {"status": "ok", "message": "连接成功"}
    return {"status": "error", "message": error_msg}

handle_llm_updated = create_llm_updated_handler(game_instance=game_instance, manager=manager)

configure_routes_and_mounts(
    app=app,
    create_websocket_router=create_websocket_router,
    manager=manager,
    game_instance=game_instance,
    create_settings_router=create_settings_router,
    model_to_dict=_model_to_dict,
    get_settings_view=get_settings_service().get_settings_view,
    patch_settings=_patch_settings_model,
    reset_settings=_reset_settings_model,
    get_llm_view=get_settings_service().get_llm_view,
    get_llm_runtime_config=get_settings_service().get_llm_runtime_config,
    get_llm_test_payload=get_settings_service().get_llm_test_payload,
    test_connectivity=test_connectivity,
    update_llm=get_settings_service().update_llm,
    on_llm_updated=handle_llm_updated,
    create_public_query_router=create_public_query_router,
    build_runtime_status=build_public_runtime_status,
    build_world_state=build_public_world_state,
    build_world_map=build_public_world_map,
    build_current_run=build_public_current_run,
    build_events_page=build_public_events_page,
    build_rankings=build_public_rankings,
    build_sect_relations=build_public_sect_relations,
    build_game_data=build_public_game_data,
    build_avatar_adjust_options=build_public_avatar_adjust_options,
    build_avatar_meta=build_public_avatar_meta,
    build_avatar_list=build_public_avatar_list,
    build_phenomena=build_public_phenomena,
    build_sect_territories=build_public_sect_territories,
    build_mortal_overview=build_public_mortal_overview,
    build_dynasty_overview=build_public_dynasty_overview,
    build_dynasty_detail=build_public_dynasty_detail,
    build_avatar_overview=build_public_avatar_overview,
    build_saves=build_public_saves,
    build_detail=build_public_detail,
    build_deceased_list=build_public_deceased_list,
    build_roleplay_session=build_public_roleplay_session,
    create_public_command_router=create_public_command_router,
    run_start_game=run_start_game,
    run_reinit_game=run_reinit_game,
    run_reset_game=run_reset_game,
    trigger_process_shutdown=lambda: trigger_process_shutdown(is_dev_mode=IS_DEV_MODE),
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
    run_send_roleplay_conversation=run_send_roleplay_conversation,
    run_end_roleplay_conversation=run_end_roleplay_conversation,
    assets_path=ASSETS_PATH,
    web_dist_path=WEB_DIST_PATH,
    is_dev_mode=IS_DEV_MODE,
)

def start():
    """启动服务的入口函数"""
    start_server(
        patch_sys_streams=patch_sys_streams,
        resolve_server_binding=resolve_server_binding,
        prepare_browser_target=prepare_browser_target,
        is_dev_mode=IS_DEV_MODE,
        app=app,
        uvicorn_module=uvicorn,
    )

if __name__ == "__main__":
    start()
