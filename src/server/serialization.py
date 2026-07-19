from __future__ import annotations

from typing import Any

from src.classes.effect import format_effects_to_text


def _get_avatar_by_id(world, avatar_id: str):
    avatar_manager = getattr(world, "avatar_manager", None)
    if avatar_manager is None:
        return None

    get_avatar = getattr(avatar_manager, "get_avatar", None)
    if callable(get_avatar):
        avatar = get_avatar(avatar_id)
        if avatar is not None:
            return avatar

    avatars = getattr(avatar_manager, "avatars", None)
    if isinstance(avatars, dict):
        return avatars.get(avatar_id)

    return None


def _get_deceased_record_by_id(world, avatar_id: str):
    deceased_manager = getattr(world, "deceased_manager", None)
    if deceased_manager is None:
        return None

    get_record = getattr(deceased_manager, "get_record", None)
    if callable(get_record):
        return get_record(avatar_id)

    return None


def _get_sect_by_id(world, sect_id: int):
    sect_context = getattr(world, "sect_context", None)
    if sect_context is not None:
        get_active_sects = getattr(sect_context, "get_active_sects", None)
        if callable(get_active_sects):
            for sect in get_active_sects():
                if int(getattr(sect, "id", -1)) == sect_id:
                    return sect

    for sect in getattr(world, "existed_sects", []) or []:
        if int(getattr(sect, "id", -1)) == sect_id:
            return sect

    try:
        from src.classes.core.sect import sects_by_id

        return sects_by_id.get(sect_id)
    except Exception:
        return None


def _build_event_subjects(event: Any, world: Any | None) -> list[dict[str, Any]]:
    """Build display subjects from structured event relations."""
    subjects: list[dict[str, Any]] = []

    snapshots = getattr(event, "subject_snapshots", None) or {}
    for avatar_id in (getattr(event, "related_avatars", None) or []):
        avatar_id_str = str(avatar_id)
        snapshot_name = str(snapshots.get(avatar_id_str) or "")
        avatar = _get_avatar_by_id(world, avatar_id_str) if world is not None else None
        if avatar is not None:
            subjects.append(
                {
                    "type": "avatar",
                    "id": avatar_id_str,
                    "name": snapshot_name or str(getattr(avatar, "name", avatar_id_str)),
                    "is_dead": bool(getattr(avatar, "is_dead", False)),
                }
            )
            continue

        record = _get_deceased_record_by_id(world, avatar_id_str) if world is not None else None
        if record is not None:
            subjects.append(
                {
                    "type": "avatar",
                    "id": avatar_id_str,
                    "name": snapshot_name or str(getattr(record, "name", avatar_id_str)),
                    "is_dead": True,
                }
            )
            continue

        subjects.append(
            {
                "type": "avatar",
                "id": avatar_id_str,
                "name": snapshot_name or avatar_id_str,
                "is_dead": False,
            }
        )

    for sect_id in (getattr(event, "related_sects", None) or []):
        sect_id_int = int(sect_id)
        sect = _get_sect_by_id(world, sect_id_int) if world is not None else None
        if sect is not None:
            subjects.append(
                {
                    "type": "sect",
                    "id": sect_id_int,
                    "name": str(getattr(sect, "name", sect_id_int)),
                    "color": getattr(sect, "color", None),
                    "is_active": bool(getattr(sect, "is_active", True)),
                }
            )
            continue

        subjects.append(
            {
                "type": "sect",
                "id": sect_id_int,
                "name": str(sect_id_int),
            }
        )

    return subjects


def serialize_active_domains(world) -> list[dict[str, Any]]:
    """Serialize hidden-domain configs for frontend display."""
    domains_data: list[dict[str, Any]] = []
    gathering_manager = getattr(world, "gathering_manager", None)
    if not world or not gathering_manager:
        return domains_data

    hidden_domain_gathering = next(
        (
            gathering
            for gathering in gathering_manager.gatherings
            if gathering.__class__.__name__ == "HiddenDomain"
        ),
        None,
    )
    if hidden_domain_gathering is None:
        return domains_data

    all_configs = hidden_domain_gathering._load_configs()
    for domain in all_configs:
        domains_data.append(
            {
                "id": domain.id,
                "name": domain.name,
                "desc": domain.desc,
                "required_realm": str(domain.required_realm),
                "danger_prob": domain.danger_prob,
                "drop_prob": domain.drop_prob,
                "cd_years": domain.cd_years,
                "open_prob": domain.open_prob,
            }
        )

    return domains_data


def serialize_events_for_client(events: list[Any], *, world: Any | None = None) -> list[dict[str, Any]]:
    """Convert runtime Event objects into transport-safe JSON dicts."""
    serialized: list[dict[str, Any]] = []
    for idx, event in enumerate(events):
        month_stamp = getattr(event, "month_stamp", None)
        stamp_int = None
        year = None
        month = None
        if month_stamp is not None:
            try:
                stamp_int = int(month_stamp)
            except Exception:
                stamp_int = None
            try:
                year = int(month_stamp.get_year())
            except Exception:
                year = None
            try:
                month = month_stamp.get_month().value
            except Exception:
                month = None

        related_avatar_ids = [
            str(avatar_id)
            for avatar_id in (getattr(event, "related_avatars", None) or [])
            if avatar_id is not None
        ]
        related_sect_ids = [
            int(sect_id)
            for sect_id in (getattr(event, "related_sects", None) or [])
            if sect_id is not None
        ]

        serialized.append(
            {
                "id": getattr(event, "id", None) or f"{stamp_int or 'evt'}-{idx}",
                "text": str(event),
                "content": getattr(event, "content", ""),
                "year": year,
                "month": month,
                "month_stamp": stamp_int,
                "related_avatar_ids": related_avatar_ids,
                "related_sects": related_sect_ids,
                "subjects": _build_event_subjects(event, world),
                "is_major": bool(getattr(event, "is_major", False)),
                "is_story": bool(getattr(event, "is_story", False)),
                "render_key": getattr(event, "render_key", None),
                "render_params": getattr(event, "render_params", None),
                "created_at": getattr(event, "created_at", 0.0),
            }
        )

    return serialized


def serialize_phenomenon(phenomenon) -> dict[str, Any] | None:
    """Serialize the current celestial phenomenon for frontend consumption."""
    if not phenomenon:
        return None

    rarity = getattr(phenomenon, "rarity", None)
    rarity_str = "N"
    if rarity:
        if hasattr(rarity, "name"):
            rarity_str = rarity.name
        elif hasattr(rarity, "level") and hasattr(rarity.level, "name"):
            rarity_str = rarity.level.name

    effect_desc = format_effects_to_text(phenomenon.effects) if hasattr(phenomenon, "effects") else ""

    return {
        "id": phenomenon.id,
        "name": phenomenon.name,
        "desc": phenomenon.desc,
        "rarity": rarity_str,
        "duration_years": phenomenon.duration_years,
        "effect_desc": effect_desc,
    }
