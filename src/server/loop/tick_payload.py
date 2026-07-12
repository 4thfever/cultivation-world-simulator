from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(slots=True)
class TickPayloadBuilder:
    build_avatar_updates: Callable[[], list[dict[str, Any]]]
    build_tick_state: Callable[[list[dict[str, Any]], list[Any], Any], dict[str, Any]]

    def build(self, *, events: list[Any], world: Any) -> dict[str, Any]:
        avatar_updates = self.build_avatar_updates()
        return self.build_tick_state(avatar_updates, events, world)
