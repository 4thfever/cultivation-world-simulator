from __future__ import annotations

from types import SimpleNamespace


def create_command_handlers(*, static_data=None, sects_by_id=None, celestial_phenomena_by_id=None, **dependencies):
    """Legacy adapter for historical tests/imports.

    New code should construct and call `GameCommandService` directly.
    """
    if static_data is None:
        if sects_by_id is None or celestial_phenomena_by_id is None:
            from src.run.static_data_registry import build_static_game_data_registry

            static_data = build_static_game_data_registry()
        else:
            static_data = SimpleNamespace(
                sects_by_id=sects_by_id,
                celestial_phenomena_by_id=celestial_phenomena_by_id,
            )

    from src.server.services.game_command_service import GameCommandService

    return GameCommandService.from_dependencies(
        static_data=static_data,
        **dependencies,
    ).handlers
