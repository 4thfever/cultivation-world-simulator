from __future__ import annotations

import random
from src.classes.action import TimedAction
from src.classes.event import Event
from src.classes.region import NormalRegion


class Mine(TimedAction):
    """
    挖矿动作，在有矿脉的区域进行挖矿，持续6个月
    可以获得矿脉对应的矿石
    """

    ACTION_NAME = "挖矿"
    EMOJI = "⛏️"
    DESC = "在当前区域挖掘矿脉，获取矿石材料"
    DOABLES_REQUIREMENTS = "在有矿脉的普通区域，且avatar的境界必须大于等于矿脉的境界"
    PARAMS = {}

    duration_months = 6

    def _execute(self) -> None:
        """
        执行挖矿动作
        """
        region = self.avatar.tile.region
        lodes = getattr(region, "lodes", [])
        if len(lodes) == 0:
            return
        available_lodes = [
            lode for lode in lodes
            if self.avatar.cultivation_progress.realm >= lode.realm
        ]
        if len(available_lodes) == 0:
            return

        # 目前固定100%成功率
        if random.random() < 1.0:
            target_lode = random.choice(available_lodes)
            # 随机选择该矿脉的一种物品
            item = random.choice(target_lode.items)
            # 基础获得1个，额外物品来自effects
            base_quantity = 1
            extra_items = int(self.avatar.effects.get("extra_mine_items", 0) or 0)
            total_quantity = base_quantity + extra_items
            self.avatar.add_item(item, total_quantity)

    def can_start(self) -> tuple[bool, str]:
        region = self.avatar.tile.region
        if not isinstance(region, NormalRegion):
            return False, "当前不在普通区域"
        lodes = getattr(region, "lodes", [])
        if len(lodes) == 0:
            return False, "当前区域没有矿脉"
        available_lodes = [
            lode for lode in lodes
            if self.avatar.cultivation_progress.realm >= lode.realm
        ]
        if len(available_lodes) == 0:
            return False, "当前区域的矿脉境界过高"
        return True, ""

    def start(self) -> Event:
        region = self.avatar.tile.region
        return Event(self.world.month_stamp, f"{self.avatar.name} 在 {self.avatar.tile.location_name} 开始挖矿", related_avatars=[self.avatar.id])

    # TimedAction 已统一 step 逻辑

    async def finish(self) -> list[Event]:
        return []

