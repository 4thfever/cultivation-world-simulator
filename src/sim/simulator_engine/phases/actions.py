from __future__ import annotations

from src.classes.ai import llm_ai
from src.classes.core.avatar import Avatar
from src.classes.event import Event, is_null_event
from src.run.log import get_logger
from src.utils.config import CONFIG


async def phase_decide_actions(world, living_avatars: list[Avatar]) -> None:
    avatars_to_decide = [
        avatar
        for avatar in living_avatars
        if avatar.current_action is None and not avatar.has_plans()
    ]
    if not avatars_to_decide:
        return

    decide_results = await llm_ai.decide(world, avatars_to_decide)
    for avatar, result in decide_results.items():
        action_name_params_pairs, avatar_thinking, short_term_objective, _event = result
        avatar.load_decide_result_chain(
            action_name_params_pairs,
            avatar_thinking,
            short_term_objective,
        )


def phase_commit_next_plans(living_avatars: list[Avatar]) -> list[Event]:
    events: list[Event] = []
    for avatar in living_avatars:
        if avatar.current_action is None:
            start_event = avatar.commit_next_plan()
            if start_event is not None and not is_null_event(start_event):
                events.append(start_event)
    return events


async def _tick_action_round(avatars: list[Avatar], log_label: str) -> tuple[list[Event], set[Avatar]]:
    events: list[Event] = []
    avatars_needing_retry: set[Avatar] = set()

    for avatar in avatars:
        try:
            new_events = await avatar.tick_action()
            if new_events:
                events.extend(new_events)

            if getattr(avatar, "_new_action_set_this_step", False):
                avatars_needing_retry.add(avatar)
        except Exception as exc:
            get_logger().logger.error(
                "Avatar %s(%s) %s failed: %s",
                avatar.name,
                avatar.id,
                log_label,
                exc,
                exc_info=True,
            )
            if hasattr(avatar, "_new_action_set_this_step"):
                avatar._new_action_set_this_step = False

    return events, avatars_needing_retry


async def phase_execute_actions(living_avatars: list[Avatar]) -> list[Event]:
    events: list[Event] = []
    max_local_rounds = CONFIG.game.max_action_rounds_per_turn

    round_events, avatars_needing_retry = await _tick_action_round(
        living_avatars,
        "tick_action",
    )
    events.extend(round_events)

    round_count = 1
    while avatars_needing_retry and round_count < max_local_rounds:
        current_avatars = list(avatars_needing_retry)
        round_events, avatars_needing_retry = await _tick_action_round(
            current_avatars,
            "retry tick_action",
        )
        events.extend(round_events)
        round_count += 1

    return events
