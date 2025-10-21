from __future__ import annotations

import random
from src.classes.action import TimedAction
from src.classes.event import Event
from src.classes.region import NormalRegion
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.classes.animal import Animal


class Hunt(TimedAction):
    """
    狩猎动作，在有动物的区域进行狩猎，持续6个月
    可以获得动物对应的物品
    """

    COMMENT = "在当前区域狩猎动物，获取动物材料"
    DOABLES_REQUIREMENTS = "在有动物的普通区域，且avatar的境界必须大于等于动物的境界"
    PARAMS = {}

    def get_available_animals(self) -> list[Animal]:
        """
        获取avatar境界足够的动物
        """
        region = self.avatar.tile.region
        avatar_realm = self.avatar.cultivation_progress.realm
        return [animal for animal in region.animals if avatar_realm >= animal.realm]

    duration_months = 6

    def _execute(self) -> None:
        """
        执行狩猎动作
        """
        success_rate = self.get_success_rate()
        available_animals = self.get_available_animals()
        if len(available_animals) == 0:
            return

        if random.random() < success_rate:
            # 成功狩猎，从avatar境界足够的动物中随机选择一种
            target_animal = random.choice(available_animals)
            # 随机选择该动物的一种物品
            item = random.choice(target_animal.items)
            self.avatar.add_item(item, 1)

    def get_success_rate(self) -> float:
        """
        获取狩猎成功率，预留接口，目前固定为100%
        """
        return 1.0  # 100%成功率

    def can_start(self) -> tuple[bool, str]:
        region = self.avatar.tile.region
        if not isinstance(region, NormalRegion):
            return False, "当前不在普通区域"
        available_animals = self.get_available_animals()
        if len(available_animals) == 0:
            return False, "当前区域无可狩猎的动物或其境界过高"
        return True, ""

    def start(self) -> Event:
        region = self.avatar.tile.region
        return Event(self.world.month_stamp, f"{self.avatar.name} 在 {region.name} 开始狩猎")

    # TimedAction 已统一 step 逻辑

    def finish(self) -> list[Event]:
        return []


