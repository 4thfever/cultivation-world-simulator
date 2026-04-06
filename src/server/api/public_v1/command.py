from __future__ import annotations

from typing import Callable, Literal, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from src.config import RunConfig
from src.server.services.public_api_contract import ok_response


class GameStartRequest(RunConfig):
    pass


class SetObjectiveRequest(BaseModel):
    avatar_id: str
    content: str


class ClearObjectiveRequest(BaseModel):
    avatar_id: str


class CreateAvatarRequest(BaseModel):
    surname: Optional[str] = None
    given_name: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    level: Optional[int] = None
    sect_id: Optional[int] = None
    persona_ids: Optional[list[int]] = None
    pic_id: Optional[int] = None
    technique_id: Optional[int] = None
    weapon_id: Optional[int] = None
    auxiliary_id: Optional[int] = None
    alignment: Optional[str] = None
    appearance: Optional[int] = None
    relations: Optional[list[dict]] = None


class DeleteAvatarRequest(BaseModel):
    avatar_id: str


class UpdateAvatarAdjustmentRequest(BaseModel):
    avatar_id: str
    category: Literal["technique", "weapon", "auxiliary", "personas", "goldfinger"]
    target_id: Optional[int] = None
    persona_ids: Optional[list[int]] = None


class UpdateAvatarPortraitRequest(BaseModel):
    avatar_id: str
    pic_id: int


class GenerateCustomContentRequest(BaseModel):
    category: Literal["technique", "weapon", "auxiliary", "goldfinger"]
    realm: Optional[str] = None
    user_prompt: str


class CreateCustomContentRequest(BaseModel):
    category: Literal["technique", "weapon", "auxiliary", "goldfinger"]
    draft: dict


class SetPhenomenonRequest(BaseModel):
    id: int


class SaveGameRequest(BaseModel):
    custom_name: Optional[str] = None


class DeleteSaveRequest(BaseModel):
    filename: str


class LoadGameRequest(BaseModel):
    filename: str


def create_public_command_router(
    *,
    run_start_game: Callable[[BaseModel], object],
    run_reinit_game: Callable[[], object],
    run_reset_game: Callable[[], object],
    trigger_process_shutdown: Callable[[], dict],
    run_pause_game: Callable[[], object],
    run_resume_game: Callable[[], object],
    run_set_long_term_objective: Callable[[BaseModel], object],
    run_clear_long_term_objective: Callable[[BaseModel], object],
    run_create_avatar: Callable[[BaseModel], object],
    run_delete_avatar: Callable[..., object],
    run_update_avatar_adjustment: Callable[[BaseModel], object],
    run_update_avatar_portrait: Callable[..., object],
    run_generate_custom_content: Callable[[BaseModel], object],
    run_create_custom_content: Callable[[BaseModel], object],
    run_set_phenomenon: Callable[..., object],
    run_cleanup_events: Callable[..., object],
    run_save_game: Callable[..., dict],
    run_delete_save: Callable[..., dict],
    run_load_game: Callable[..., object],
) -> APIRouter:
    router = APIRouter()

    @router.post("/api/v1/command/game/start")
    async def start_game_v1(req: GameStartRequest):
        return ok_response(await run_start_game(req))

    @router.post("/api/v1/command/game/reinit")
    async def reinit_game_v1():
        return ok_response(await run_reinit_game())

    @router.post("/api/v1/command/game/reset")
    async def reset_game_v1():
        return ok_response(await run_reset_game())

    @router.post("/api/v1/command/system/shutdown")
    async def shutdown_server_v1():
        return ok_response(trigger_process_shutdown())

    @router.post("/api/v1/command/game/pause")
    async def pause_game_v1():
        return ok_response(await run_pause_game())

    @router.post("/api/v1/command/game/resume")
    async def resume_game_v1():
        return ok_response(await run_resume_game())

    @router.post("/api/v1/command/avatar/set-long-term-objective")
    async def set_long_term_objective_v1(req: SetObjectiveRequest):
        return ok_response(await run_set_long_term_objective(req))

    @router.post("/api/v1/command/avatar/clear-long-term-objective")
    async def clear_long_term_objective_v1(req: ClearObjectiveRequest):
        return ok_response(await run_clear_long_term_objective(req))

    @router.post("/api/v1/command/avatar/create")
    async def create_avatar_v1(req: CreateAvatarRequest):
        return ok_response(await run_create_avatar(req))

    @router.post("/api/v1/command/avatar/delete")
    async def delete_avatar_v1(req: DeleteAvatarRequest):
        return ok_response(await run_delete_avatar(avatar_id=req.avatar_id))

    @router.post("/api/v1/command/avatar/update-adjustment")
    async def update_avatar_adjustment_v1(req: UpdateAvatarAdjustmentRequest):
        return ok_response(await run_update_avatar_adjustment(req))

    @router.post("/api/v1/command/avatar/update-portrait")
    async def update_avatar_portrait_v1(req: UpdateAvatarPortraitRequest):
        return ok_response(
            await run_update_avatar_portrait(avatar_id=req.avatar_id, pic_id=req.pic_id)
        )

    @router.post("/api/v1/command/avatar/generate-custom-content")
    async def generate_custom_content_v1(req: GenerateCustomContentRequest):
        return ok_response(await run_generate_custom_content(req))

    @router.post("/api/v1/command/avatar/create-custom-content")
    def create_custom_content_v1(req: CreateCustomContentRequest):
        return ok_response(run_create_custom_content(req))

    @router.post("/api/v1/command/world/set-phenomenon")
    async def set_phenomenon_v1(req: SetPhenomenonRequest):
        return ok_response(await run_set_phenomenon(phenomenon_id=req.id))

    @router.delete("/api/v1/command/events/cleanup")
    async def cleanup_events_v1(
        keep_major: bool = True,
        before_month_stamp: int = None,
    ):
        return ok_response(
            await run_cleanup_events(
                keep_major=keep_major,
                before_month_stamp=before_month_stamp,
            )
        )

    @router.post("/api/v1/command/game/save")
    def api_save_game_v1(req: SaveGameRequest):
        return ok_response(run_save_game(custom_name=req.custom_name))

    @router.post("/api/v1/command/game/delete-save")
    def api_delete_game_v1(req: DeleteSaveRequest):
        return ok_response(run_delete_save(filename=req.filename))

    @router.post("/api/v1/command/game/load")
    async def api_load_game_v1(req: LoadGameRequest):
        return ok_response(await run_load_game(filename=req.filename))

    return router
