from __future__ import annotations

import random
from src.classes.action import TimedAction
from src.classes.event import Event
from src.classes.region import NormalRegion


class Harvest(TimedAction):
    """
    采集动作，在有植物的区域进行采集，持续6个月
    可以获得植物对应的物品
    """

    COMMENT = "在当前区域采集植物，获取植物材料"
    DOABLES_REQUIREMENTS = "在有植物的普通区域，且avatar的境界必须大于等于植物的境界"
    PARAMS = {}

    duration_months = 6

    def _execute(self) -> None:
        """
        执行采集动作
        """
        region = self.avatar.tile.region
        plants = getattr(region, "plants", [])
        if len(plants) == 0:
            return
        available_plants = [
            plant for plant in plants
            if self.avatar.cultivation_progress.realm >= plant.realm
        ]
        if len(available_plants) == 0:
            return

        # 目前固定100%成功率
        if random.random() < 1.0:
            target_plant = random.choice(available_plants)
            # 随机选择该植物的一种物品
            item = random.choice(target_plant.items)
            # 基础获得1个，额外物品来自effects
            base_quantity = 1
            extra_items = int(self.avatar.effects.get("extra_harvest_items", 0) or 0)
            total_quantity = base_quantity + extra_items
            self.avatar.add_item(item, total_quantity)

    def can_start(self) -> tuple[bool, str]:
        region = self.avatar.tile.region
        if not isinstance(region, NormalRegion):
            return False, "当前不在普通区域"
        plants = getattr(region, "plants", [])
        if len(plants) == 0:
            return False, "当前区域没有植物"
        available_plants = [
            plant for plant in plants
            if self.avatar.cultivation_progress.realm >= plant.realm
        ]
        if len(available_plants) == 0:
            return False, "当前区域的植物境界过高"
        return True, ""

    def start(self) -> Event:
        region = self.avatar.tile.region
        return Event(self.world.month_stamp, f"{self.avatar.name} 在 {region.name} 开始采集", related_avatars=[self.avatar.id])

    # TimedAction 已统一 step 逻辑

    async def finish(self) -> list[Event]:
        return []


