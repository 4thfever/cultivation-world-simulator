from __future__ import annotations

from src.classes.action import TimedAction
from src.classes.event import Event
from src.classes.region import CityRegion
from src.classes.event import Event
import random


class DevourMortals(TimedAction):
    """
    吞噬凡人：在城市区域执行，需持有万魂幡，吞噬魂魄可增加战力。
    与普通修炼相比，经验获取显著更高。
    """

    COMMENT = "在城镇吞噬凡人，获得大量修行经验（邪功法）"
    DOABLES_REQUIREMENTS = "仅限城市区域；持有万魂幡"
    PARAMS = {}

    duration_months = 2
    EXP_GAIN = 2000

    def _execute(self) -> None:
        region = self.avatar.tile.region
        if not isinstance(region, CityRegion):
            return
        # 若持有万魂幡：累积吞噬魂魄（10~100），上限10000
        tr = getattr(self.avatar, "treasure", None)
        if tr is not None and tr.name == "万魂幡":
            gain = random.randint(10, 100)
            tr.devoured_souls = min(10000, int(tr.devoured_souls) + gain)

    def can_start(self) -> bool:
        region = self.avatar.tile.region
        if not isinstance(region, CityRegion):
            return False
        # 需持有万魂幡且行为被允许
        tr = getattr(self.avatar, "treasure", None)
        if tr is None or tr.name != "万魂幡":
            return False
        legal = self.avatar.effects.get("legal_actions", [])
        return "DevourMortals" in legal

    def start(self) -> Event:
        return Event(self.world.month_stamp, f"{self.avatar.name} 在城镇开始吞噬凡人")

    def finish(self) -> list[Event]:
        return []


