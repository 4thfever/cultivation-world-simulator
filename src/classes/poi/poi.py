from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(kw_only=True)
class PointOfInterest(ABC):
    id: str
    kind: str
    x: int
    y: int
    name: str
    desc: str = ""
    created_month: int = 0
    expires_month: int | None = None
    discovered_by: set[str] = field(default_factory=set)
    icon_key: str = ""
    is_clickable: bool = True

    @property
    def loc(self) -> tuple[int, int]:
        return self.x, self.y

    def is_expired(self, current_month: int) -> bool:
        return self.expires_month is not None and int(current_month) >= int(self.expires_month)

    def is_discoverable_by(self, avatar: Any) -> bool:
        return True

    def discover(self, avatar: Any) -> bool:
        avatar_id = str(getattr(avatar, "id", "") or "")
        if not avatar_id or avatar_id in self.discovered_by:
            return False
        self.discovered_by.add(avatar_id)
        return True

    def is_known_by(self, avatar: Any) -> bool:
        return str(getattr(avatar, "id", "") or "") in self.discovered_by

    def get_summary_payload(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "name": self.name,
            "x": int(self.x),
            "y": int(self.y),
            "icon_key": self.icon_key,
            "clickable": bool(self.is_clickable),
        }

    def _base_save_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "id": self.id,
            "kind": self.kind,
            "x": int(self.x),
            "y": int(self.y),
            "name": self.name,
            "desc": self.desc,
            "created_month": int(self.created_month),
            "expires_month": int(self.expires_month) if self.expires_month is not None else None,
            "discovered_by": sorted(self.discovered_by),
            "icon_key": self.icon_key,
            "is_clickable": bool(self.is_clickable),
        }

    @abstractmethod
    def get_detail_payload(self, world: Any) -> dict[str, Any]:
        ...

    @abstractmethod
    def to_save_dict(self) -> dict[str, Any]:
        ...
