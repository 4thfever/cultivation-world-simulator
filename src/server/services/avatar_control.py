from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from src.i18n import t
from src.sim.avatar_init import ManualAvatarAgeLimitError


def _available_portrait_ids(avatar_assets: dict, *, race_id: str, gender_value: str) -> set[int]:
    gender_key = "female" if gender_value == "female" else "male"
    race_assets = avatar_assets.get(race_id) or avatar_assets.get("human", {})
    return set(race_assets.get(gender_key, []))


def set_long_term_objective_for_avatar(runtime, *, avatar_id: str, content: str, setter) -> dict[str, str]:
    world = runtime.get("world")
    if not world:
        raise HTTPException(status_code=503, detail=t("World not initialized"))

    avatar = world.avatar_manager.avatars.get(avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail=t("Avatar not found"))

    setter(avatar, content)
    return {"status": "ok", "message": t("Objective set")}


def clear_long_term_objective_for_avatar(runtime, *, avatar_id: str, clearer) -> dict[str, str]:
    world = runtime.get("world")
    if not world:
        raise HTTPException(status_code=503, detail=t("World not initialized"))

    avatar = world.avatar_manager.avatars.get(avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail=t("Avatar not found"))

    cleared = clearer(avatar)
    return {
        "status": "ok",
        "message": t("Objective cleared") if cleared else t("No user objective to clear"),
    }


def update_avatar_portrait_in_world(
    runtime,
    *,
    avatar_id: str,
    pic_id: int,
    avatar_assets: dict[str, list[int]],
) -> dict[str, str]:
    world = runtime.get("world")
    if not world:
        raise HTTPException(status_code=503, detail=t("World not initialized"))

    avatar = world.avatar_manager.avatars.get(avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail=t("Avatar not found"))

    available_ids = _available_portrait_ids(
        avatar_assets,
        race_id=getattr(getattr(avatar, "race", None), "id", "human"),
        gender_value=getattr(avatar.gender, "value", "male"),
    )
    if available_ids and pic_id not in available_ids:
        raise HTTPException(status_code=400, detail=t("Invalid pic_id for avatar gender"))

    avatar.custom_pic_id = pic_id
    return {"status": "ok", "message": t("Avatar portrait updated")}


def delete_avatar_in_world(runtime, *, avatar_id: str) -> dict[str, str]:
    world = runtime.get("world")
    if not world:
        raise HTTPException(status_code=503, detail=t("World not initialized"))

    if avatar_id not in world.avatar_manager.avatars:
        raise HTTPException(status_code=404, detail=t("Avatar not found"))

    session = runtime.get_roleplay_session() if hasattr(runtime, "get_roleplay_session") else None
    if _roleplay_session_references_avatar(session, avatar_id):
        raise HTTPException(
            status_code=409,
            detail=t("Finish the active roleplay before deleting this avatar"),
        )

    world.avatar_manager.remove_avatar(avatar_id)
    return {
        "status": "ok",
        "message": t("Avatar deleted"),
        "removed_avatar_id": str(avatar_id),
    }


def _roleplay_session_references_avatar(session: Any, avatar_id: str) -> bool:
    if not isinstance(session, dict):
        return False

    avatar_id = str(avatar_id)
    if str(session.get("controlled_avatar_id") or "") == avatar_id:
        return True

    for key in ("pending_request", "conversation_session"):
        value = session.get(key)
        if not isinstance(value, dict):
            continue
        if any(
            str(value.get(field) or "") == avatar_id
            for field in ("avatar_id", "target_avatar_id", "initiator_avatar_id")
        ):
            return True
    return False


def update_avatar_adjustment_in_world(
    runtime,
    *,
    avatar_id: str,
    category: str,
    target_id: int | None,
    persona_ids: list[int] | None,
    apply_avatar_adjustment,
) -> dict[str, str]:
    world = runtime.get("world")
    if not world:
        raise HTTPException(status_code=503, detail=t("World not initialized"))

    avatar = world.avatar_manager.avatars.get(avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail=t("Avatar not found"))

    apply_avatar_adjustment(
        avatar,
        category=category,
        target_id=target_id,
        persona_ids=persona_ids,
    )
    return {"status": "ok", "message": t("Avatar adjustment applied")}


