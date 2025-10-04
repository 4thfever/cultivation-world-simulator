from __future__ import annotations

import random
from src.classes.action import TimedAction
from src.classes.event import Event
from src.classes.root import get_essence_types_for_root
from src.classes.region import CultivateRegion


class Cultivate(TimedAction):
    """
    修炼动作，可以增加修仙进度。
    """

    COMMENT = "修炼，增进修为"
    DOABLES_REQUIREMENTS = "在修炼区域中，修炼区域的灵气为角色的灵根之一，且角色未到瓶颈。"
    PARAMS = {}

    duration_months = 10

    def _execute(self) -> None:
        """
        修炼
        获得的exp增加取决于essence的对应灵根的大小。
        """
        root = self.avatar.root
        essence = self.avatar.tile.region.essence
        # 多元素：取与角色灵根任一匹配元素的最大密度
        essence_types = get_essence_types_for_root(root)
        essence_density = max((essence.get_density(et) for et in essence_types), default=0)
        exp = self.get_exp(essence_density)
        self.avatar.cultivation_progress.add_exp(exp)

    def get_exp(self, essence_density: int) -> int:
        """
        根据essence的密度，计算获得的exp。
        公式为：base * essence_density
        """
        if self.avatar.cultivation_progress.is_in_bottleneck():
            return 0
        base = 100
        return base * essence_density

    def can_start(self) -> bool:
        root = self.avatar.root
        region = self.avatar.tile.region
        essence_types = get_essence_types_for_root(root)
        if not self.avatar.cultivation_progress.can_cultivate():
            return False
        if not isinstance(region, CultivateRegion):
            return False
        if all(region.essence.get_density(et) == 0 for et in essence_types):
            return False
        return True

    def start(self) -> Event:
        return Event(self.world.month_stamp, f"{self.avatar.name} 在 {self.avatar.tile.region.name} 开始修炼")

    # TimedAction 已统一 step 逻辑

    def finish(self) -> list[Event]:
        return []


