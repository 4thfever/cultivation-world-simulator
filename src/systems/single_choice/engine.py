from __future__ import annotations

from src.utils.llm import call_llm_with_task_name
from src.utils.llm.exceptions import LLMError, ParseError
from src.utils.strings import to_json_str_with_intent

from .models import ChoiceSource, SingleChoiceDecision, SingleChoiceRequest
from .parser import choose_fallback_key, extract_choice_payload, normalize_choice_key
from .scenario import OutcomeT, SingleChoiceScenario


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

        fallback_key = choose_fallback_key(valid_keys, request.fallback_policy)
        return SingleChoiceDecision(
            selected_key=fallback_key,
            thinking=thinking,
            source=ChoiceSource.FALLBACK,
            raw_response=response,
            used_fallback=True,
            fallback_reason=f"invalid_choice:{choice}",
        )
    except (LLMError, ParseError, Exception) as exc:
        fallback_key = choose_fallback_key(valid_keys, request.fallback_policy)
        return SingleChoiceDecision(
            selected_key=fallback_key,
            thinking="",
            source=ChoiceSource.FALLBACK,
            raw_response=None,
            used_fallback=True,
            fallback_reason=type(exc).__name__,
        )


async def resolve_single_choice(scenario: SingleChoiceScenario[OutcomeT]) -> OutcomeT:
    request = scenario.build_request()
    decision = await decide_single_choice(request)
    return await scenario.apply_decision(decision)
