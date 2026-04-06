from __future__ import annotations

from typing import Callable

from fastapi import APIRouter, Query

from src.server.services.public_api_contract import ok_response


def create_public_query_router(
    *,
    build_runtime_status: Callable[[], dict],
    build_world_state: Callable[[], dict],
    build_world_map: Callable[[], dict],
    build_current_run: Callable[[], dict],
    build_events_page: Callable[..., dict],
    build_rankings: Callable[[], dict],
    build_sect_relations: Callable[[], dict],
    build_game_data: Callable[[], dict],
    build_avatar_adjust_options: Callable[[], dict],
    build_avatar_meta: Callable[[], dict],
    build_avatar_list: Callable[[], dict],
    build_phenomena: Callable[[], dict],
    build_sect_territories: Callable[[], dict],
    build_mortal_overview: Callable[[], dict],
    build_dynasty_overview: Callable[[], dict],
    build_dynasty_detail: Callable[[], dict],
    build_saves: Callable[[], dict],
    build_detail: Callable[..., dict],
) -> APIRouter:
    router = APIRouter()

    @router.get("/api/v1/query/runtime/status")
    def get_runtime_status_v1():
        return ok_response(build_runtime_status())

    @router.get("/api/v1/query/world/state")
    def get_world_state_v1():
        return ok_response(build_world_state())

    @router.get("/api/v1/query/world/map")
    def get_world_map_v1():
        return ok_response(build_world_map())

    @router.get("/api/v1/query/system/current-run")
    def get_current_run_v1():
        return ok_response(build_current_run())

    @router.get("/api/v1/query/events")
    def get_events_v1(
        avatar_id: str = None,
        avatar_id_1: str = None,
        avatar_id_2: str = None,
        sect_id: int = None,
        major_scope: str = Query("all", pattern="^(all|major|minor)$"),
        cursor: str = None,
        limit: int = 100,
    ):
        return ok_response(
            build_events_page(
                avatar_id=avatar_id,
                avatar_id_1=avatar_id_1,
                avatar_id_2=avatar_id_2,
                sect_id=sect_id,
                major_scope=major_scope,
                cursor=cursor,
                limit=limit,
            )
        )

    @router.get("/api/v1/query/rankings")
    def get_rankings_v1():
        return ok_response(build_rankings())

    @router.get("/api/v1/query/sect-relations")
    def get_sect_relations_v1():
        return ok_response(build_sect_relations())

    @router.get("/api/v1/query/meta/game-data")
    def get_game_data_v1():
        return ok_response(build_game_data())

    @router.get("/api/v1/query/meta/avatar-adjust-options")
    def get_avatar_adjust_options_v1():
        return ok_response(build_avatar_adjust_options())

    @router.get("/api/v1/query/meta/avatars")
    def get_avatar_meta_v1():
        return ok_response(build_avatar_meta())

    @router.get("/api/v1/query/meta/avatar-list")
    def get_avatar_list_v1():
        return ok_response(build_avatar_list())

    @router.get("/api/v1/query/meta/phenomena")
    def get_phenomena_list_v1():
        return ok_response(build_phenomena())

    @router.get("/api/v1/query/sects/territories")
    def get_sect_territories_v1():
        return ok_response(build_sect_territories())

    @router.get("/api/v1/query/mortals/overview")
    def get_mortal_overview_v1():
        return ok_response(build_mortal_overview())

    @router.get("/api/v1/query/dynasty/overview")
    def get_dynasty_overview_v1():
        return ok_response(build_dynasty_overview())

    @router.get("/api/v1/query/dynasty/detail")
    def get_dynasty_detail_v1():
        return ok_response(build_dynasty_detail())

    @router.get("/api/v1/query/saves")
    def get_saves_v1():
        return ok_response(build_saves())

    @router.get("/api/v1/query/detail")
    def get_detail_info_v1(
        target_type: str = Query(alias="type"),
        target_id: str = Query(alias="id"),
    ):
        return ok_response(build_detail(target_type=target_type, target_id=target_id))

    return router
