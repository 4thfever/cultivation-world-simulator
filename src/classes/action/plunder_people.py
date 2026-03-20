from __future__ import annotations

from src.i18n import t
from src.classes.action import TimedAction
from src.classes.event import Event
from src.classes.environment.region import CityRegion
from src.classes.alignment import Alignment


class PlunderPeople(TimedAction):
    """
    在城镇对百姓进行搜刮，获取少量灵石。
    仅邪阵营可执行。
    """

    ACTION_NAME_ID = "plunder_people_action_name"
    DESC_ID = "plunder_people_description"
    REQUIREMENTS_ID = "plunder_people_requirements"
    
    EMOJI = "💀"
    PARAMS = {}
    TOTAL_GAIN = 90
    TOTAL_POPULATION_LOSS = 3.0
    LUCK_DELTA = -0.3

    duration_months = 3

    def can_possibly_start(self) -> bool:
        if self.avatar.alignment != Alignment.EVIL:
            return False
        return True

    def _execute(self) -> None:
        return

    def can_start(self) -> tuple[bool, str]:
        region = self.avatar.tile.region
        if not isinstance(region, CityRegion):
            return False, t("Can only execute in city areas")
        if self.avatar.alignment != Alignment.EVIL:
            return False, t("Only evil alignment can execute")
        return True, ""

    def start(self) -> Event:
        content = t("{avatar} begins plundering people in town", avatar=self.avatar.name)
        return Event(self.world.month_stamp, content, related_avatars=[self.avatar.id])

    # TimedAction 已统一 step 逻辑

    async def finish(self) -> list[Event]:
        region = self.avatar.tile.region
        if isinstance(region, CityRegion):
            region.change_population(-self.TOTAL_POPULATION_LOSS)

        multiplier_raw = self.avatar.effects.get("extra_plunder_multiplier", 0.0)
        multiplier = 1.0 + float(multiplier_raw or 0.0)
        gain = int(self.TOTAL_GAIN * multiplier)
        self.avatar.magic_stone = self.avatar.magic_stone + gain
        self.avatar.add_persistent_effect(
            "effect_source_plunder_people_karma",
            {"extra_luck": self.LUCK_DELTA},
        )
        return []
