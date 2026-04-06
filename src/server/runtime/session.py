from __future__ import annotations

import asyncio
import inspect
import time
from typing import Any, Awaitable, Callable


DEFAULT_GAME_STATE: dict[str, Any] = {
    "world": None,
    "sim": None,
    "is_paused": True,
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

    def mark_pending_initialization(self, *, clear_world: bool) -> None:
        if clear_world:
            self._state["world"] = None
            self._state["sim"] = None
            self._state["current_save_path"] = None
        self._state["is_paused"] = True
        self._state["init_status"] = "pending"
        self._state["init_phase"] = 0
        self._state["init_phase_name"] = ""
        self._state["init_progress"] = 0
        self._state["init_error"] = None

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
