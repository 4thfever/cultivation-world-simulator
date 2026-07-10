from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


DISCLOSURE_SHARE_ALL = "share_all"
DISCLOSURE_KEEP_SECRET = "keep_secret"
WORLD_SECRET_NONE_ID = "none"
WORLD_SECRET_RANDOM_ID = "random"


@dataclass(slots=True)
class WorldSecretFragment:
    id: str
    secret_id: str
    order: int
    angle: str
    text: str
    trigger_kind: str


@dataclass(slots=True)
class WorldSecretDefinition:
    id: str
    title: str
    secret: str
    weight: float
    fragments: list[WorldSecretFragment] = field(default_factory=list)


@dataclass(slots=True)
class WorldSecretTriggerBinding:
    fragment_id: str
    trigger_kind: str
    region_id: int | None = None
    city_region_id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "fragment_id": self.fragment_id,
            "trigger_kind": self.trigger_kind,
            "region_id": self.region_id,
            "city_region_id": self.city_region_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "WorldSecretTriggerBinding | None":
        if not isinstance(data, dict):
            return None
        fragment_id = str(data.get("fragment_id", "") or "")
        trigger_kind = str(data.get("trigger_kind", "") or "")
        if not fragment_id or not trigger_kind:
            return None

        def _optional_int(value: Any) -> int | None:
            if value is None:
                return None
            try:
                return int(value)
            except (TypeError, ValueError):
                return None

        return cls(
            fragment_id=fragment_id,
            trigger_kind=trigger_kind,
            region_id=_optional_int(data.get("region_id")),
            city_region_id=_optional_int(data.get("city_region_id")),
        )


@dataclass(slots=True)
class WorldSecretRuntime:
    selected_secret_id: str = WORLD_SECRET_NONE_ID
    trigger_bindings: dict[str, WorldSecretTriggerBinding] = field(default_factory=dict)
    resolved_by_avatar_ids: set[str] = field(default_factory=set)
    disclosure_decisions: dict[str, str] = field(default_factory=dict)
    public_revealed: bool = False
    public_revealed_month: int | None = None
    public_revealed_by_avatar_id: str | None = None

    def is_enabled(self) -> bool:
        return bool(self.selected_secret_id and self.selected_secret_id != WORLD_SECRET_NONE_ID)

    def to_dict(self) -> dict[str, Any]:
        return {
            "selected_secret_id": self.selected_secret_id,
            "trigger_bindings": {
                fragment_id: binding.to_dict()
                for fragment_id, binding in self.trigger_bindings.items()
            },
            "resolved_by_avatar_ids": sorted(self.resolved_by_avatar_ids),
            "disclosure_decisions": dict(self.disclosure_decisions),
            "public_revealed": bool(self.public_revealed),
            "public_revealed_month": self.public_revealed_month,
            "public_revealed_by_avatar_id": self.public_revealed_by_avatar_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "WorldSecretRuntime":
        if not isinstance(data, dict):
            return cls()

        bindings: dict[str, WorldSecretTriggerBinding] = {}
        raw_bindings = data.get("trigger_bindings", {}) or {}
        if isinstance(raw_bindings, dict):
            for key, value in raw_bindings.items():
                binding = WorldSecretTriggerBinding.from_dict(value)
                if binding is not None:
                    bindings[str(key)] = binding

        public_month = data.get("public_revealed_month")
        try:
            public_month_int = int(public_month) if public_month is not None else None
        except (TypeError, ValueError):
            public_month_int = None

        return cls(
            selected_secret_id=str(data.get("selected_secret_id", WORLD_SECRET_NONE_ID) or WORLD_SECRET_NONE_ID),
            trigger_bindings=bindings,
            resolved_by_avatar_ids={str(item) for item in (data.get("resolved_by_avatar_ids", []) or [])},
            disclosure_decisions={
                str(key): str(value)
                for key, value in (data.get("disclosure_decisions", {}) or {}).items()
            },
            public_revealed=bool(data.get("public_revealed", False)),
            public_revealed_month=public_month_int,
            public_revealed_by_avatar_id=(
                str(data.get("public_revealed_by_avatar_id"))
                if data.get("public_revealed_by_avatar_id") is not None
                else None
            ),
        )


@dataclass(slots=True)
class AvatarWorldSecretKnowledge:
    secret_id: str
    known_fragment_ids: set[str] = field(default_factory=set)
    knows_full_secret: bool = False
    full_secret_month: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "known_fragment_ids": sorted(self.known_fragment_ids),
            "knows_full_secret": bool(self.knows_full_secret),
            "full_secret_month": self.full_secret_month,
        }

    @classmethod
    def from_dict(cls, secret_id: str, data: dict[str, Any] | None) -> "AvatarWorldSecretKnowledge":
        data = data if isinstance(data, dict) else {}
        raw_month = data.get("full_secret_month")
        try:
            full_secret_month = int(raw_month) if raw_month is not None else None
        except (TypeError, ValueError):
            full_secret_month = None
        return cls(
            secret_id=str(secret_id),
            known_fragment_ids={str(item) for item in (data.get("known_fragment_ids", []) or [])},
            knows_full_secret=bool(data.get("knows_full_secret", False)),
            full_secret_month=full_secret_month,
        )


def serialize_avatar_world_secret_knowledge(avatar: Any) -> dict[str, dict[str, Any]]:
    knowledge = getattr(avatar, "world_secret_knowledge", {}) or {}
    result: dict[str, dict[str, Any]] = {}
    for secret_id, item in knowledge.items():
        if isinstance(item, AvatarWorldSecretKnowledge):
            result[str(secret_id)] = item.to_dict()
        elif isinstance(item, dict):
            result[str(secret_id)] = AvatarWorldSecretKnowledge.from_dict(str(secret_id), item).to_dict()
    return result


def deserialize_avatar_world_secret_knowledge(data: dict[str, Any] | None) -> dict[str, AvatarWorldSecretKnowledge]:
    result: dict[str, AvatarWorldSecretKnowledge] = {}
    if not isinstance(data, dict):
        return result
    for secret_id, item in data.items():
        result[str(secret_id)] = AvatarWorldSecretKnowledge.from_dict(str(secret_id), item)
    return result
