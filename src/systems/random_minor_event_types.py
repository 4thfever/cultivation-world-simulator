from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from src.classes.event import Event

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar


class MinorEventCategory(StrEnum):
    SOLO_INNER = "solo_inner"
    SOLO_DAILY = "solo_daily"
    PAIR_SOCIAL = "pair_social"


class MinorEventParticipants(StrEnum):
    SOLO = "solo"
    PAIR = "pair"


class MinorEventTone(StrEnum):
    NEUTRAL = "neutral"
    WARM = "warm"
    TENSE = "tense"
    COMPETITIVE = "competitive"


class MinorEventRelationHint(StrEnum):
    NONE = "none"
    MAYBE_UP = "maybe_up"
    MAYBE_DOWN = "maybe_down"
    MIXED = "mixed"


@dataclass(frozen=True)
class MinorEventType:
    event_key: str
    category: MinorEventCategory
    participants: MinorEventParticipants
    tone: MinorEventTone
    relation_hint: MinorEventRelationHint
    weight: float
    desc_id: str

    @property
    def is_pair_event(self) -> bool:
        return self.participants == MinorEventParticipants.PAIR


@dataclass(frozen=True)
class MinorEventContext:
    source_avatar: "Avatar"
    target_avatar: "Avatar | None"
    event_type: MinorEventType
    location_name: str
    world_info: str


@dataclass(frozen=True)
class MinorEventResult:
    event: Event
    a_to_b_delta: int | None = None
    b_to_a_delta: int | None = None


__all__ = [
    "MinorEventCategory",
    "MinorEventParticipants",
    "MinorEventTone",
    "MinorEventRelationHint",
    "MinorEventType",
    "MinorEventContext",
    "MinorEventResult",
]
