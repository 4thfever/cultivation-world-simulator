from __future__ import annotations

from typing import Any


class GameQueryService:
    """Stable public-query service facade.

    Phase 1 keeps the existing query builder implementation underneath, but
    routers depend on this explicit service object instead of a long list of
    builder callables.
    """

    def __init__(self, builders: Any):
        self._builders = builders

    @classmethod
    def from_dependencies(cls, *, static_data: Any, **dependencies: Any) -> "GameQueryService":
        """Create the service from concrete query dependencies.

        The old builder namespace remains an internal implementation detail,
        while callers only compose a query service.
        """
        from src.server.public_query_builders import create_public_query_builders

        builders = create_public_query_builders(
            **dependencies,
            sects_by_id=static_data.sects_by_id,
            races_by_id=static_data.races_by_id,
            personas_by_id=static_data.personas_by_id,
            techniques_by_id=static_data.techniques_by_id,
            weapons_by_id=static_data.weapons_by_id,
            auxiliaries_by_id=static_data.auxiliaries_by_id,
            celestial_phenomena_by_id=static_data.celestial_phenomena_by_id,
        )
        return cls(builders)

    @property
    def builders(self) -> Any:
        return self._builders

    def get_runtime_status(self) -> dict:
        return self._builders.build_public_runtime_status()

    def get_world_state(self) -> dict:
        return self._builders.build_public_world_state()

    def get_world_map(self) -> dict:
        return self._builders.build_public_world_map()

    def get_map_presets(self, *, locale: str | None = None) -> dict:
        return self._builders.build_public_map_presets(locale=locale)

    def get_current_run(self) -> dict:
        return self._builders.build_public_current_run()

    def get_events_page(
        self,
        *,
        avatar_id: str | None,
        avatar_id_1: str | None,
        avatar_id_2: str | None,
        sect_id: int | None,
        major_scope: str,
        cursor: str | None,
        limit: int,
    ) -> dict:
        return self._builders.build_public_events_page(
            avatar_id=avatar_id,
            avatar_id_1=avatar_id_1,
            avatar_id_2=avatar_id_2,
            sect_id=sect_id,
            major_scope=major_scope,
            cursor=cursor,
            limit=limit,
        )

    def get_rankings(self) -> dict:
        return self._builders.build_public_rankings()

    def get_sect_relations(self) -> dict:
        return self._builders.build_public_sect_relations()

    def get_game_data(self) -> dict:
        return self._builders.build_public_game_data()

    def get_avatar_adjust_options(self) -> dict:
        return self._builders.build_public_avatar_adjust_options()

    def get_avatar_meta(self) -> dict:
        return self._builders.build_public_avatar_meta()

    def get_avatar_list(self) -> dict:
        return self._builders.build_public_avatar_list()

    def get_phenomena(self) -> dict:
        return self._builders.build_public_phenomena()

    def get_sect_territories(self) -> dict:
        return self._builders.build_public_sect_territories()

    def get_mortal_overview(self) -> dict:
        return self._builders.build_public_mortal_overview()

    def get_dynasty_overview(self) -> dict:
        return self._builders.build_public_dynasty_overview()

    def get_dynasty_detail(self) -> dict:
        return self._builders.build_public_dynasty_detail()

    def get_avatar_overview(self) -> dict:
        return self._builders.build_public_avatar_overview()

    def get_saves(self) -> dict:
        return self._builders.build_public_saves()

    def get_detail(self, *, target_type: str, target_id: str) -> dict:
        return self._builders.build_public_detail(
            target_type=target_type,
            target_id=target_id,
        )

    def get_deceased_list(self) -> dict:
        return self._builders.build_public_deceased_list()

    def get_roleplay_session(self) -> dict:
        return self._builders.build_public_roleplay_session()

    def get_world_secret_meta(self) -> dict:
        return self._builders.build_public_world_secret_meta()

    def get_world_secret_overview(self) -> dict:
        return self._builders.build_public_world_secret_overview()
