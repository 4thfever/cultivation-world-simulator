from __future__ import annotations

from typing import Any, Callable


def build_avatar_detail(
    avatar: Any,
    *,
    resolve_avatar_pic_id: Callable[[Any], int],
) -> dict[str, Any]:
    info = avatar.get_structured_info()
    info["pic_id"] = resolve_avatar_pic_id(avatar)
    info["realm_id"] = avatar.cultivation_progress.realm.value
    return info
