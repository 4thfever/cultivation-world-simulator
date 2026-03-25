from __future__ import annotations

from dataclasses import dataclass, field
import time
import uuid


@dataclass
class EventObservation:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_id: str = ""
    observer_avatar_id: str = ""
    subject_avatar_id: str | None = None
    propagation_kind: str = "self_direct"
    relation_type: str | None = None
    created_at: float = field(default_factory=time.time)
