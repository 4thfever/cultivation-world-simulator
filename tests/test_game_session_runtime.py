import asyncio

import pytest

from src.server.runtime import DEFAULT_GAME_STATE, GameSessionRuntime


def test_reset_to_idle_restores_defaults_and_clears_runtime_state():
    state = dict(DEFAULT_GAME_STATE)
    state.update(
        {
            "world": object(),
            "sim": object(),
            "run_config": {"content_locale": "en-US"},
            "current_save_path": "save.json",
            "is_paused": False,
            "init_status": "ready",
            "init_phase": 4,
            "init_phase_name": "generating_avatars",
            "init_progress": 80,
            "init_error": "boom",
            "llm_check_failed": True,
            "llm_error_message": "bad key",
        }
    )
    runtime = GameSessionRuntime(state)

    runtime.reset_to_idle()

    assert state["world"] is None
    assert state["sim"] is None
    assert state["run_config"] is None
    assert state["current_save_path"] is None
    assert state["is_paused"] is True
    assert state["init_status"] == "idle"
    assert state["init_phase"] == 0
    assert state["init_phase_name"] == ""
    assert state["init_progress"] == 0
    assert state["init_error"] is None
    assert state["llm_check_failed"] is False
    assert state["llm_error_message"] == ""


@pytest.mark.asyncio
async def test_run_mutation_serializes_concurrent_operations():
    runtime = GameSessionRuntime(dict(DEFAULT_GAME_STATE))
    execution_order: list[str] = []

    async def _slow(name: str, delay: float):
        execution_order.append(f"{name}:start")
        await asyncio.sleep(delay)
        execution_order.append(f"{name}:end")

    await asyncio.gather(
        runtime.run_mutation(_slow, "first", 0.03),
        runtime.run_mutation(_slow, "second", 0.0),
    )

    assert execution_order == [
        "first:start",
        "first:end",
        "second:start",
        "second:end",
    ]
