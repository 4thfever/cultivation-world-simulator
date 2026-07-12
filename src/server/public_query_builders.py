from __future__ import annotations

from types import SimpleNamespace


def create_public_query_builders(*, static_data=None, **dependencies):
    """Legacy adapter for historical tests/imports.

    New code should construct and call `GameQueryService` directly.
    """
    legacy_static_keys = {
        "sects_by_id",
        "races_by_id",
        "personas_by_id",
        "techniques_by_id",
        "weapons_by_id",
        "auxiliaries_by_id",
        "goldfingers_by_id",
        "celestial_phenomena_by_id",
    }
    legacy_static = {
        key: dependencies.pop(key)
        for key in list(dependencies)
        if key in legacy_static_keys
    }

    if static_data is None and legacy_static:
        static_data = SimpleNamespace(
            sects_by_id=legacy_static.get("sects_by_id", {}),
            races_by_id=legacy_static.get("races_by_id", {}),
            personas_by_id=legacy_static.get("personas_by_id", {}),
            techniques_by_id=legacy_static.get("techniques_by_id", {}),
            weapons_by_id=legacy_static.get("weapons_by_id", {}),
            auxiliaries_by_id=legacy_static.get("auxiliaries_by_id", {}),
            goldfingers_by_id=legacy_static.get("goldfingers_by_id", {}),
            celestial_phenomena_by_id=legacy_static.get("celestial_phenomena_by_id", {}),
        )

    if static_data is None:
        from src.run.static_data_registry import build_static_game_data_registry

        static_data = build_static_game_data_registry()

    from src.server.services.game_query_service import GameQueryService

    return GameQueryService.from_dependencies(
        static_data=static_data,
        **dependencies,
    ).builders
