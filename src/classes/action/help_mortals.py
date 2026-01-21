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

    ACTION_NAME_ID = "help_mortals_action_name"
    DESC_ID = "help_mortals_description"
    REQUIREMENTS_ID = "help_mortals_requirements"
    
    EMOJI = "🤝"
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
        from src.i18n import t
        region = self.avatar.tile.region
        if not isinstance(region, CityRegion):
            return False, t("Can only execute in city areas")
        if self.avatar.alignment != Alignment.RIGHTEOUS:
            return False, t("Only righteous alignment can execute")
        cost = self.COST
        if not (self.avatar.magic_stone >= cost):
            return False, t("Insufficient spirit stones")
        return True, ""

    def start(self) -> Event:
        from src.i18n import t
        content = t("{avatar} begins helping mortals in town", avatar=self.avatar.name)
        return Event(self.world.month_stamp, content, related_avatars=[self.avatar.id])

    # TimedAction 已统一 step 逻辑

    async def finish(self) -> list[Event]:
        return []

