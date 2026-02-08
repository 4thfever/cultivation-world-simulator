from __future__ import annotations

from src.i18n import t
from src.classes.action import TimedAction
from src.classes.event import Event
from src.classes.environment.region import CityRegion
from src.classes.alignment import Alignment


class HelpPeople(TimedAction):
    """
    在城镇救济百姓，消耗少量灵石。
    仅正阵营可执行。
    """

    ACTION_NAME_ID = "help_people_action_name"
    DESC_ID = "help_people_description"
    REQUIREMENTS_ID = "help_people_requirements"
    
    EMOJI = "🤝"
    PARAMS = {}
    COST = 10

    duration_months = 3

    def _execute(self) -> None:
        region = self.avatar.tile.region
        if not isinstance(region, CityRegion):
            return
        cost = self.COST
        if self.avatar.magic_stone >= cost:
            self.avatar.magic_stone = self.avatar.magic_stone - cost
            region.change_prosperity(3)

    def can_start(self) -> tuple[bool, str]:
        region = self.avatar.tile.region
        if not isinstance(region, CityRegion):
            return False, t("Can only execute in city areas")
        cost = self.COST
        if not (self.avatar.magic_stone >= cost):
            return False, t("Insufficient spirit stones")
        return True, ""

    def start(self) -> Event:
        content = t("{avatar} begins helping people in town", avatar=self.avatar.name)
        return Event(self.world.month_stamp, content, related_avatars=[self.avatar.id])

    # TimedAction 已统一 step 逻辑

    async def finish(self) -> list[Event]:
        return []
