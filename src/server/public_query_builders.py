from __future__ import annotations

from types import SimpleNamespace


def create_public_query_builders(
    *,
    runtime,
    avatar_assets,
    config,
    model_to_dict,
    get_runtime_run_config,
    resolve_avatar_action_emoji,
    resolve_avatar_pic_id,
    serialize_events_for_client,
    serialize_phenomenon,
    get_world_state,
    get_world_map,
    sects_by_id,
    get_runtime_status,
    get_events_page,
    get_game_data_query,
    personas_by_id,
    realm_order,
    techniques_by_id,
    weapons_by_id,
    auxiliaries_by_id,
    alignment_enum,
    get_detail_query,
    build_sect_detail,
    language_manager,
    build_avatar_adjust_options,
    get_avatar_assets_meta_query,
    get_avatar_list_query,
    get_phenomena_list_query,
    celestial_phenomena_by_id,
    get_sect_territories_summary_query,
    list_saves_query,
    get_list_saves,
    get_rankings_query,
    get_sect_relations_query,
    compute_sect_relations,
    get_mortal_overview_query,
    build_mortal_overview,
    get_dynasty_overview_query,
    build_dynasty_overview,
    get_dynasty_detail_query,
    build_dynasty_detail,
    get_deceased_list_query,
):
    def _resolve_avatar_pic_id(avatar):
        return resolve_avatar_pic_id(avatar_assets=avatar_assets, avatar=avatar)

    def build_public_world_state() -> dict:
        return get_world_state(
            runtime,
            resolve_avatar_action_emoji=resolve_avatar_action_emoji,
            resolve_avatar_pic_id=_resolve_avatar_pic_id,
            serialize_events_for_client=serialize_events_for_client,
            serialize_phenomenon=serialize_phenomenon,
        )

    def build_public_world_map() -> dict:
        return get_world_map(
            runtime,
            sects_by_id=sects_by_id,
            render_config=config.get("frontend_defaults", {}),
        )

    def build_public_runtime_status() -> dict:
        return get_runtime_status(
            runtime,
            getattr(getattr(config, "meta", None), "version", ""),
        )

    def build_public_current_run() -> dict:
        return model_to_dict(get_runtime_run_config(runtime))

    def build_public_events_page(
        *,
        avatar_id: str | None,
        avatar_id_1: str | None,
        avatar_id_2: str | None,
        sect_id: int | None,
        major_scope: str,
        cursor: str | None,
        limit: int,
    ) -> dict:
        return get_events_page(
            runtime,
            serialize_events_for_client=serialize_events_for_client,
            avatar_id=avatar_id,
            avatar_id_1=avatar_id_1,
            avatar_id_2=avatar_id_2,
            sect_id=sect_id,
            major_scope=major_scope,
            cursor=cursor,
            limit=limit,
        )

    def build_public_game_data() -> dict:
        return get_game_data_query(
            sects_by_id=sects_by_id,
            personas_by_id=personas_by_id,
            realm_order=realm_order,
            techniques_by_id=techniques_by_id,
            weapons_by_id=weapons_by_id,
            auxiliaries_by_id=auxiliaries_by_id,
            alignment_enum=alignment_enum,
        )

    def build_public_detail(*, target_type: str, target_id: str) -> dict:
        return get_detail_query(
            runtime,
            target_type=target_type,
            target_id=target_id,
            sects_by_id=sects_by_id,
            build_sect_detail=build_sect_detail,
            language_manager=language_manager,
            resolve_avatar_pic_id=_resolve_avatar_pic_id,
        )

    def build_public_avatar_adjust_options() -> dict:
        return build_avatar_adjust_options()

    def build_public_avatar_meta() -> dict:
        return get_avatar_assets_meta_query(avatar_assets=avatar_assets)

    def build_public_avatar_list() -> dict:
        return get_avatar_list_query(runtime)

    def build_public_phenomena() -> dict:
        return get_phenomena_list_query(
            celestial_phenomena_by_id=celestial_phenomena_by_id,
            serialize_phenomenon=serialize_phenomenon,
        )

    def build_public_sect_territories() -> dict:
        return get_sect_territories_summary_query(runtime)

    def build_public_saves() -> dict:
        return list_saves_query(list_saves=get_list_saves())

    def build_public_rankings() -> dict:
        return get_rankings_query(runtime)

    def build_public_sect_relations() -> dict:
        return get_sect_relations_query(runtime, compute_sect_relations=compute_sect_relations)

    def build_public_mortal_overview() -> dict:
        return get_mortal_overview_query(runtime, build_mortal_overview=build_mortal_overview)

    def build_public_dynasty_overview() -> dict:
        return get_dynasty_overview_query(runtime, build_dynasty_overview=build_dynasty_overview)

    def build_public_dynasty_detail() -> dict:
        return get_dynasty_detail_query(runtime, build_dynasty_detail=build_dynasty_detail)

    def build_public_deceased_list() -> dict:
        return get_deceased_list_query(runtime)

    return SimpleNamespace(
        build_public_world_state=build_public_world_state,
        build_public_world_map=build_public_world_map,
        build_public_runtime_status=build_public_runtime_status,
        build_public_current_run=build_public_current_run,
        build_public_events_page=build_public_events_page,
        build_public_game_data=build_public_game_data,
        build_public_detail=build_public_detail,
        build_public_avatar_adjust_options=build_public_avatar_adjust_options,
        build_public_avatar_meta=build_public_avatar_meta,
        build_public_avatar_list=build_public_avatar_list,
        build_public_phenomena=build_public_phenomena,
        build_public_sect_territories=build_public_sect_territories,
        build_public_saves=build_public_saves,
        build_public_rankings=build_public_rankings,
        build_public_sect_relations=build_public_sect_relations,
        build_public_mortal_overview=build_public_mortal_overview,
        build_public_dynasty_overview=build_public_dynasty_overview,
        build_public_dynasty_detail=build_public_dynasty_detail,
        build_public_deceased_list=build_public_deceased_list,
    )
