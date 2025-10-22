from __future__ import annotations

from src.classes.action import TimedAction
from src.classes.event import Event
import random


class DevourMortals(TimedAction):
    """
    吞噬凡人：需持有万魂幡，吞噬魂魄可较多增加战力。
    """

    COMMENT = "吞噬凡人，较多增加战力"
    DOABLES_REQUIREMENTS = "持有万魂幡"
    PARAMS = {}

    duration_months = 2

    def _execute(self) -> None:
        # 若持有万魂幡：累积吞噬魂魄（10~100），上限10000
        tr = getattr(self.avatar, "treasure", None)
        if tr is not None and tr.name == "万魂幡":
            gain = random.randint(10, 100)
            tr.devoured_souls = min(10000, int(tr.devoured_souls) + gain)

    def can_start(self) -> tuple[bool, str]:
        legal = self.avatar.effects.get("legal_actions", [])
        ok = "DevourMortals" in legal
        return (ok, "" if ok else "未被允许的非法动作（缺少万魂幡或权限）")

    def start(self) -> Event:
        return Event(self.world.month_stamp, f"{self.avatar.name} 在城镇开始吞噬凡人", related_avatars=[self.avatar.id])

    def finish(self) -> list[Event]:
        return []


