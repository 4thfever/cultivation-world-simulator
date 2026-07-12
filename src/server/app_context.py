from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.server.host_runtime import ConnectionManager
from src.server.runtime import GameSessionRuntime
from src.server.services.game_command_service import GameCommandService
from src.server.services.game_query_service import GameQueryService


@dataclass(slots=True)
class ServerAppContext:
    """Composition container for the server runtime and public services."""

    runtime: GameSessionRuntime
    manager: ConnectionManager
    game_state: dict[str, Any]
    avatar_assets: dict[str, Any]
    settings_service: Any
    static_data: Any
    query_service: GameQueryService
    command_service: GameCommandService
    version: str = ""
