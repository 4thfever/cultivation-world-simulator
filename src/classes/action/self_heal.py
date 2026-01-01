from __future__ import annotations

from src.classes.action import TimedAction
from src.classes.event import Event
from src.classes.sect_region import SectRegion


class SelfHeal(TimedAction):
    """
    在宗门总部静养疗伤（仅宗门弟子可用，且必须位于自身宗门总部）。
    单月动作，执行后HP直接回满。
    """

    ACTION_NAME = "疗伤"
    EMOJI = "💚"
    DESC = "在宗门总部静养疗伤，回满HP"
    DOABLES_REQUIREMENTS = "自己是宗门弟子，且位于本宗门总部区域，且当前HP未满"
    PARAMS = {}

    # 单月动作
    duration_months = 1

    def _execute(self) -> None:
        # 单月直接回满HP
        hp_obj = self.avatar.hp
        delta = int(max(0, hp_obj.max - hp_obj.cur))
        if delta > 0:
            hp_obj.recover(delta)
        self._healed_total = delta

    def _is_in_own_sect_headquarter(self) -> bool:
        sect = getattr(self.avatar, "sect", None)
        if sect is None:
            return False
        tile = getattr(self.avatar, "tile", None)
        region = getattr(tile, "region", None)
        if not isinstance(region, SectRegion):
            return False
        hq_name = getattr(getattr(sect, "headquarter", None), "name", None) or getattr(sect, "name", None)
        return bool(hq_name) and region and region.name == hq_name

    def can_start(self) -> tuple[bool, str]:
        # 必须是宗门弟子且在自身宗门总部，且当前HP未满
        if getattr(self.avatar, "sect", None) is None:
            return False, "仅宗门弟子可用"
        if not self._is_in_own_sect_headquarter():
            return False, "需要位于自身宗门总部"
        hp_obj = getattr(self.avatar, "hp", None)
        if hp_obj is None:
            return False, "缺少HP信息"
        if not (hp_obj.cur < hp_obj.max):
            return False, "当前HP已满"
        return True, ""

    def start(self) -> Event:
        region = getattr(getattr(self.avatar, "tile", None), "region", None)
        region_name = getattr(region, "name", "宗门总部")
        # 重置累计量
        self._healed_total = 0
        return Event(self.world.month_stamp, f"{self.avatar.name} 在 {region_name} 开始静养疗伤", related_avatars=[self.avatar.id])

    # TimedAction 已统一 step 逻辑

    async def finish(self) -> list[Event]:
        healed_total = int(getattr(self, "_healed_total", 0))
        # 统一用一次事件简要反馈
        return [Event(self.world.month_stamp, f"{self.avatar.name} 疗伤完成，HP已回满（本次恢复{healed_total}点，当前HP {self.avatar.hp}）", related_avatars=[self.avatar.id])]


