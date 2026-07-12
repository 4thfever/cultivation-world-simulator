from __future__ import annotations

from typing import Any

from src.i18n import t
from src.systems.cultivation_display import build_avatar_cultivation_display


def build_avatar_list_item(avatar: Any) -> dict[str, Any]:
    sect_name = avatar.sect.name if avatar.sect else t("Rogue Cultivator")
    realm_str = avatar.cultivation_progress.realm.value if hasattr(avatar, "cultivation_progress") else t("Unknown")
    cultivation_display = build_avatar_cultivation_display(avatar) if hasattr(avatar, "cultivation_progress") else None
    return {
        "id": str(avatar.id),
        "name": avatar.name,
        "sect_name": sect_name,
        "realm": realm_str,
        "cultivation": cultivation_display,
        "cultivation_display": cultivation_display["display_full_name"] if cultivation_display else "",
        "gender": str(avatar.gender),
        "race": getattr(getattr(avatar, "race", None), "id", "human"),
        "age": avatar.age.age,
    }


def build_avatar_list_payload(world: Any) -> dict[str, Any]:
    avatars = [
        build_avatar_list_item(avatar)
        for avatar in world.avatar_manager.avatars.values()
    ]
    avatars.sort(key=lambda item: item["name"])
    return {"avatars": avatars}
