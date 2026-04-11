from __future__ import annotations

from typing import Any

from src.classes.effect import format_effects_to_text


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


def serialize_events_for_client(events: list[Any]) -> list[dict[str, Any]]:
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
