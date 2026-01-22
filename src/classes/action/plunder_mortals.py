from __future__ import annotations

from src.i18n import t
from src.classes.action import TimedAction
from src.classes.event import Event
from src.classes.region import CityRegion
from src.classes.alignment import Alignment


class PlunderMortals(TimedAction):
    """
    在城镇对凡人进行搜刮，获取少量灵石。
    仅邪阵营可执行。
    """

    ACTION_NAME_ID = "plunder_mortals_action_name"
    DESC_ID = "plunder_mortals_description"
    REQUIREMENTS_ID = "plunder_mortals_requirements"
    
    EMOJI = "💀"
    PARAMS = {}
    GAIN = 20

    duration_months = 3

    def _execute(self) -> None:
        region = self.avatar.tile.region
        if not isinstance(region, CityRegion):
            return
        
        # 基础收益
        base_gain = self.GAIN
        
        # 应用搜刮收益倍率
        multiplier_raw = self.avatar.effects.get("extra_plunder_multiplier", 0.0)
        multiplier = 1.0 + float(multiplier_raw or 0.0)
        
        # 计算最终收益
        gain = int(base_gain * multiplier)
        self.avatar.magic_stone = self.avatar.magic_stone + gain

    def can_start(self) -> tuple[bool, str]:
        region = self.avatar.tile.region
        if not isinstance(region, CityRegion):
            return False, t("Can only execute in city areas")
        if self.avatar.alignment != Alignment.EVIL:
            return False, t("Only evil alignment can execute")
        return True, ""

    def start(self) -> Event:
        content = t("{avatar} begins plundering mortals in town", avatar=self.avatar.name)
        return Event(self.world.month_stamp, content, related_avatars=[self.avatar.id])

    # TimedAction 已统一 step 逻辑

    async def finish(self) -> list[Event]:
        return []

