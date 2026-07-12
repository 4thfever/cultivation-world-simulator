from __future__ import annotations

from typing import Any


def build_prompt_context(avatar) -> dict[str, Any]:
    world = avatar.world
    observed = world.get_observable_avatars(avatar)
    return {
        "avatar_id": str(avatar.id),
        "avatar_name": avatar.name,
        "current_action": avatar.current_action_name,
        "short_term_objective": str(getattr(avatar, "short_term_objective", "") or ""),
        "thinking": str(getattr(avatar, "thinking", "") or ""),
        "recent_major_events": [
            str(getattr(ev, "content", "")) for ev in world.event_manager.get_major_events_by_avatar(avatar.id, limit=4)
        ],
        "recent_events": [
            str(getattr(ev, "content", "")) for ev in world.event_manager.get_minor_events_by_avatar(avatar.id, limit=6)
        ],
        "nearby_avatars": [
            {
                "id": str(getattr(other, "id", "")),
                "name": str(getattr(other, "name", "") or ""),
                "realm": str(getattr(getattr(other, "cultivation_progress", None), "get_info", lambda: "")()),
            }
            for other in observed[:8]
        ],
    }
