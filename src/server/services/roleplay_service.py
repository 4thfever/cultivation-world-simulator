from __future__ import annotations

import asyncio
import time
from typing import Any

from fastapi import HTTPException

from src.classes.actions import get_action_infos_str
from src.classes.core.avatar.info_presenter import get_avatar_ai_context
from src.classes.emotions import EmotionType
from src.utils.config import CONFIG
from src.utils.llm import call_llm_with_task_name


def get_roleplay_session(runtime) -> dict[str, Any]:
    raw_session = runtime.get_roleplay_session()
    session = {key: value for key, value in raw_session.items() if not str(key).startswith("_")}
    pending = session.get("pending_request")
    if isinstance(pending, dict):
        session["pending_request"] = dict(pending)
    return session


def clear_roleplay_session(runtime) -> None:
    runtime.clear_roleplay_session()


def is_player_controlled_choice_target(*, avatar) -> bool:
    runtime = getattr(getattr(avatar, "world", None), "runtime", None)
    if runtime is None or not hasattr(runtime, "get_roleplay_session"):
        return False
    session = runtime.get_roleplay_session()
    return str(session.get("controlled_avatar_id") or "") == str(getattr(avatar, "id", ""))


def _require_world(runtime):
    world = runtime.get("world")
    if world is None:
        raise HTTPException(status_code=503, detail="World not initialized")
    return world


def _find_avatar_or_raise(world, avatar_id: str):
    avatar = world.avatar_manager.get_avatar(avatar_id)
    if avatar is None:
        raise HTTPException(status_code=404, detail="Avatar not found")
    return avatar


def _make_pending_decision_request(*, avatar) -> dict[str, Any]:
    return {
        "request_id": f"roleplay-decision-{avatar.id}-{int(time.time() * 1000)}",
        "type": "decision",
        "avatar_id": str(avatar.id),
        "title": f"{avatar.name} 需要新的指令",
        "description": "世界已暂停，正在等待你的扮演指令。",
        "created_at": time.time(),
    }


