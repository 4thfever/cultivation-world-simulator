from __future__ import annotations

from src.classes.action import TimedAction
from src.classes.event import Event
from src.classes.region import CityRegion
from src.classes.alignment import Alignment
from src.classes.technique import TechniqueAttribute


class DevourMortals(TimedAction):
    """
    吞噬凡人：仅邪阵营可在城市区域执行，获得大量修炼经验。
    与普通修炼相比，经验获取显著更高。
    """

    COMMENT = "在城镇吞噬凡人，获得大量修行经验（邪功法）"
    DOABLES_REQUIREMENTS = "仅限城市区域，且当前功法为‘邪’，且未处于瓶颈"
    PARAMS = {}

    duration_months = 2
    EXP_GAIN = 2000

    def _execute(self) -> None:
        region = self.avatar.tile.region
        if not isinstance(region, CityRegion):
            return
        if self.avatar.cultivation_progress.is_in_bottleneck():
            return
        self.avatar.cultivation_progress.add_exp(self.EXP_GAIN)

    def can_start(self) -> bool:
        region = self.avatar.tile.region
        if not isinstance(region, CityRegion):
            return False
        tech = self.avatar.technique
        if tech.attribute != TechniqueAttribute.EVIL:
            return False
        return not self.avatar.cultivation_progress.is_in_bottleneck()

    def start(self) -> Event:
        return Event(self.world.month_stamp, f"{self.avatar.name} 在城镇开始吞噬凡人")

    def finish(self) -> list[Event]:
        return []


