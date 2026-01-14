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
        """
        向双方分发事件。
        发起者侧会进入侧栏（to_sidebar=True），从而被 Simulator 收集并存入全局数据库。
        由于 Simulator 已经统一处理了相关角色的交互计数，这里无需再手动调用 target.add_event。
        """
        initiator.add_event(event, to_sidebar=True)

    @staticmethod
    def push_self(event: Event, avatar: "Avatar", *, to_sidebar: bool = True) -> None:
        """仅向自身分发事件。"""
        avatar.add_event(event, to_sidebar=to_sidebar)


