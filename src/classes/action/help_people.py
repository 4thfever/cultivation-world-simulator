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
    TOTAL_COST = 45
    TOTAL_POPULATION_GAIN = 1.8
    LUCK_DELTA = 0.3

    duration_months = 3

    def can_possibly_start(self) -> bool:
        if self.avatar.alignment != Alignment.RIGHTEOUS:
            return False
        return True

    def _execute(self) -> None:
        return

    def can_start(self) -> tuple[bool, str]:
        region = self.avatar.tile.region
        if not isinstance(region, CityRegion):
            return False, t("Can only execute in city areas")
        if not (self.avatar.magic_stone >= self.TOTAL_COST):
            return False, t("Insufficient spirit stones")
        return True, ""

    def start(self) -> Event:
        self.avatar.magic_stone = self.avatar.magic_stone - self.TOTAL_COST
        content = t("{avatar} begins helping people in town", avatar=self.avatar.name)
        return Event(self.world.month_stamp, content, related_avatars=[self.avatar.id])

    # TimedAction 已统一 step 逻辑

    async def finish(self) -> list[Event]:
        region = self.avatar.tile.region
        if isinstance(region, CityRegion):
            region.change_population(self.TOTAL_POPULATION_GAIN)
        self.avatar.add_persistent_effect(
            "effect_source_help_people_karma",
            {"extra_luck": self.LUCK_DELTA},
        )
        return []
