from __future__ import annotations

from src.i18n import t
from src.classes.action import TimedAction
from src.classes.event import Event
from src.classes.environment.region import CityRegion
import random


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
    POPULATION_LOSS = 2.5

    duration_months = 2

    def can_possibly_start(self) -> bool:
        legal = self.avatar.effects.get("legal_actions", [])
        if "DevourPeople" not in legal:
            return False
        return True

    def _execute(self) -> None:
        # 若持有万魂幡：累积吞噬魂魄（10~100），上限10000
        # 万魂幡是辅助装备(auxiliary)
        auxiliary = self.avatar.auxiliary
        if auxiliary is not None and auxiliary.name == "万魂幡":
            gain = random.randint(10, 100)
            current_souls = auxiliary.special_data.get("devoured_souls", 0)
            auxiliary.special_data["devoured_souls"] = min(10000, int(current_souls) + gain)
            
            # 若在城市中，大幅降低人口
            region = self.avatar.tile.region
            if isinstance(region, CityRegion):
                region.change_population(-self.POPULATION_LOSS)

    def can_start(self) -> tuple[bool, str]:
        legal = self.avatar.effects.get("legal_actions", [])
        ok = "DevourPeople" in legal
        return (ok, "" if ok else t("Forbidden illegal action (missing Ten Thousand Souls Banner or permission)"))

    def start(self) -> Event:
        content = t("{avatar} begins devouring people in town", avatar=self.avatar.name)
        return Event(self.world.month_stamp, content, related_avatars=[self.avatar.id])

    async def finish(self) -> list[Event]:
        return []
