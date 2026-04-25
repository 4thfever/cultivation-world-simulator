from __future__ import annotations

import asyncio
import time
from typing import Any

from fastapi import HTTPException

from src.classes.emotions import EmotionType
from src.i18n import t
from src.server.services.roleplay_action_display import build_roleplay_action_chain_display
from src.utils.config import CONFIG
from src.utils.llm import call_llm_with_task_name
from src.utils.strings import to_json_str_with_intent


_MAX_INTERACTION_HISTORY = 24


def get_roleplay_session(runtime) -> dict[str, Any]:
    raw_session = runtime.get_roleplay_session()
    session = {key: value for key, value in raw_session.items() if not str(key).startswith("_")}
    pending = session.get("pending_request")
    if isinstance(pending, dict):
        session["pending_request"] = dict(pending)
    conversation_session = session.get("conversation_session")
    if isinstance(conversation_session, dict):
        session["conversation_session"] = dict(conversation_session)
    history = session.get("interaction_history")
    if isinstance(history, list):
        copied_history: list[dict[str, Any]] = []
        for item in history:
            if not isinstance(item, dict):
                continue
            copied_item = dict(item)
            actions = copied_item.get("actions")
            if isinstance(actions, list):
                copied_item["actions"] = [
                    {
                        **dict(action),
                        "tokens": [dict(token) for token in action.get("tokens", []) if isinstance(token, dict)],
                    }
                    for action in actions
                    if isinstance(action, dict)
                ]
            copied_history.append(copied_item)
        session["interaction_history"] = copied_history
    return session


def _append_interaction_history(runtime, record: dict[str, Any]) -> None:
    session = runtime.get_roleplay_session()
    history = session.get("interaction_history")
    if not isinstance(history, list):
        history = []
        session["interaction_history"] = history

    history.append({"created_at": time.time(), **record})
    if len(history) > _MAX_INTERACTION_HISTORY:
        del history[:-_MAX_INTERACTION_HISTORY]


def _find_choice_option_text(pending: dict[str, Any], selected_key: str) -> str:
    options = pending.get("options")
    if isinstance(options, list):
        for option in options:
            if not isinstance(option, dict):
                continue
            if str(option.get("key") or "") != str(selected_key):
                continue
            title = str(option.get("title") or "").strip()
            description = str(option.get("description") or "").strip()
            if title and description:
                return f"{title}：{description}"
            if title:
                return title
            if description:
                return description
    return str(selected_key)


def _build_choice_prompt_text(*, title: str, description: str) -> str:
    clean_title = str(title or "").strip()
    clean_description = str(description or "").strip()
    if clean_description:
        return clean_description
    return clean_title


def _get_choice_option_variant(option) -> str:
    metadata = getattr(option, "metadata", None)
    if not isinstance(metadata, dict):
        return "default"
    raw_variant = str(metadata.get("display_variant") or metadata.get("variant") or "").strip().lower()
    if raw_variant in {"accept", "reject", "default"}:
        return raw_variant
    return "default"


def clear_roleplay_session(runtime) -> None:
    runtime.clear_roleplay_session()


def is_player_controlled_choice_target(*, avatar) -> bool:
    return is_player_controlled_avatar(avatar=avatar)


def is_player_controlled_avatar(*, avatar) -> bool:
    runtime = getattr(getattr(avatar, "world", None), "runtime", None)
    if runtime is None or not hasattr(runtime, "get_roleplay_session"):
        return False
    session = runtime.get_roleplay_session()
    return str(session.get("controlled_avatar_id") or "") == str(getattr(avatar, "id", ""))


def _require_world(runtime):
    world = runtime.get("world")
    if world is None:
        raise HTTPException(status_code=503, detail=t("World is not initialized yet"))
    return world


def _find_avatar_or_raise(world, avatar_id: str):
    avatar = world.avatar_manager.get_avatar(avatar_id)
    if avatar is None:
        raise HTTPException(status_code=404, detail=t("Target avatar does not exist"))
    return avatar


