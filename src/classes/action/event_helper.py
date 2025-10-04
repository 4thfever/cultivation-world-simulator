from __future__ import annotations

from typing import Optional

from src.classes.event import Event


class EventHelper:
    """
    事件推送辅助：统一“侧栏只推一次、双方都写历史”的约定。

    - push_pair: 向发起者与目标同时写入事件；默认仅在发起者侧进入侧栏。
    - push_self: 仅向自身写入事件，可控制是否进入侧栏。
    """
    @staticmethod
    def push_pair(event: Event, initiator: "Avatar", target: Optional["Avatar"], *, to_sidebar_once: bool = True) -> None:
        initiator.add_event(event, to_sidebar=True)
        if target is not None:
            target.add_event(event, to_sidebar=(not to_sidebar_once), to_history=True)

    @staticmethod
    def push_self(event: Event, avatar: "Avatar", *, to_sidebar: bool = True) -> None:
        avatar.add_event(event, to_sidebar=to_sidebar)


