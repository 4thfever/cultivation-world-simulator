from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


BACKGROUND_NPC_EVENT_TYPE = "background_npc"


class BackgroundNpcTriggerKind(StrEnum):
    REGION_TICK = "region_tick"
    AVATAR_WITNESS = "avatar_witness"
    ACTION_ECHO = "action_echo"


@dataclass(frozen=True)
class BackgroundNpcProfile:
    id: int
    profile_key: str
    role_label_id: str
    category: str
    default_scene_tags: tuple[str, ...]


@dataclass(frozen=True)
class BackgroundNpcEventType:
    id: int
    event_key: str
    profile_key: str
    trigger_kind: BackgroundNpcTriggerKind
    region_types: tuple[str, ...]
    required_tags: tuple[str, ...]
    excluded_tags: tuple[str, ...]
    map_ids: tuple[str, ...]
    avatar_filters: dict[str, str]
    action_keys: tuple[str, ...]
    weight: float
    cooldown_months: int
    max_per_month: int
    text_id: str


@dataclass(frozen=True)
class BackgroundNpcRegionBinding:
    id: int
    map_id: str
    region_id: int
    scene_tags: tuple[str, ...]


@dataclass(frozen=True)
class BackgroundNpcContext:
    event_type: BackgroundNpcEventType
    profile: BackgroundNpcProfile
    region: object | None
    avatar: object | None = None
    action_key: str | None = None
    sect_name: str | None = None
    dynasty_title: str | None = None


__all__ = [
    "BACKGROUND_NPC_EVENT_TYPE",
    "BackgroundNpcContext",
    "BackgroundNpcEventType",
    "BackgroundNpcProfile",
    "BackgroundNpcRegionBinding",
    "BackgroundNpcTriggerKind",
]
