from __future__ import annotations

import time
from typing import Any


MAX_INTERACTION_HISTORY = 24


def append_interaction_history(
    runtime,
    record: dict[str, Any],
    *,
    max_items: int = MAX_INTERACTION_HISTORY,
) -> None:
    session = runtime.get_roleplay_session()
    history = session.get("interaction_history")
    if not isinstance(history, list):
        history = []
        session["interaction_history"] = history

    history.append({"created_at": time.time(), **record})
    if len(history) > max_items:
        del history[:-max_items]
