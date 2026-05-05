from __future__ import annotations

from src.i18n import t
from src.classes.action import TimedAction
from src.classes.event import Event
from src.classes.alignment import Alignment
from src.classes.environment.region import CityRegion
from src.classes.race import is_yao_avatar
from src.systems.cultivation import REALM_RANK


class EatMortals(TimedAction):
    ACTION_NAME_ID = "eat_mortals_action_name"
    DESC_ID = "eat_mortals_description"
    REQUIREMENTS_ID = "eat_mortals_requirements"

    EMOJI = "🍖"
    PARAMS = {}

    duration_months = 1
    POPULATION_LOSS_RATIO = 0.004
    BASE_EXP = 80

    def can_possibly_start(self) -> bool:
        if not is_yao_avatar(self.avatar):
            return False
        return getattr(self.avatar, "alignment", None) != Alignment.RIGHTEOUS

    def _execute(self) -> None:
        return

    def can_start(self) -> tuple[bool, str]:
        if not is_yao_avatar(self.avatar):
            return False, t("Only yao cultivators can eat mortals.")
        if getattr(self.avatar, "alignment", None) == Alignment.RIGHTEOUS:
            return False, t("Righteous cultivators will not eat mortals.")
        region = getattr(getattr(self.avatar, "tile", None), "region", None)
        if not isinstance(region, CityRegion):
            return False, t("Can only eat mortals in city areas.")
        if float(getattr(region, "population", 0.0) or 0.0) <= 0:
            return False, t("There are no mortals here to eat.")
        return True, ""

    def start(self) -> Event:
        region = self.avatar.tile.region
        return Event(
            self.world.month_stamp,
            t("{avatar} stalks the mortal crowds of {city}.", avatar=self.avatar.name, city=region.name),
            related_avatars=[self.avatar.id],
        )

    async def finish(self) -> list[Event]:
        region = getattr(getattr(self.avatar, "tile", None), "region", None)
        if not isinstance(region, CityRegion):
            return []

        population_loss = max(0.001, float(region.population) * self.POPULATION_LOSS_RATIO)
        eaten_people = max(1, int(float(region.population) * 10000 * self.POPULATION_LOSS_RATIO))
        region.change_population(-population_loss)

        realm_rank = REALM_RANK.get(self.avatar.cultivation_progress.realm, 0) + 1
        multiplier = 1.0 + float(self.avatar.effects.get("extra_eat_mortals_exp_multiplier", 0.0) or 0.0)
        exp = max(1, int(self.BASE_EXP * realm_rank * multiplier))
        if self.avatar.cultivation_progress.can_cultivate():
            self.avatar.cultivation_progress.add_exp(exp)

        return [
            Event(
                self.world.month_stamp,
                t("{avatar} ate {count} mortals in {city}, refining flesh and fear into {exp} cultivation experience.", avatar=self.avatar.name, count=eaten_people, city=region.name, exp=exp),
                related_avatars=[self.avatar.id],
                is_major=True,
            )
        ]
