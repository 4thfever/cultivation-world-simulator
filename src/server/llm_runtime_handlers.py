from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Callable

from src.utils.llm.config import LLMConfig


def create_llm_runtime_handlers(
    *,
    game_state: dict[str, Any],
    manager: Any,
    settings_service: Any,
    create_llm_updated_handler: Callable[..., Any],
    test_connectivity_impl: Callable[..., tuple[bool, str]],
) -> SimpleNamespace:
    def test_connectivity(config):
        return test_connectivity_impl(config=config)

    def test_llm_connection(req) -> dict:
        profile, api_key = settings_service.get_llm_test_payload(req)
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

    handle_llm_updated = create_llm_updated_handler(
        game_instance=game_state,
        manager=manager,
    )

    async def handle_global_llm_failure(error_message: str) -> None:
        if game_state.get("llm_check_failed") and game_state.get("llm_error_message") == error_message:
            return

        game_state["llm_check_failed"] = True
        game_state["llm_error_message"] = error_message
        game_state["is_paused"] = True
        await manager.broadcast(
            {
                "type": "llm_config_required",
                "error": error_message,
            }
        )

    return SimpleNamespace(
        test_connectivity=test_connectivity,
        test_llm_connection=test_llm_connection,
        handle_llm_updated=handle_llm_updated,
        handle_global_llm_failure=handle_global_llm_failure,
    )
