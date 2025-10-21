from __future__ import annotations

from src.classes.action import TimedAction
from src.classes.event import Event
from src.classes.region import CityRegion
from src.classes.alignment import Alignment


class PlunderMortals(TimedAction):
    """
    在城镇对凡人进行搜刮，获取少量灵石。
    仅邪阵营可执行。
    """

    COMMENT = "在城镇搜刮凡人，获取少量灵石"
    DOABLES_REQUIREMENTS = "仅限城市区域，且角色阵营为‘邪’"
    PARAMS = {}
    GAIN = 20

    duration_months = 3

    def _execute(self) -> None:
        region = self.avatar.tile.region
        if not isinstance(region, CityRegion):
            return
        gain = self.GAIN
        self.avatar.magic_stone = self.avatar.magic_stone + gain

    def can_start(self) -> tuple[bool, str]:
        region = self.avatar.tile.region
        if not isinstance(region, CityRegion):
            return False, "仅能在城市区域执行"
        if self.avatar.alignment != Alignment.EVIL:
            return False, "仅邪阵营可执行"
        return True, ""

    def start(self) -> Event:
        return Event(self.world.month_stamp, f"{self.avatar.name} 在城镇开始搜刮凡人", related_avatars=[self.avatar.id])

    # TimedAction 已统一 step 逻辑

    def finish(self) -> list[Event]:
        return []


