from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class CancellationToken:
    runtime: Any

    def is_cancelled(self) -> bool:
        return bool(getattr(self.runtime, "is_reset_requested", lambda: False)())


@dataclass(slots=True)
class RuntimePauseController:
    runtime: Any

    def set_roleplay_paused(self, paused: bool) -> None:
        self.runtime.set_roleplay_auto_paused(paused)

    def is_effectively_paused(self) -> bool:
        return bool(self.runtime.is_effectively_paused())


@dataclass(slots=True)
class RoleplayDecisionGateway:
    runtime: Any

    def get_session(self) -> dict[str, Any]:
        return self.runtime.get_roleplay_session()

    def get_controlled_avatar_id(self) -> str:
        return str(self.get_session().get("controlled_avatar_id") or "")

    def controls_avatar(self, avatar_id: str) -> bool:
        return self.get_controlled_avatar_id() == str(avatar_id)

    def clear_session(self) -> None:
        self.runtime.clear_roleplay_session()


def get_roleplay_gateway_from_world(world: Any) -> RoleplayDecisionGateway | None:
    runtime = getattr(world, "runtime", None)
    if runtime is None or not hasattr(runtime, "get_roleplay_session"):
        return None
    return RoleplayDecisionGateway(runtime)
