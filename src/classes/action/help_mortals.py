from __future__ import annotations

from src.classes.action import TimedAction
from src.classes.event import Event
from src.classes.region import CityRegion
from src.classes.alignment import Alignment


class HelpMortals(TimedAction):
    """
    在城镇帮助凡人，消耗少量灵石。
    仅正阵营可执行。
    """

    ACTION_NAME = "帮助凡人"
    EMOJI = "🤝"
    DESC = "在城镇帮助凡人，消耗少量灵石"
    DOABLES_REQUIREMENTS = "仅限城市区域，且角色阵营为‘正’，并且灵石足够"
    PARAMS = {}
    COST = 10

    duration_months = 3

    def _execute(self) -> None:
        region = self.avatar.tile.region
        if not isinstance(region, CityRegion):
            return
        cost = self.COST
        if getattr(self.avatar.magic_stone, "value", 0) >= cost:
            self.avatar.magic_stone = self.avatar.magic_stone - cost

    def can_start(self) -> tuple[bool, str]:
        region = self.avatar.tile.region
        if not isinstance(region, CityRegion):
            return False, "仅能在城市区域执行"
        if self.avatar.alignment != Alignment.RIGHTEOUS:
            return False, "仅正阵营可执行"
        cost = self.COST
        if not (self.avatar.magic_stone >= cost):
            return False, "灵石不足"
        return True, ""

    def start(self) -> Event:
        return Event(self.world.month_stamp, f"{self.avatar.name} 在城镇开始帮助凡人", related_avatars=[self.avatar.id])

    # TimedAction 已统一 step 逻辑

    async def finish(self) -> list[Event]:
        return []


