from __future__ import annotations

from typing import Callable

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.i18n import t


def create_websocket_router(
    *,
    manager,
    game_instance: dict,
) -> APIRouter:
    router = APIRouter()

    @router.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await manager.connect(websocket)

        if game_instance.get("llm_check_failed", False):
            error_msg = game_instance.get("llm_error_message", t("LLM connection failed"))
            await websocket.send_json({
                "type": "llm_config_required",
                "error": error_msg,
            })
            print(f"Sent LLM configuration requirement to client: {error_msg}")

        try:
            while True:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text('{"type":"pong"}')
        except WebSocketDisconnect:
            manager.disconnect(websocket)
        except Exception as exc:
            print(f"WS Error: {exc}")
            manager.disconnect(websocket)

    return router
