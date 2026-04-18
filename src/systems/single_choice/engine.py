from __future__ import annotations

import asyncio

from src.utils.llm import call_llm_with_task_name
from src.utils.llm.exceptions import LLMError, ParseError
from src.utils.strings import to_json_str_with_intent

from .models import ChoiceSource, SingleChoiceDecision, SingleChoiceRequest
from .parser import choose_fallback_key, extract_choice_payload, normalize_choice_key
from .scenario import OutcomeT, SingleChoiceScenario


def _build_fallback_decision(request: SingleChoiceRequest, *, reason: str) -> SingleChoiceDecision:
    valid_keys = [option.key for option in request.options]
    fallback_key = choose_fallback_key(valid_keys, request.fallback_policy)
    return SingleChoiceDecision(
        selected_key=fallback_key,
        thinking="",
        source=ChoiceSource.FALLBACK,
        raw_response=None,
        used_fallback=True,
        fallback_reason=reason,
    )


def _build_prompt_infos(request: SingleChoiceRequest) -> dict:
    options_payload = []
    for option in request.options:
        options_payload.append(
            {
                "key": option.key,
                "title": option.title,
                "description": option.description,
            }
        )

    infos = {
        "world_info": request.avatar.world.static_info,
        "avatar_infos": {request.avatar.name: request.avatar.get_info(detailed=True)},
        "situation": request.situation,
        "options_json": to_json_str_with_intent(options_payload),
    }
    infos.update(request.context)
    return infos


async def decide_single_choice(request: SingleChoiceRequest) -> SingleChoiceDecision:
    infos = _build_prompt_infos(request)
    valid_keys = [option.key for option in request.options]

    try:
        response = await call_llm_with_task_name(
            request.task_name,
            request.template_path,
            infos=infos,
        )
        choice, thinking = extract_choice_payload(response)
        normalized_key = normalize_choice_key(choice, valid_keys)
        if normalized_key is not None:
            return SingleChoiceDecision(
                selected_key=normalized_key,
                thinking=thinking,
                source=ChoiceSource.LLM,
                raw_response=response,
                used_fallback=False,
            )

        return SingleChoiceDecision(
            selected_key=choose_fallback_key(valid_keys, request.fallback_policy),
            thinking=thinking,
            source=ChoiceSource.FALLBACK,
            raw_response=response,
            used_fallback=True,
            fallback_reason=f"invalid_choice:{choice}",
        )
    except (LLMError, ParseError, Exception) as exc:
        return _build_fallback_decision(request, reason=type(exc).__name__)


def _ensure_request_identity(request: SingleChoiceRequest) -> SingleChoiceRequest:
    if not request.request_id:
        avatar_id = str(getattr(request.avatar, "id", getattr(request.avatar, "name", "avatar")))
        request.request_id = f"choice-{avatar_id}-{int(asyncio.get_running_loop().time() * 1000)}"
    if not request.title:
        request.title = f"{getattr(request.avatar, 'name', '角色')} 需要做出选择"
    if not request.description:
        request.description = request.situation
    return request


async def _maybe_wait_for_roleplay_choice(request: SingleChoiceRequest) -> SingleChoiceDecision | None:
    try:
        from src.server.services.roleplay_service import (
            begin_roleplay_choice,
            finish_roleplay_choice_wait,
            is_player_controlled_choice_target,
        )
    except Exception:
        return None

    if not is_player_controlled_choice_target(avatar=request.avatar):
        return None

    runtime = getattr(getattr(request.avatar, "world", None), "runtime", None)
    if runtime is None:
        return None

    request = _ensure_request_identity(request)
    selected_key = None
    choice_future = begin_roleplay_choice(runtime, request=request)
    try:
        selected_key = await choice_future
    except asyncio.CancelledError:
        finish_roleplay_choice_wait(runtime, avatar_id=str(getattr(request.avatar, "id", "")))
        return _build_fallback_decision(request, reason="roleplay_choice_cancelled")

    valid_keys = [option.key for option in request.options]
    normalized_key = normalize_choice_key(str(selected_key), valid_keys)
    if normalized_key is not None:
        finish_roleplay_choice_wait(
            runtime,
            avatar_id=str(getattr(request.avatar, "id", "")),
            selected_key=str(selected_key),
        )
        return SingleChoiceDecision(
            selected_key=normalized_key,
            thinking="",
            source=ChoiceSource.PLAYER_ROLEPLAY,
            raw_response={"selected_key": str(selected_key)},
            used_fallback=False,
        )

    finish_roleplay_choice_wait(
        runtime,
        avatar_id=str(getattr(request.avatar, "id", "")),
        selected_key=str(selected_key),
    )
    return _build_fallback_decision(request, reason=f"invalid_player_choice:{selected_key}")


async def resolve_single_choice(scenario: SingleChoiceScenario[OutcomeT]) -> OutcomeT:
    request = scenario.build_request()
    decision = await _maybe_wait_for_roleplay_choice(request)
    if decision is None:
        decision = await decide_single_choice(request)
    return await scenario.apply_decision(decision)
