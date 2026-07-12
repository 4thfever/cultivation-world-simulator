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


def create_server_context(
    *,
    runtime: GameSessionRuntime,
    manager: ConnectionManager,
    game_state: dict[str, Any],
    avatar_assets: dict[str, Any],
    settings_service: Any,
    static_data: Any,
    query_dependencies: dict[str, Any],
    command_dependencies: dict[str, Any],
    version: str = "",
) -> ServerAppContext:
    """Build the server composition root from explicit dependency maps."""
    query_service = GameQueryService.from_dependencies(
        static_data=static_data,
        **query_dependencies,
    )
    command_service = GameCommandService.from_dependencies(
        static_data=static_data,
        **command_dependencies,
    )
    return ServerAppContext(
        runtime=runtime,
        manager=manager,
        game_state=game_state,
        avatar_assets=avatar_assets,
        settings_service=settings_service,
        static_data=static_data,
        query_service=query_service,
        command_service=command_service,
        version=version,
    )