def create_avatar_in_world(
    runtime,
    *,
    req,
    create_avatar_from_request,
    sects_by_id,
    uses_space_separated_names,
    language_manager,
    avatar_assets: dict[str, list[int]],
    alignment_from_str,
    get_appearance_by_level,
    resolve_avatar_pic_id,
    resolve_avatar_action_emoji,
) -> dict[str, Any]:
    world = runtime.get("world")
    if not world:
        raise HTTPException(status_code=503, detail=t("World not initialized"))

    sect = sects_by_id.get(req.sect_id) if req.sect_id is not None else None
    personas = req.persona_ids if req.persona_ids else None

    have_name = False
    final_name = None
    surname = (req.surname or "").strip()
    given_name = (req.given_name or "").strip()
    race_id = str(getattr(req, "race", None) or "human")
    if race_id != "human":
        if given_name:
            from src.utils.name_generator import get_name_with_race_surname

            final_name = get_name_with_race_surname(req.gender, race_id, given_name)
            have_name = True
    elif surname or given_name:
        if surname and given_name:
            if uses_space_separated_names(language_manager.current):
                final_name = f"{surname} {given_name}"
            else:
                final_name = f"{surname}{given_name}"
            have_name = True
        elif surname:
            final_name = f"{surname}某"
            have_name = True
        else:
            final_name = given_name
            have_name = True
    if not have_name:
        final_name = None

    try:
        avatar = create_avatar_from_request(
            world,
            world.month_stamp,
            name=final_name,
            gender=req.gender,
            age=req.age,
            level=req.level,
            sect=sect,
            personas=personas,
            technique=req.technique_id,
            weapon=req.weapon_id,
            auxiliary=req.auxiliary_id,
            appearance=req.appearance,
            race=getattr(req, "race", None),
            relations=req.relations,
        )
    except ManualAvatarAgeLimitError as exc:
        raise HTTPException(
            status_code=400,
            detail=t(
                "Age {age} exceeds the maximum {max_age} for {realm}",
                age=exc.age,
                max_age=exc.max_age,
                realm=exc.realm,
            ),
        ) from exc

    if req.pic_id is not None:
        available_ids = _available_portrait_ids(
            avatar_assets,
            race_id=getattr(getattr(avatar, "race", None), "id", "human"),
            gender_value=getattr(avatar.gender, "value", "male"),
        )
        if available_ids and req.pic_id not in available_ids:
            raise HTTPException(status_code=400, detail=t("Invalid pic_id for selected gender"))
        avatar.custom_pic_id = req.pic_id

    if req.alignment:
        avatar.alignment = alignment_from_str(req.alignment)

    if req.appearance is not None:
        avatar.appearance = get_appearance_by_level(req.appearance)

    if req.alignment:
        avatar.alignment = alignment_from_str(req.alignment)

    world.avatar_manager.register_avatar(avatar, is_newly_born=True)
    return {
        "status": "ok",
        "message": t("Created avatar {avatar_name}", avatar_name=avatar.name),
        "avatar_id": str(avatar.id),
        "avatar": {
            "id": str(getattr(avatar, "id", "no_id")),
            "name": str(getattr(avatar, "name", "no_name")),
            "x": int(getattr(avatar, "pos_x", 0)),
            "y": int(getattr(avatar, "pos_y", 0)),
            "action": str(getattr(avatar, "current_action_name", "")),
            "action_emoji": resolve_avatar_action_emoji(avatar),
            "gender": str(getattr(getattr(avatar, "gender", None), "value", "")),
            "race": getattr(getattr(avatar, "race", None), "id", "human"),
            "pic_id": resolve_avatar_pic_id(avatar),
            "realm": getattr(getattr(getattr(avatar, "cultivation_progress", None), "realm", None), "value", ""),
            "is_dead": bool(getattr(avatar, "is_dead", False)),
        },
    }
