from __future__ import annotations

from src.classes.action import TimedAction
from src.classes.event import Event
from src.classes.region import CityRegion
from src.classes.alignment import Alignment


class PlunderMortals(TimedAction):
    """
    在城镇对凡人进行搜刮，获取少量灵石。
    仅邪阵营可执行。
    """

    ACTION_NAME = "搜刮凡人"
    EMOJI = "💀"
    DESC = "在城镇搜刮凡人，获取少量灵石"
    DOABLES_REQUIREMENTS = "仅限城市区域，且角色阵营为‘邪’"
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
            return False, "仅能在城市区域执行"
        if self.avatar.alignment != Alignment.EVIL:
            return False, "仅邪阵营可执行"
        return True, ""

    def start(self) -> Event:
        return Event(self.world.month_stamp, f"{self.avatar.name} 在城镇开始搜刮凡人", related_avatars=[self.avatar.id])

    # TimedAction 已统一 step 逻辑

    async def finish(self) -> list[Event]:
        return []


