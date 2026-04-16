from __future__ import annotations

import asyncio
import inspect
import time
from typing import Any, Awaitable, Callable


DEFAULT_GAME_STATE: dict[str, Any] = {
    "world": None,
    "sim": None,
    "is_paused": True,
    "roleplay_auto_paused": False,
    "init_status": "idle",
    "init_phase": 0,
    "init_phase_name": "",
    "init_progress": 0,
    "init_error": None,
    "init_start_time": None,
    "run_config": None,
    "current_save_path": None,
    "llm_check_failed": False,
    "llm_error_message": "",
    "roleplay_session": {
        "controlled_avatar_id": None,
        "status": "inactive",
        "pending_request": None,
        "last_prompt_context": None,
    },
}


class GameSessionRuntime:
    """
    Unified access point for the in-memory game session state.

    Phase 1 keeps the underlying storage as a plain dict so existing code and
    tests can still interact with `game_instance`, while lifecycle mutations
    and simulator stepping are gradually routed through this runtime facade.
    """

    def __init__(self, state: dict[str, Any]):
        self._state = state
        self._mutation_lock = asyncio.Lock()

    @property
    def state(self) -> dict[str, Any]:
        return self._state

    def get(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

    def update(self, values: dict[str, Any]) -> None:
        self._state.update(values)

    def replace_with_defaults(self) -> None:
        self._state.clear()
        self._state.update(DEFAULT_GAME_STATE)

    def reset_to_idle(self, *, clear_run_config: bool = True) -> None:
        run_config = None if clear_run_config else self._state.get("run_config")
        self._state.update(
            {
                "world": None,
                "sim": None,
                "current_save_path": None,
                "run_config": run_config,
                "is_paused": True,
                "roleplay_auto_paused": False,
                "init_status": "idle",
                "init_phase": 0,
                "init_phase_name": "",
                "init_progress": 0,
                "init_error": None,
                "init_start_time": None,
                "llm_check_failed": False,
                "llm_error_message": "",
            }
        )
        self.clear_roleplay_session()

    def mark_pending_initialization(self, *, clear_world: bool) -> None:
        if clear_world:
            self._state["world"] = None
            self._state["sim"] = None
            self._state["current_save_path"] = None
        self._state["is_paused"] = True
        self._state["roleplay_auto_paused"] = False
        self._state["init_status"] = "pending"
        self._state["init_phase"] = 0
        self._state["init_phase_name"] = ""
        self._state["init_progress"] = 0
        self._state["init_error"] = None
        self.clear_roleplay_session()

    def begin_initialization(self) -> None:
        self._state["init_status"] = "in_progress"
        self._state["init_start_time"] = time.time()
        self._state["init_error"] = None

    def finish_initialization(self, *, phase_name: str = "") -> None:
        self._state["init_status"] = "ready"
        self._state["init_progress"] = 100
        if phase_name:
            self._state["init_phase_name"] = phase_name

    def fail_initialization(self, error: str) -> None:
        self._state["init_status"] = "error"
        self._state["init_error"] = str(error)

    def set_paused(self, paused: bool) -> None:
        self._state["is_paused"] = bool(paused)

    def set_roleplay_auto_paused(self, paused: bool) -> None:
        self._state["roleplay_auto_paused"] = bool(paused)

    def is_effectively_paused(self) -> bool:
        return bool(self._state.get("is_paused", False) or self._state.get("roleplay_auto_paused", False))

    def get_pause_reason(self) -> str:
        if self._state.get("roleplay_auto_paused", False):
            session = self.get_roleplay_session()
            status = str(session.get("status", "") or "")
            if status == "awaiting_decision":
                return "roleplay_waiting_decision"
            if status == "awaiting_choice":
                return "roleplay_waiting_choice"
            return "roleplay_waiting"
        if self._state.get("is_paused", False):
            return "paused"
        return ""

    def get_roleplay_session(self) -> dict[str, Any]:
        session = self._state.get("roleplay_session")
        if not isinstance(session, dict):
            session = {
                "controlled_avatar_id": None,
                "status": "inactive",
                "pending_request": None,
                "last_prompt_context": None,
            }
            self._state["roleplay_session"] = session
        return session

    def clear_roleplay_session(self) -> None:
        existing = self._state.get("roleplay_session")
        if isinstance(existing, dict):
            choice_future = existing.get("_choice_future")
            try:
                if choice_future is not None and hasattr(choice_future, "done") and not choice_future.done():
                    choice_future.cancel()
            except Exception:
                pass
        self._state["roleplay_session"] = {
            "controlled_avatar_id": None,
            "status": "inactive",
            "pending_request": None,
            "last_prompt_context": None,
        }
        self._state["roleplay_auto_paused"] = False

    async def run_mutation(
        self,
        operation: Callable[..., Any] | Awaitable[Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Serialize world mutations and simulator stepping through one lock.
        """
        async with self._mutation_lock:
            if callable(operation):
                result = operation(*args, **kwargs)
            else:
                result = operation

            if inspect.isawaitable(result):
                return await result
            return result
