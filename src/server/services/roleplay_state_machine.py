from __future__ import annotations

import time
from typing import Any

from fastapi import HTTPException

from src.i18n import t
from src.server.services.roleplay_state import RoleplayStatus


def ensure_no_pending_request(session: dict[str, Any]) -> None:
    if session.get("pending_request") is not None:
        raise HTTPException(status_code=409, detail=t("There is already a pending roleplay request"))


def make_pending_decision_request(*, avatar) -> dict[str, Any]:
    return {
        "request_id": f"roleplay-decision-{avatar.id}-{int(time.time() * 1000)}",
        "type": "decision",
        "avatar_id": str(avatar.id),
        "title": t("{avatar_name} needs a new command", avatar_name=avatar.name),
        "description": t("World paused and waiting for your roleplay command."),
        "created_at": time.time(),
    }


def make_pending_choice_request(
    *,
    avatar,
    request_id: str,
    title: str,
    description: str,
    options: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "request_id": request_id,
        "type": "choice",
        "avatar_id": str(avatar.id),
        "title": title,
        "description": description,
        "options": options,
        "created_at": time.time(),
    }


def make_pending_conversation_request(
    *,
    avatar,
    target_avatar,
    request_id: str,
    title: str,
    description: str,
    messages: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "request_id": request_id,
        "type": "conversation",
        "avatar_id": str(avatar.id),
        "target_avatar_id": str(target_avatar.id),
        "title": title,
        "description": description,
        "messages": list(messages),
        "can_end": True,
        "created_at": time.time(),
    }


def set_observing(
    runtime,
    *,
    avatar_id: str,
    prompt_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    session = runtime.get_roleplay_session()
    session["controlled_avatar_id"] = str(avatar_id)
    session["status"] = RoleplayStatus.OBSERVING.value
    session["pending_request"] = None
    session["last_prompt_context"] = prompt_context
    session.pop("_choice_future", None)
    session.pop("_choice_request_model", None)
    runtime.set_roleplay_auto_paused(False)
    return dict(session)


def set_waiting_decision(runtime, *, avatar, prompt_context: dict[str, Any]) -> dict[str, Any]:
    session = runtime.get_roleplay_session()
    session["controlled_avatar_id"] = str(avatar.id)
    session["status"] = RoleplayStatus.AWAITING_DECISION.value
    session["pending_request"] = make_pending_decision_request(avatar=avatar)
    session["last_prompt_context"] = prompt_context
    runtime.set_roleplay_auto_paused(True)
    return dict(session)


def set_awaiting_choice(
    runtime,
    *,
    avatar,
    request_id: str,
    title: str,
    description: str,
    options: list[dict[str, Any]],
    prompt_context: dict[str, Any],
    choice_future: Any,
    request_model: Any,
) -> dict[str, Any]:
    session = runtime.get_roleplay_session()
    session["controlled_avatar_id"] = str(avatar.id)
    session["status"] = RoleplayStatus.AWAITING_CHOICE.value
    session["pending_request"] = make_pending_choice_request(
        avatar=avatar,
        request_id=request_id,
        title=title,
        description=description,
        options=options,
    )
    session["last_prompt_context"] = prompt_context
    session["_choice_future"] = choice_future
    session["_choice_request_model"] = request_model
    runtime.set_roleplay_auto_paused(True)
    return dict(session)


def set_conversing(
    runtime,
    *,
    avatar,
    target_avatar,
    request_id: str,
    title: str,
    description: str,
    messages: list[dict[str, Any]],
    prompt_context: dict[str, Any],
) -> dict[str, Any]:
    session = runtime.get_roleplay_session()
    session["controlled_avatar_id"] = str(avatar.id)
    session["status"] = RoleplayStatus.CONVERSING.value
    session["pending_request"] = make_pending_conversation_request(
        avatar=avatar,
        target_avatar=target_avatar,
        request_id=request_id,
        title=title,
        description=description,
        messages=messages,
    )
    session["last_prompt_context"] = prompt_context
    session["conversation_session"] = {
        "session_id": request_id,
        "request_id": request_id,
        "avatar_id": str(avatar.id),
        "target_avatar_id": str(target_avatar.id),
        "initiator_avatar_id": str(avatar.id),
        "status": "awaiting_player",
        "messages": messages,
        "started_at": time.time(),
        "last_summary": None,
        "last_ai_thinking": "",
    }
    runtime.set_roleplay_auto_paused(True)
    return dict(session)


def set_submitting(session: dict[str, Any]) -> None:
    session["status"] = RoleplayStatus.SUBMITTING.value


def require_status(session: dict[str, Any], expected: RoleplayStatus, detail: str) -> None:
    if str(session.get("status") or "") != expected.value:
        raise HTTPException(status_code=409, detail=t(detail))


def require_controlled_avatar(session: dict[str, Any], avatar_id: str) -> None:
    if str(session.get("controlled_avatar_id") or "") != str(avatar_id):
        raise HTTPException(status_code=409, detail=t("Roleplay target does not match"))


def require_pending_request(pending: dict[str, Any], request_id: str, detail: str) -> None:
    if str(pending.get("request_id") or "") != str(request_id):
        raise HTTPException(status_code=404, detail=t(detail))
