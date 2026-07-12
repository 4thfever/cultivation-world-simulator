from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class RoleplayStatus(StrEnum):
    INACTIVE = "inactive"
    OBSERVING = "observing"
    AWAITING_DECISION = "awaiting_decision"
    AWAITING_CHOICE = "awaiting_choice"
    CONVERSING = "conversing"
    SUBMITTING = "submitting"


@dataclass(slots=True)
class RoleplaySession:
    controlled_avatar_id: str | None = None
    status: RoleplayStatus = RoleplayStatus.INACTIVE
    pending_request: dict[str, Any] | None = None
    last_prompt_context: dict[str, Any] | None = None
    conversation_session: dict[str, Any] | None = None
    interaction_history: list[dict[str, Any]] = field(default_factory=list)

    def to_runtime_dict(self) -> dict[str, Any]:
        return {
            "controlled_avatar_id": self.controlled_avatar_id,
            "status": self.status.value,
            "pending_request": self.pending_request,
            "last_prompt_context": self.last_prompt_context,
            "conversation_session": self.conversation_session,
            "interaction_history": list(self.interaction_history),
        }


def create_roleplay_session_dict() -> dict[str, Any]:
    return RoleplaySession().to_runtime_dict()
