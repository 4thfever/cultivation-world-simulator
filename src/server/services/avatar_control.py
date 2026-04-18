from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from src.i18n import t


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

    gender_key = "females" if getattr(avatar.gender, "value", "male") == "female" else "males"
    available_ids = set(avatar_assets.get(gender_key, []))
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

    world.avatar_manager.remove_avatar(avatar_id)
    return {"status": "ok", "message": t("Avatar deleted")}


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
) -> dict[str, str]:
    world = runtime.get("world")
    if not world:
        raise HTTPException(status_code=503, detail=t("World not initialized"))

    sect = sects_by_id.get(req.sect_id) if req.sect_id is not None else None
    personas = req.persona_ids if req.persona_ids else None

    have_name = False
    final_name = None
    surname = (req.surname or "").strip()
    given_name = (req.given_name or "").strip()
    if surname or given_name:
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
        relations=req.relations,
    )

    if req.pic_id is not None:
        gender_key = "females" if getattr(avatar.gender, "value", "male") == "female" else "males"
        available_ids = set(avatar_assets.get(gender_key, []))
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
    }