def _make_pending_choice_request(
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


def _set_observing(runtime, *, avatar_id: str, prompt_context: dict[str, Any] | None = None) -> dict[str, Any]:
    session = runtime.get_roleplay_session()
    session["controlled_avatar_id"] = str(avatar_id)
    session["status"] = "observing"
    session["pending_request"] = None
    session["last_prompt_context"] = prompt_context
    session.pop("_choice_future", None)
    session.pop("_choice_request_model", None)
    runtime.set_roleplay_auto_paused(False)
    return dict(session)


def finish_roleplay_choice_wait(runtime, *, avatar_id: str, selected_key: str | None = None) -> dict[str, Any]:
    session = runtime.get_roleplay_session()
    if str(session.get("status") or "") == "inactive":
        return dict(session)
    if str(session.get("controlled_avatar_id") or "") not in ("", str(avatar_id)):
        return dict(session)
    prompt_context = {
        **(session.get("last_prompt_context") or {}),
    }
    if selected_key is not None:
        prompt_context["last_selected_key"] = str(selected_key)
    return _set_observing(runtime, avatar_id=avatar_id, prompt_context=prompt_context)


def _set_waiting_decision(runtime, *, avatar, prompt_context: dict[str, Any]) -> dict[str, Any]:
    session = runtime.get_roleplay_session()
    session["controlled_avatar_id"] = str(avatar.id)
    session["status"] = "awaiting_decision"
    session["pending_request"] = _make_pending_decision_request(avatar=avatar)
    session["last_prompt_context"] = prompt_context
    runtime.set_roleplay_auto_paused(True)
    return dict(session)


def begin_roleplay_choice(
    runtime,
    *,
    request,
) -> asyncio.Future:
    avatar = request.avatar
    session = runtime.get_roleplay_session()
    pending = session.get("pending_request")
    if pending is not None:
        raise HTTPException(status_code=409, detail="Another roleplay request is already pending")

    request_id = str(getattr(request, "request_id", "") or f"roleplay-choice-{avatar.id}-{int(time.time() * 1000)}")
    request.request_id = request_id
    request_title = str(getattr(request, "title", "") or f"{avatar.name} 需要做出选择")
    request_description = str(getattr(request, "description", "") or getattr(request, "situation", "") or "")
    options = [
        {
            "key": str(option.key),
            "title": str(option.title),
            "description": str(option.description),
        }
        for option in getattr(request, "options", [])
    ]
    prompt_context = {
        **_build_prompt_context(avatar),
        "choice_title": request_title,
        "choice_description": request_description,
    }
    choice_future = asyncio.get_running_loop().create_future()
    session["controlled_avatar_id"] = str(avatar.id)
    session["status"] = "awaiting_choice"
    session["pending_request"] = _make_pending_choice_request(
        avatar=avatar,
        request_id=request_id,
        title=request_title,
        description=request_description,
        options=options,
    )
    session["last_prompt_context"] = prompt_context
    session["_choice_future"] = choice_future
    session["_choice_request_model"] = request
    runtime.set_roleplay_auto_paused(True)
    return choice_future


def _build_prompt_context(avatar) -> dict[str, Any]:
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


def start_roleplay(runtime, *, avatar_id: str) -> dict[str, Any]:
    world = _require_world(runtime)
    avatar = _find_avatar_or_raise(world, avatar_id)
    session = runtime.get_roleplay_session()
    current_avatar_id = session.get("controlled_avatar_id")
    if current_avatar_id and str(current_avatar_id) != str(avatar_id):
        raise HTTPException(status_code=409, detail="Another avatar is already under roleplay control")

    prompt_context = _build_prompt_context(avatar)
    if avatar.current_action is None and not avatar.has_plans():
        return _set_waiting_decision(runtime, avatar=avatar, prompt_context=prompt_context)
    return _set_observing(runtime, avatar_id=str(avatar.id), prompt_context=prompt_context)


def stop_roleplay(runtime, *, avatar_id: str | None = None) -> dict[str, Any]:
    session = runtime.get_roleplay_session()
    current_avatar_id = session.get("controlled_avatar_id")
    if avatar_id and current_avatar_id and str(current_avatar_id) != str(avatar_id):
        raise HTTPException(status_code=409, detail="Roleplay target mismatch")
    runtime.clear_roleplay_session()
    return get_roleplay_session(runtime)


def maybe_request_roleplay_decision(world) -> bool:
    runtime = getattr(world, "runtime", None)
    if runtime is None:
        return False

    session = runtime.get_roleplay_session()
    controlled_avatar_id = session.get("controlled_avatar_id")
    if not controlled_avatar_id or str(session.get("status", "")) == "awaiting_decision":
        return False

    avatar = world.avatar_manager.get_avatar(str(controlled_avatar_id))
    if avatar is None or getattr(avatar, "is_dead", False):
        runtime.clear_roleplay_session()
        return False

    if avatar.current_action is None and not avatar.has_plans():
        _set_waiting_decision(runtime, avatar=avatar, prompt_context=_build_prompt_context(avatar))
        return True

    return False


async def submit_roleplay_decision(runtime, *, avatar_id: str, request_id: str, command_text: str) -> dict[str, Any]:
    world = _require_world(runtime)
    avatar = _find_avatar_or_raise(world, avatar_id)
    session = runtime.get_roleplay_session()
    pending = session.get("pending_request") or {}

    if str(session.get("controlled_avatar_id") or "") != str(avatar_id):
        raise HTTPException(status_code=409, detail="Roleplay target mismatch")
    if str(session.get("status") or "") != "awaiting_decision":
        raise HTTPException(status_code=409, detail="Roleplay is not waiting for a decision")
    if str(pending.get("request_id") or "") != str(request_id):
        raise HTTPException(status_code=404, detail="Roleplay request not found")
    if not str(command_text or "").strip():
        raise HTTPException(status_code=400, detail="Roleplay command text is required")

    session["status"] = "submitting"
    command_text = str(command_text).strip()

    observed = world.get_observable_avatars(avatar)
    info = {
        "avatar_name": avatar.name,
        "avatar_info": avatar.get_expanded_info(co_region_avatars=observed, detailed=True),
        "avatar_ai_context": {
            **get_avatar_ai_context(avatar, co_region_avatars=observed),
            "player_command": command_text,
            "decision_mode": "player_roleplay",
        },
        "world_info": world.get_info(avatar=avatar, detailed=True),
        "world_lore": world.world_lore.text,
        "general_action_infos": get_action_infos_str(avatar),
        "player_command": command_text,
    }
    template_path = CONFIG.paths.templates / "ai.txt"
    response = await call_llm_with_task_name("action_decision", template_path, info)
    payload = response.get(avatar.name, {}) if isinstance(response, dict) else {}
    raw_pairs = payload.get("action_name_params_pairs", [])
    pairs = []
    for item in raw_pairs:
        if isinstance(item, list) and len(item) == 2:
            pairs.append((item[0], item[1] or {}))
        elif isinstance(item, dict) and "action_name" in item and "action_params" in item:
            pairs.append((item["action_name"], item["action_params"] or {}))

    if not pairs:
        session["status"] = "awaiting_decision"
        runtime.set_roleplay_auto_paused(True)
        raise HTTPException(status_code=422, detail="No valid action plan generated from roleplay command")

    avatar_thinking = str(payload.get("avatar_thinking", payload.get("thinking", "")) or command_text)
    short_term_objective = str(payload.get("short_term_objective", "") or command_text)
    raw_emotion = str(payload.get("current_emotion", "") or "")
    try:
        avatar.emotion = EmotionType(raw_emotion)
    except ValueError:
        pass

    avatar.load_decide_result_chain(pairs, avatar_thinking, short_term_objective)
    _set_observing(
        runtime,
        avatar_id=str(avatar.id),
        prompt_context={
            **_build_prompt_context(avatar),
            "last_player_command": command_text,
        },
    )
    return {
        "status": "ok",
        "message": "扮演指令已提交",
        "planned_action_count": len(pairs),
    }


async def submit_roleplay_choice(runtime, *, avatar_id: str, request_id: str, selected_key: str) -> dict[str, Any]:
    world = _require_world(runtime)
    _find_avatar_or_raise(world, avatar_id)
    session = runtime.get_roleplay_session()
    pending = session.get("pending_request") or {}

    if str(session.get("controlled_avatar_id") or "") != str(avatar_id):
        raise HTTPException(status_code=409, detail="Roleplay target mismatch")
    if str(session.get("status") or "") != "awaiting_choice":
        raise HTTPException(status_code=409, detail="Roleplay is not waiting for a choice")
    if str(pending.get("request_id") or "") != str(request_id):
        raise HTTPException(status_code=404, detail="Roleplay request not found")

    choice_future = session.get("_choice_future")
    if choice_future is None:
        raise HTTPException(status_code=409, detail="Roleplay choice future not available")
    if hasattr(choice_future, "done") and choice_future.done():
        raise HTTPException(status_code=409, detail="Roleplay choice request already resolved")

    session["status"] = "submitting"
    choice_future.set_result(str(selected_key))
    return {
        "status": "ok",
        "message": "扮演选择已提交",
        "selected_key": str(selected_key),
    }
