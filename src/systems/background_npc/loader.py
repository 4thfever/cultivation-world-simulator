from __future__ import annotations

from src.utils.df import game_configs, get_float, get_int, get_str

from .models import (
    BackgroundNpcEventType,
    BackgroundNpcProfile,
    BackgroundNpcRegionBinding,
    BackgroundNpcTriggerKind,
)


def _split_tokens(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    text = str(value).strip()
    if not text:
        return ()
    return tuple(part.strip() for part in text.replace("|", ";").split(";") if part.strip())


def _parse_avatar_filters(value: object) -> dict[str, str]:
    filters: dict[str, str] = {}
    for token in _split_tokens(value):
        if "=" not in token:
            raise ValueError(f"Invalid background NPC avatar filter: {token}")
        key, raw_value = token.split("=", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        if not key or not raw_value:
            raise ValueError(f"Invalid background NPC avatar filter: {token}")
        filters[key] = raw_value
    return filters


def load_background_npc_profiles() -> list[BackgroundNpcProfile]:
    profiles: list[BackgroundNpcProfile] = []
    for row in game_configs.get("background_npc_profile", []) or []:
        profile_key = get_str(row, "profile_key")
        role_label_id = get_str(row, "role_label_id")
        if not profile_key or profile_key == "stable profile key":
            continue
        if not role_label_id:
            raise ValueError(f"Missing background NPC role_label_id: {row}")
        profiles.append(
            BackgroundNpcProfile(
                id=get_int(row, "id"),
                profile_key=profile_key,
                role_label_id=role_label_id,
                category=get_str(row, "category"),
                default_scene_tags=_split_tokens(row.get("default_scene_tags")),
            )
        )
    return profiles


def load_background_npc_event_types() -> list[BackgroundNpcEventType]:
    event_types: list[BackgroundNpcEventType] = []
    for row in game_configs.get("background_npc_event", []) or []:
        event_key = get_str(row, "event_key")
        if not event_key or event_key == "stable event key":
            continue
        profile_key = get_str(row, "profile_key")
        text_id = get_str(row, "text_id")
        if not profile_key:
            raise ValueError(f"Missing background NPC profile_key: {row}")
        if not text_id:
            raise ValueError(f"Missing background NPC text_id: {row}")
        try:
            trigger_kind = BackgroundNpcTriggerKind(get_str(row, "trigger_kind"))
        except ValueError as exc:
            raise ValueError(f"Invalid background NPC trigger_kind: {row}") from exc
        weight = get_float(row, "weight", 1.0)
        if weight <= 0:
            raise ValueError(f"Background NPC weight must be positive: {row}")
        event_types.append(
            BackgroundNpcEventType(
                id=get_int(row, "id"),
                event_key=event_key,
                profile_key=profile_key,
                trigger_kind=trigger_kind,
                region_types=_split_tokens(row.get("region_types")),
                required_tags=_split_tokens(row.get("required_tags")),
                excluded_tags=_split_tokens(row.get("excluded_tags")),
                map_ids=_split_tokens(row.get("map_ids")),
                avatar_filters=_parse_avatar_filters(row.get("avatar_filters")),
                action_keys=_split_tokens(row.get("action_keys")),
                weight=weight,
                cooldown_months=max(0, get_int(row, "cooldown_months", 0)),
                max_per_month=max(1, get_int(row, "max_per_month", 1)),
                text_id=text_id,
            )
        )
    return event_types


def load_background_npc_region_bindings() -> list[BackgroundNpcRegionBinding]:
    bindings: list[BackgroundNpcRegionBinding] = []
    for row in game_configs.get("background_npc_region_binding", []) or []:
        map_id = get_str(row, "map_id")
        if not map_id or map_id == "map id":
            continue
        region_id = get_int(row, "region_id", -1)
        if region_id < 0:
            raise ValueError(f"Invalid background NPC region_id: {row}")
        bindings.append(
            BackgroundNpcRegionBinding(
                id=get_int(row, "id"),
                map_id=map_id,
                region_id=region_id,
                scene_tags=_split_tokens(row.get("scene_tags")),
            )
        )
    return bindings


__all__ = [
    "load_background_npc_event_types",
    "load_background_npc_profiles",
    "load_background_npc_region_bindings",
]
