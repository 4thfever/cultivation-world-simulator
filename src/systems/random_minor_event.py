from __future__ import annotations

from src.classes.core.avatar import Avatar
from src.classes.core.world import World
from src.classes.event import Event

from .random_minor_event_service import RandomMinorEventService


async def try_trigger_random_minor_event(avatar: Avatar, world: World) -> list[Event]:
    if not RandomMinorEventService.should_trigger(avatar):
        return []
    return await RandomMinorEventService.try_create_events(avatar, world)


__all__ = ["try_trigger_random_minor_event"]
