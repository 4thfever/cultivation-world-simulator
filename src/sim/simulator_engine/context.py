from __future__ import annotations

from dataclasses import dataclass, field

from src.classes.core.avatar import Avatar
from src.classes.core.world import World
from src.classes.event import Event
from src.systems.time import Month, MonthStamp


@dataclass(slots=True)
class SimulationStepContext:
    world: World
    living_avatars: list[Avatar]
    events: list[Event] = field(default_factory=list)
    processed_event_ids: set[str] = field(default_factory=set)
    month_stamp: MonthStamp | None = None

    @classmethod
    def create(cls, world: World) -> "SimulationStepContext":
        return cls(
            world=world,
            living_avatars=world.avatar_manager.get_living_avatars(),
            month_stamp=world.month_stamp,
        )

    @property
    def is_january(self) -> bool:
        return self.month_stamp is not None and self.month_stamp.get_month() == Month.JANUARY

    def add_events(self, new_events: list[Event] | None) -> None:
        if new_events:
            self.events.extend(new_events)
