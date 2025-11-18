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
        # 结算额外修炼经验（来自功法/宗门/灵根等已合并）
        extra_exp = int(self.avatar.effects.get("extra_cultivate_exp", 0) or 0)
        if extra_exp:
            exp += extra_exp
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

    def can_start(self) -> tuple[bool, str]:
        root = self.avatar.root
        region = self.avatar.tile.region
        essence_types = get_essence_types_for_root(root)
        if not self.avatar.cultivation_progress.can_cultivate():
            return False, "修为已达瓶颈，无法继续修炼"
        if not isinstance(region, CultivateRegion):
            return False, "当前不在修炼区域"
        if all(region.essence.get_density(et) == 0 for et in essence_types):
            return False, "当前区域无与灵根相符的灵气"
        return True, ""

    def start(self) -> Event:
        # 计算修炼时长缩减
        reduction = float(self.avatar.effects.get("cultivate_duration_reduction", 0.0))
        reduction = max(0.0, min(0.9, reduction))  # 限制在 [0, 0.9] 范围内
        
        # 动态设置此次修炼的实际duration（四舍五入确保为整数月份）
        base_duration = self.__class__.duration_months
        actual_duration = max(1, round(base_duration * (1.0 - reduction)))
        self.duration_months = actual_duration
        
        return Event(self.world.month_stamp, f"{self.avatar.name} 在 {self.avatar.tile.region.name} 开始修炼", related_avatars=[self.avatar.id])

    # TimedAction 已统一 step 逻辑

    async def finish(self) -> list[Event]:
        return []


