from __future__ import annotations

from src.utils.df import game_configs

from .random_minor_event_types import (
    MinorEventCategory,
    MinorEventParticipants,
    MinorEventRelationHint,
    MinorEventTone,
    MinorEventType,
)


def _parse_event_type(record: dict) -> MinorEventType:
    try:
        category = MinorEventCategory(str(record["category"]))
        participants = MinorEventParticipants(str(record["participants"]))
        tone = MinorEventTone(str(record["tone"]))
        relation_hint = MinorEventRelationHint(str(record["relation_hint"]))
    except KeyError as exc:
        raise ValueError(f"Missing random minor event field: {exc.args[0]}") from exc
    except ValueError as exc:
        raise ValueError(f"Invalid random minor event enum value in record: {record}") from exc

    event_key = str(record.get("event_key", "")).strip()
    desc_id = str(record.get("desc_id", "")).strip()
    if not event_key:
        raise ValueError(f"Missing random minor event event_key: {record}")
    if not desc_id:
        raise ValueError(f"Missing random minor event desc_id: {record}")

    try:
        weight = float(record.get("weight", 1.0))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid random minor event weight: {record}") from exc

    if weight <= 0:
        raise ValueError(f"Random minor event weight must be positive: {record}")

    return MinorEventType(
        event_key=event_key,
        category=category,
        participants=participants,
        tone=tone,
        relation_hint=relation_hint,
        weight=weight,
        desc_id=desc_id,
    )


def load_minor_event_types() -> list[MinorEventType]:
    records = game_configs.get("random_minor_event", [])
    if not records:
        return []
    return [_parse_event_type(record) for record in records]


__all__ = ["load_minor_event_types"]
