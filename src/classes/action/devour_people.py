from __future__ import annotations

from src.i18n import t
from src.classes.action import TimedAction
from src.classes.event import Event
from src.classes.environment.region import CityRegion
from src.classes.items.auxiliary import (
    TEN_THOUSAND_SOULS_BANNER_MAX_SOULS,
    is_ten_thousand_souls_banner,
)


class DevourPeople(TimedAction):
    """
    吞噬生灵：需持有万魂幡，吞噬魂魄可较多增加战力。
    """
    
    # 多语言 ID
    ACTION_NAME_ID = "devour_people_action_name"
    DESC_ID = "devour_people_description"
    REQUIREMENTS_ID = "devour_people_requirements"
    
    # 不需要翻译的常量
    EMOJI = "🩸"
    PARAMS = {}
    POPULATION_LOSS_RATIO = 0.01
    LUCK_DELTA = -1.0

    duration_months = 2

    def can_possibly_start(self) -> bool:
        legal = self.avatar.effects.get("legal_actions", [])
        if "DevourPeople" not in legal:
            return False
        return True

    def _execute(self) -> None:
        return

    def can_start(self) -> tuple[bool, str]:
        legal = self.avatar.effects.get("legal_actions", [])
        ok = "DevourPeople" in legal
        if not ok:
            return False, t("Forbidden illegal action (missing Ten Thousand Souls Banner or permission)")
        region = self.avatar.tile.region
        if not isinstance(region, CityRegion):
            return False, t("Can only execute in city areas")
        return True, ""

    def start(self) -> Event:
        content = t("{avatar} begins devouring people in town", avatar=self.avatar.name)
        return Event(self.world.month_stamp, content, related_avatars=[self.avatar.id])

    async def finish(self) -> list[Event]:
        auxiliary = self.avatar.auxiliary
        region = self.avatar.tile.region
        if not is_ten_thousand_souls_banner(auxiliary) or not isinstance(region, CityRegion):
            return []

        population_loss = float(region.population) * self.POPULATION_LOSS_RATIO
        consumed_people = int(float(region.population) * 10000 * self.POPULATION_LOSS_RATIO)
        region.change_population(-population_loss)

        current_souls = int(auxiliary.special_data.get("devoured_souls", 0) or 0)
        auxiliary.special_data["devoured_souls"] = min(
            TEN_THOUSAND_SOULS_BANNER_MAX_SOULS,
            current_souls + consumed_people,
        )
        self.avatar.add_persistent_effect(
            "effect_source_devour_people_karma",
            {"extra_luck": self.LUCK_DELTA},
        )
        return []
