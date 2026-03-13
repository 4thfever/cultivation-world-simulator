from __future__ import annotations

from src.classes.event import Event
from src.run.log import get_logger

from .context import SimulationStepContext


def log_events(events: list[Event]) -> None:
    logger = get_logger().logger
    for event in events:
        logger.info("EVENT: %s", str(event))


def finalize_step(simulator, ctx: SimulationStepContext) -> list[Event]:
    for avatar in ctx.world.avatar_manager.avatars.values():
        if avatar.enable_metrics_tracking:
            avatar.record_metrics()

    unique_events: dict[str, Event] = {}
    for event in ctx.events:
        if event.id not in unique_events:
            unique_events[event.id] = event
    final_events = list(unique_events.values())

    if ctx.world.event_manager:
        for event in final_events:
            ctx.world.event_manager.add_event(event)

    simulator._phase_log_events(final_events)
    ctx.world.month_stamp = ctx.world.month_stamp + 1
    ctx.events = final_events
    return final_events
