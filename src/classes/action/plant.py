from __future__ import annotations

from src.i18n import t
from src.classes.action import TimedAction
from src.classes.event import Event
from src.systems.cultivation import Realm
from src.classes.environment.region import NormalRegion

REALM_PLANT_INCOME = {
    Realm.Qi_Refinement: 100,
    Realm.Foundation_Establishment: 200,
    Realm.Core_Formation: 300,
    Realm.Nascent_Soul: 400,
}

class Plant(TimedAction):
    """
    种植动作，在普通区域进行种植，持续6个月
    可以直接获得灵石
    """
    
    # 多语言 ID
    ACTION_NAME_ID = "plant_action_name"
    DESC_ID = "plant_description"
    REQUIREMENTS_ID = "plant_requirements"
    
    # 不需要翻译的常量
    EMOJI = "🌱"
    PARAMS = {}

    duration_months = 6

    def __init__(self, avatar, world):
        super().__init__(avatar, world)
        self.gained_stones: int = 0

    def _execute(self) -> None:
        """
        执行种植动作
        """
        base_income = REALM_PLANT_INCOME.get(self.avatar.cultivation_progress.realm, 100)
        extra_income = int(self.avatar.effects.get("extra_plant_income", 0) or 0)
        self.gained_stones = base_income + extra_income
        self.avatar.magic_stone += self.gained_stones

    def can_start(self) -> tuple[bool, str]:
        region = self.avatar.tile.region
        if not isinstance(region, NormalRegion):
            return False, t(self.REQUIREMENTS_ID)
        return True, ""

    def start(self) -> Event:
        content = t("{avatar} begins planting at {location}",
                   avatar=self.avatar.name, location=self.avatar.tile.location_name)
        return Event(self.world.month_stamp, content, related_avatars=[self.avatar.id])

    async def finish(self) -> list[Event]:
        content = t("{avatar} finished planting, earned {stones} Spirit Stones",
                   avatar=self.avatar.name, stones=self.gained_stones)
        return [Event(
            self.world.month_stamp,
            content,
            related_avatars=[self.avatar.id]
        )]
