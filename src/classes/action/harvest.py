from __future__ import annotations

import random
from src.classes.action import TimedAction
from src.classes.event import Event
from src.classes.region import NormalRegion
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.classes.plant import Plant


class Harvest(TimedAction):
    """
    采集动作，在有植物的区域进行采集，持续6个月
    可以获得植物对应的物品
    """

    COMMENT = "在当前区域采集植物，获取植物材料"
    DOABLES_REQUIREMENTS = "在有植物的普通区域，且avatar的境界必须大于等于植物的境界"
    PARAMS = {}

    def get_available_plants(self) -> list[Plant]:
        """
        获取avatar境界足够的植物
        """
        region = self.avatar.tile.region
        avatar_realm = self.avatar.cultivation_progress.realm
        return [plant for plant in region.plants if avatar_realm >= plant.realm]

    duration_months = 6

    def _execute(self) -> None:
        """
        执行采集动作
        """
        success_rate = self.get_success_rate()
        available_plants = self.get_available_plants()
        if len(available_plants) == 0:
            return

        if random.random() < success_rate:
            # 成功采集，从avatar境界足够的植物中随机选择一种
            target_plant = random.choice(available_plants)
            # 随机选择该植物的一种物品
            item = random.choice(target_plant.items)
            self.avatar.add_item(item, 1)

    def get_success_rate(self) -> float:
        """
        获取采集成功率，预留接口，目前固定为100%
        """
        return 1.0  # 100%成功率

    def can_start(self) -> bool:
        region = self.avatar.tile.region
        if not isinstance(region, NormalRegion):
            return False
        avaliable_plants = self.get_available_plants()
        if len(avaliable_plants) == 0:
            return False
        return True

    def start(self) -> Event:
        region = self.avatar.tile.region
        return Event(self.world.month_stamp, f"{self.avatar.name} 在 {region.name} 开始采集", related_avatars=[self.avatar.id])

    # TimedAction 已统一 step 逻辑

    def finish(self) -> list[Event]:
        return []


