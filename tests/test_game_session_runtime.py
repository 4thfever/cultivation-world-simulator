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
            "roleplay_auto_paused": True,
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
    assert state["roleplay_auto_paused"] is False
    assert state["init_status"] == "idle"
    assert state["init_phase"] == 0
    assert state["init_phase_name"] == ""
    assert state["init_progress"] == 0
    assert state["init_error"] is None
    assert state["llm_check_failed"] is False
    assert state["llm_error_message"] == ""
    assert state["roleplay_session"]["controlled_avatar_id"] is None


def test_roleplay_pause_state_is_counted_in_effective_pause():
    runtime = GameSessionRuntime(dict(DEFAULT_GAME_STATE))

    assert runtime.is_effectively_paused() is True

    runtime.set_paused(False)
    assert runtime.is_effectively_paused() is False

    runtime.set_roleplay_auto_paused(True)
    assert runtime.is_effectively_paused() is True
    assert runtime.get_pause_reason() == "roleplay_waiting"

    runtime.clear_roleplay_session()
    assert runtime.is_effectively_paused() is False


def test_default_roleplay_session_is_not_shared_between_runtimes():
    runtime_a = GameSessionRuntime(dict(DEFAULT_GAME_STATE))
    runtime_a.get_roleplay_session()["pending_request"] = {"request_id": "leaked"}
    runtime_a.get_roleplay_session()["interaction_history"].append({"type": "test"})

    runtime_b = GameSessionRuntime(dict(DEFAULT_GAME_STATE))

    assert runtime_b.get_roleplay_session()["pending_request"] is None
    assert runtime_b.get_roleplay_session()["interaction_history"] == []
    assert DEFAULT_GAME_STATE["roleplay_session"]["pending_request"] is None
    assert DEFAULT_GAME_STATE["roleplay_session"]["interaction_history"] == []


def test_roleplay_pause_reason_reflects_choice_waiting():
    runtime = GameSessionRuntime(dict(DEFAULT_GAME_STATE))
    session = runtime.get_roleplay_session()
    session["controlled_avatar_id"] = "avatar-1"
    session["status"] = "awaiting_choice"
    session["pending_request"] = {"request_id": "choice-1", "type": "choice"}
    runtime.set_paused(False)
    runtime.set_roleplay_auto_paused(True)

    assert runtime.is_effectively_paused() is True
    assert runtime.get_pause_reason() == "roleplay_waiting_choice"


def test_clear_roleplay_session_cancels_pending_choice_future():
    runtime = GameSessionRuntime(dict(DEFAULT_GAME_STATE))
    loop = asyncio.new_event_loop()
    try:
        future = loop.create_future()
        session = runtime.get_roleplay_session()
        session["_choice_future"] = future

        runtime.clear_roleplay_session()

        assert future.cancelled() is True
        assert runtime.get_roleplay_session()["status"] == "inactive"
    finally:
        loop.close()


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
