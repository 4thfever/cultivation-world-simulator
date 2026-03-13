from __future__ import annotations

from dataclasses import dataclass, field

from src.classes.core.avatar import Avatar
from src.classes.core.world import World
from src.classes.event import Event
from src.systems.time import Month, MonthStamp


@dataclass(slots=True)
class SimulationStepContext:
    # 单次 step 共享的运行时容器：
    # 把“在世角色缓存、事件汇总、交互去重状态”集中到一起，
    # 避免这些临时状态散落在 Simulator.step() 的局部变量里。
    world: World
    living_avatars: list[Avatar]
    events: list[Event] = field(default_factory=list)
    processed_event_ids: set[str] = field(default_factory=set)
    month_stamp: MonthStamp | None = None

    @classmethod
    def create(cls, world: World) -> "SimulationStepContext":
        # 每轮开始时抓取一次在世角色快照，后续只允许通过 phase
        # 明确地修改这份列表，例如死亡结算阶段会原地移除死者。
        return cls(
            world=world,
            living_avatars=world.avatar_manager.get_living_avatars(),
            month_stamp=world.month_stamp,
        )

    @property
    def is_january(self) -> bool:
        return self.month_stamp is not None and self.month_stamp.get_month() == Month.JANUARY

    def add_events(self, new_events: list[Event] | None) -> None:
        # phase 可以返回空列表或 None，这里统一做一次兼容，
        # 让 step() 的编排代码保持扁平。
        if new_events:
            self.events.extend(new_events)