def _make_pending_decision_request(*, avatar) -> dict[str, Any]:
    return {
        "request_id": f"roleplay-decision-{avatar.id}-{int(time.time() * 1000)}",
        "type": "decision",
        "avatar_id": str(avatar.id),
        "title": t("{avatar_name} needs a new command", avatar_name=avatar.name),
        "description": t("World paused and waiting for your roleplay command."),
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


def _make_pending_conversation_request(
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
        raise HTTPException(status_code=409, detail=t("There is already a pending roleplay request"))

    request_id = str(getattr(request, "request_id", "") or f"roleplay-choice-{avatar.id}-{int(time.time() * 1000)}")
    request.request_id = request_id
    request_title = str(getattr(request, "title", "") or t("{avatar_name} needs to make a choice", avatar_name=avatar.name))
    request_description = str(getattr(request, "description", "") or getattr(request, "situation", "") or "")
    options = [
        {
            "key": str(option.key),
            "title": str(option.title),
            "description": str(option.description),
            "variant": _get_choice_option_variant(option),
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
    choice_prompt_text = _build_choice_prompt_text(title=request_title, description=request_description)
    if choice_prompt_text:
        _append_interaction_history(
            runtime,
            {
                "type": "choice_prompt",
                "text": choice_prompt_text,
            },
        )
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


def _build_conversation_history_payload(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for item in messages[-12:]:
        payload.append(
            {
                "role": str(item.get("role", "")),
                "speaker_name": str(item.get("speaker_name", "")),
                "content": str(item.get("content", "")),
            }
        )
    return payload


def _build_fallback_conversation_reply(*, target_avatar, last_player_message: str) -> tuple[str, str]:
    if not last_player_message.strip():
        return t("The other party falls silent for a moment and does not reply immediately."), ""
    return t("{target_avatar_name} pauses to think and responds to the topic.", target_avatar_name=target_avatar.name), ""


async def _generate_roleplay_conversation_reply(*, avatar, target_avatar, messages: list[dict[str, Any]]) -> dict[str, str]:
    world = avatar.world
    info = {
        "avatar_name": avatar.name,
        "target_avatar_name": target_avatar.name,
        "world_info": to_json_str_with_intent(world.get_info(avatar=avatar, detailed=True)),
        "avatar_infos": to_json_str_with_intent(
            {
                avatar.name: avatar.get_expanded_info(other_avatar=target_avatar, detailed=True),
                target_avatar.name: target_avatar.get_info(detailed=True),
            }
        ),
        "conversation_history": to_json_str_with_intent(_build_conversation_history_payload(messages)),
    }
    template_path = CONFIG.paths.templates / "roleplay_conversation_turn.txt"
    try:
        response = await call_llm_with_task_name("roleplay_conversation_turn", template_path, info)
        payload = response.get(target_avatar.name, {}) if isinstance(response, dict) else {}
        reply = str(payload.get("reply_content", payload.get("conversation_content", "")) or "").strip()
        thinking = str(payload.get("speaker_thinking", payload.get("thinking", "")) or "").strip()
        if reply:
            return {"reply_content": reply, "speaker_thinking": thinking}
    except Exception:
        pass

    last_player_message = str(messages[-1].get("content", "") if messages else "")
    fallback_reply, fallback_thinking = _build_fallback_conversation_reply(
        target_avatar=target_avatar,
        last_player_message=last_player_message,
    )
    return {
        "reply_content": fallback_reply,
        "speaker_thinking": fallback_thinking,
    }


def _build_fallback_conversation_summary(*, avatar, target_avatar, messages: list[dict[str, Any]]) -> dict[str, str]:
    turns = max(sum(1 for item in messages if item.get("role") == "player"), 1)
    summary = t(
        "{avatar_name} and {target_avatar_name} talked for {turns} turns and both gained a new impression of the topic at hand.",
        avatar_name=avatar.name,
        target_avatar_name=target_avatar.name,
        turns=turns,
    )
    return {
        "summary": summary,
        "relation_hint": "",
        "story_hint": "",
    }


async def _summarize_roleplay_conversation(*, avatar, target_avatar, messages: list[dict[str, Any]]) -> dict[str, str]:
    world = avatar.world
    info = {
        "avatar_name": avatar.name,
        "target_avatar_name": target_avatar.name,
        "world_info": to_json_str_with_intent(world.get_info(avatar=avatar, detailed=True)),
        "avatar_infos": to_json_str_with_intent(
            {
                avatar.name: avatar.get_expanded_info(other_avatar=target_avatar, detailed=True),
                target_avatar.name: target_avatar.get_info(detailed=True),
            }
        ),
        "conversation_history": to_json_str_with_intent(_build_conversation_history_payload(messages)),
    }
    template_path = CONFIG.paths.templates / "roleplay_conversation_summary.txt"
    try:
        response = await call_llm_with_task_name("roleplay_conversation_summary", template_path, info)
        if isinstance(response, dict):
            summary = str(response.get("summary", "") or "").strip()
            relation_hint = str(response.get("relation_hint", "") or "").strip()
            story_hint = str(response.get("story_hint", "") or "").strip()
            if summary:
                return {
                    "summary": summary,
                    "relation_hint": relation_hint,
                    "story_hint": story_hint,
                }
    except Exception:
        pass
    return _build_fallback_conversation_summary(avatar=avatar, target_avatar=target_avatar, messages=messages)


def begin_roleplay_conversation(runtime, *, avatar, target_avatar) -> dict[str, Any]:
    session = runtime.get_roleplay_session()
    pending = session.get("pending_request")
    existing = session.get("conversation_session")
    if isinstance(existing, dict):
        if (
            str(existing.get("avatar_id") or "") == str(avatar.id)
            and str(existing.get("target_avatar_id") or "") == str(target_avatar.id)
            and str(existing.get("status") or "") in {"awaiting_player", "awaiting_continue", "completed"}
        ):
            return dict(session)
    if pending is not None:
        raise HTTPException(status_code=409, detail=t("There is already a pending roleplay request"))

    request_id = f"roleplay-conversation-{avatar.id}-{target_avatar.id}-{int(time.time() * 1000)}"
    title = t("{avatar_name} is talking with {target_avatar_name}", avatar_name=avatar.name, target_avatar_name=target_avatar.name)
    description = t(
        "World paused and waiting for you to continue speaking as {avatar_name} with {target_avatar_name}.",
        avatar_name=avatar.name,
        target_avatar_name=target_avatar.name,
    )
    messages: list[dict[str, Any]] = []
    session["controlled_avatar_id"] = str(avatar.id)
    session["status"] = "conversing"
    session["pending_request"] = _make_pending_conversation_request(
        avatar=avatar,
        target_avatar=target_avatar,
        request_id=request_id,
        title=title,
        description=description,
        messages=messages,
    )
    session["last_prompt_context"] = {
        **_build_prompt_context(avatar),
        "target_avatar_id": str(target_avatar.id),
        "target_avatar_name": target_avatar.name,
        "conversation_title": title,
    }
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


def start_roleplay(runtime, *, avatar_id: str) -> dict[str, Any]:
    world = _require_world(runtime)
    avatar = _find_avatar_or_raise(world, avatar_id)
    session = runtime.get_roleplay_session()
    current_avatar_id = session.get("controlled_avatar_id")
    if current_avatar_id and str(current_avatar_id) != str(avatar_id):
        raise HTTPException(status_code=409, detail=t("There is already another avatar under roleplay control"))

    prompt_context = _build_prompt_context(avatar)
    if avatar.current_action is None and not avatar.has_plans():
        return _set_waiting_decision(runtime, avatar=avatar, prompt_context=prompt_context)
    return _set_observing(runtime, avatar_id=str(avatar.id), prompt_context=prompt_context)


def stop_roleplay(runtime, *, avatar_id: str | None = None) -> dict[str, Any]:
    session = runtime.get_roleplay_session()
    current_avatar_id = session.get("controlled_avatar_id")
    if avatar_id and current_avatar_id and str(current_avatar_id) != str(avatar_id):
        raise HTTPException(status_code=409, detail=t("Roleplay target does not match"))
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
    from src.classes.actions import get_action_infos_str
    from src.classes.core.avatar.info_presenter import get_avatar_ai_context

    world = _require_world(runtime)
    avatar = _find_avatar_or_raise(world, avatar_id)
    session = runtime.get_roleplay_session()
    pending = session.get("pending_request") or {}

    if str(session.get("controlled_avatar_id") or "") != str(avatar_id):
        raise HTTPException(status_code=409, detail=t("Roleplay target does not match"))
    if str(session.get("status") or "") != "awaiting_decision":
        raise HTTPException(status_code=409, detail=t("The current request is not waiting for a roleplay command"))
    if str(pending.get("request_id") or "") != str(request_id):
        raise HTTPException(status_code=404, detail=t("Roleplay request does not exist or has expired"))
    if not str(command_text or "").strip():
        raise HTTPException(status_code=400, detail=t("Please enter a roleplay command"))

    session["status"] = "submitting"
    command_text = str(command_text).strip()
    _append_interaction_history(
        runtime,
        {
            "type": "command",
            "text": command_text,
        },
    )

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
        _append_interaction_history(
            runtime,
            {
                "type": "error",
                "text": t("Failed to generate a valid action plan from this command"),
            },
        )
        raise HTTPException(status_code=422, detail=t("Failed to generate a valid action plan from this command"))

    avatar_thinking = str(payload.get("avatar_thinking", payload.get("thinking", "")) or command_text)
    short_term_objective = str(payload.get("short_term_objective", "") or command_text)
    raw_emotion = str(payload.get("current_emotion", "") or "")
    try:
        avatar.emotion = EmotionType(raw_emotion)
    except ValueError:
        pass

    avatar.load_decide_result_chain(pairs, avatar_thinking, short_term_objective)
    _append_interaction_history(
        runtime,
        {
            "type": "action_chain",
            "actions": build_roleplay_action_chain_display(pairs),
        },
    )
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
        "message": t("Roleplay command submitted"),
        "planned_action_count": len(pairs),
    }


async def submit_roleplay_choice(runtime, *, avatar_id: str, request_id: str, selected_key: str) -> dict[str, Any]:
    world = _require_world(runtime)
    _find_avatar_or_raise(world, avatar_id)
    session = runtime.get_roleplay_session()
    pending = session.get("pending_request") or {}

    if str(session.get("controlled_avatar_id") or "") != str(avatar_id):
        raise HTTPException(status_code=409, detail=t("Roleplay target does not match"))
    if str(session.get("status") or "") != "awaiting_choice":
        raise HTTPException(status_code=409, detail=t("The current request is not waiting for a roleplay choice"))
    if str(pending.get("request_id") or "") != str(request_id):
        raise HTTPException(status_code=404, detail=t("Roleplay request does not exist or has expired"))

    choice_future = session.get("_choice_future")
    if choice_future is None:
        raise HTTPException(status_code=409, detail=t("Roleplay choice state is invalid, please trigger it again"))
    if hasattr(choice_future, "done") and choice_future.done():
        raise HTTPException(status_code=409, detail=t("This roleplay choice has already been handled"))

    session["status"] = "submitting"
    _append_interaction_history(
        runtime,
        {
            "type": "choice",
            "text": _find_choice_option_text(pending, str(selected_key)),
        },
    )
    choice_future.set_result(str(selected_key))
    return {
        "status": "ok",
        "message": t("Roleplay choice submitted"),
        "selected_key": str(selected_key),
    }


async def submit_roleplay_conversation_turn(runtime, *, avatar_id: str, request_id: str, message: str) -> dict[str, Any]:
    world = _require_world(runtime)
    avatar = _find_avatar_or_raise(world, avatar_id)
    session = runtime.get_roleplay_session()
    pending = session.get("pending_request") or {}
    conversation_session = session.get("conversation_session") or {}

    if str(session.get("controlled_avatar_id") or "") != str(avatar_id):
        raise HTTPException(status_code=409, detail=t("Roleplay target does not match"))
    if str(session.get("status") or "") != "conversing":
        raise HTTPException(status_code=409, detail=t("The current request is not in a roleplay conversation"))
    if str(pending.get("request_id") or "") != str(request_id):
        raise HTTPException(status_code=404, detail=t("Roleplay conversation request does not exist or has expired"))
    if str(conversation_session.get("request_id") or "") != str(request_id):
        raise HTTPException(status_code=404, detail=t("Roleplay conversation session does not exist or has expired"))
    if not str(message or "").strip():
        raise HTTPException(status_code=400, detail=t("Please enter dialogue content"))

    target_avatar = _find_avatar_or_raise(world, str(conversation_session.get("target_avatar_id") or ""))
    session["status"] = "submitting"

    messages = list(conversation_session.get("messages") or [])
    player_message = {
        "id": f"msg-player-{int(time.time() * 1000)}",
        "role": "player",
        "speaker_avatar_id": str(avatar.id),
        "speaker_name": avatar.name,
        "content": str(message).strip(),
        "created_at": time.time(),
    }
    messages.append(player_message)
    _append_interaction_history(
        runtime,
        {
            "type": "conversation_player",
            "text": player_message["content"],
        },
    )

    reply_payload = await _generate_roleplay_conversation_reply(
        avatar=avatar,
        target_avatar=target_avatar,
        messages=messages,
    )
    reply_text = str(reply_payload.get("reply_content", "") or "").strip()
    ai_thinking = str(reply_payload.get("speaker_thinking", "") or "").strip()
    reply_message = {
        "id": f"msg-target-{int(time.time() * 1000)}",
        "role": "assistant",
        "speaker_avatar_id": str(target_avatar.id),
        "speaker_name": target_avatar.name,
        "content": reply_text,
        "created_at": time.time(),
    }
    messages.append(reply_message)
    _append_interaction_history(
        runtime,
        {
            "type": "conversation_assistant",
            "text": reply_text,
        },
    )

    conversation_session["messages"] = messages
    conversation_session["status"] = "awaiting_player"
    conversation_session["last_ai_thinking"] = ai_thinking
    pending["messages"] = list(messages)
    session["pending_request"] = pending
    session["conversation_session"] = conversation_session
    session["status"] = "conversing"
    session["last_prompt_context"] = {
        **(session.get("last_prompt_context") or {}),
        "last_player_message": player_message["content"],
        "last_target_reply": reply_text,
    }
    target_avatar.thinking = ai_thinking
    runtime.set_roleplay_auto_paused(True)
    return {
        "status": "ok",
        "message": t("Conversation updated"),
        "messages": list(messages),
        "reply": reply_text,
    }


async def end_roleplay_conversation(runtime, *, avatar_id: str, request_id: str) -> dict[str, Any]:
    world = _require_world(runtime)
    avatar = _find_avatar_or_raise(world, avatar_id)
    session = runtime.get_roleplay_session()
    pending = session.get("pending_request") or {}
    conversation_session = session.get("conversation_session") or {}

    if str(session.get("controlled_avatar_id") or "") != str(avatar_id):
        raise HTTPException(status_code=409, detail=t("Roleplay target does not match"))
    if str(session.get("status") or "") != "conversing":
        raise HTTPException(status_code=409, detail=t("The current request is not in a roleplay conversation"))
    if str(pending.get("request_id") or "") != str(request_id):
        raise HTTPException(status_code=404, detail=t("Roleplay conversation request does not exist or has expired"))
    if str(conversation_session.get("request_id") or "") != str(request_id):
        raise HTTPException(status_code=404, detail=t("Roleplay conversation session does not exist or has expired"))

    target_avatar = _find_avatar_or_raise(world, str(conversation_session.get("target_avatar_id") or ""))
    messages = list(conversation_session.get("messages") or [])
    summary_payload = await _summarize_roleplay_conversation(
        avatar=avatar,
        target_avatar=target_avatar,
        messages=messages,
    )
    summary_text = str(summary_payload.get("summary", "") or "").strip()
    _append_interaction_history(
        runtime,
        {
            "type": "conversation_summary",
            "text": summary_text,
        },
    )

    conversation_session["status"] = "completed"
    conversation_session["last_summary"] = dict(summary_payload)
    session["conversation_session"] = conversation_session
    session["pending_request"] = None
    session["status"] = "observing"
    session["last_prompt_context"] = {
        **(session.get("last_prompt_context") or {}),
        "last_conversation_summary": summary_text,
        "target_avatar_name": target_avatar.name,
    }
    runtime.set_roleplay_auto_paused(False)
    return {
        "status": "ok",
        "message": t("Conversation ended"),
        "summary": summary_text,
        "relation_hint": str(summary_payload.get("relation_hint", "") or ""),
        "story_hint": str(summary_payload.get("story_hint", "") or ""),
    }
