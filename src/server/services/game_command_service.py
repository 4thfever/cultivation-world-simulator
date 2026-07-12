from __future__ import annotations

from typing import Any


class GameCommandService:
    """Stable public-command service facade.

    The existing command handler namespace remains the implementation detail
    for Phase 1. Public routers call this service object so command growth no
    longer expands router factory signatures.
    """

    def __init__(self, handlers: Any):
        self._handlers = handlers

    @classmethod
    def from_dependencies(cls, *, static_data: Any, **dependencies: Any) -> "GameCommandService":
        """Create the service from command dependencies.

        Command handlers stay behind the service boundary so router/app wiring
        does not keep growing with command-specific dependency lists.
        """
        from src.server.command_handlers import create_command_handlers

        handlers = create_command_handlers(
            **dependencies,
            sects_by_id=static_data.sects_by_id,
            celestial_phenomena_by_id=static_data.celestial_phenomena_by_id,
        )
        return cls(handlers)

    @property
    def handlers(self) -> Any:
        return self._handlers

    async def start_game(self, req: Any) -> dict:
        return await self._handlers.run_start_game(req)

    async def reinit_game(self) -> dict:
        return await self._handlers.run_reinit_game()

    async def reset_game(self) -> dict:
        return await self._handlers.run_reset_game()

    async def pause_game(self) -> dict:
        return await self._handlers.run_pause_game()

    async def pause_game_and_drain(self) -> dict:
        return await self._handlers.run_pause_game_and_drain()

    async def resume_game(self) -> dict:
        return await self._handlers.run_resume_game()

    async def set_long_term_objective(self, req: Any) -> dict:
        return await self._handlers.run_set_long_term_objective(req)

    async def clear_long_term_objective(self, req: Any) -> dict:
        return await self._handlers.run_clear_long_term_objective(req)

    async def create_avatar(self, req: Any) -> dict:
        return await self._handlers.run_create_avatar(req)

    async def delete_avatar(self, *, avatar_id: str) -> dict:
        return await self._handlers.run_delete_avatar(avatar_id=avatar_id)

    async def update_avatar_adjustment(self, req: Any) -> dict:
        return await self._handlers.run_update_avatar_adjustment(req)

    async def update_avatar_portrait(self, *, avatar_id: str, pic_id: int) -> dict:
        return await self._handlers.run_update_avatar_portrait(
            avatar_id=avatar_id,
            pic_id=pic_id,
        )

    async def generate_custom_content(self, req: Any) -> dict:
        return await self._handlers.run_generate_custom_content(req)

    def create_custom_content(self, req: Any) -> dict:
        return self._handlers.run_create_custom_content(req)

    async def set_phenomenon(self, *, phenomenon_id: int) -> dict:
        return await self._handlers.run_set_phenomenon(phenomenon_id=phenomenon_id)

    async def cleanup_events(
        self,
        *,
        keep_major: bool,
        before_month_stamp: int | None,
    ) -> dict:
        return await self._handlers.run_cleanup_events(
            keep_major=keep_major,
            before_month_stamp=before_month_stamp,
        )

    def save_game(self, *, custom_name: str | None) -> dict:
        return self._handlers.run_save_game(custom_name=custom_name)

    def delete_save(self, *, filename: str) -> dict:
        return self._handlers.run_delete_save(filename=filename)

    async def load_game(self, *, filename: str) -> dict:
        return await self._handlers.run_load_game(filename=filename)

    async def start_roleplay(self, *, avatar_id: str) -> dict:
        # This command mutates only runtime session metadata and intentionally
        # follows the underlying roleplay service's non-locking path.
        return await self._handlers.run_start_roleplay(avatar_id=avatar_id)

    async def stop_roleplay(self, *, avatar_id: str | None) -> dict:
        return await self._handlers.run_stop_roleplay(avatar_id=avatar_id)

    async def submit_roleplay_decision(
        self,
        *,
        avatar_id: str,
        request_id: str,
        command_text: str,
    ) -> dict:
        return await self._handlers.run_submit_roleplay_decision(
            avatar_id=avatar_id,
            request_id=request_id,
            command_text=command_text,
        )

    async def submit_roleplay_choice(
        self,
        *,
        avatar_id: str,
        request_id: str,
        selected_key: str,
    ) -> dict:
        return await self._handlers.run_submit_roleplay_choice(
            avatar_id=avatar_id,
            request_id=request_id,
            selected_key=selected_key,
        )

    async def send_roleplay_conversation(
        self,
        *,
        avatar_id: str,
        request_id: str,
        message: str,
    ) -> dict:
        return await self._handlers.run_send_roleplay_conversation(
            avatar_id=avatar_id,
            request_id=request_id,
            message=message,
        )

    async def end_roleplay_conversation(
        self,
        *,
        avatar_id: str,
        request_id: str,
    ) -> dict:
        return await self._handlers.run_end_roleplay_conversation(
            avatar_id=avatar_id,
            request_id=request_id,
        )
