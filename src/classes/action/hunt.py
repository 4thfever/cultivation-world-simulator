from __future__ import annotations

import random
from src.classes.action import TimedAction
from src.classes.event import Event
from src.classes.region import NormalRegion


class Hunt(TimedAction):
    """
    狩猎动作，在有动物的区域进行狩猎，持续6个月
    可以获得动物对应的物品
    """

    COMMENT = "在当前区域狩猎动物，获取动物材料"
    DOABLES_REQUIREMENTS = "在有动物的普通区域，且avatar的境界必须大于等于动物的境界"
    PARAMS = {}

    duration_months = 6

    def _execute(self) -> None:
        """
        执行狩猎动作
        """
        region = self.avatar.tile.region
        animals = getattr(region, "animals", [])
        if len(animals) == 0:
            return
        available_animals = [
            animal for animal in animals
            if self.avatar.cultivation_progress.realm >= animal.realm
        ]
        if len(available_animals) == 0:
            return

        # 目前固定100%成功率
        if random.random() < 1.0:
            target_animal = random.choice(available_animals)
            # 随机选择该动物的一种物品
            item = random.choice(target_animal.items)
            self.avatar.add_item(item, 1)

    def can_start(self) -> tuple[bool, str]:
        region = self.avatar.tile.region
        if not isinstance(region, NormalRegion):
            return False, "当前不在普通区域"
        animals = getattr(region, "animals", [])
        if len(animals) == 0:
            return False, "当前区域没有动物"
        available_animals = [
            animal for animal in animals
            if self.avatar.cultivation_progress.realm >= animal.realm
        ]
        if len(available_animals) == 0:
            return False, "当前区域的动物境界过高"
        return True, ""

    def start(self) -> Event:
        region = self.avatar.tile.region
        return Event(self.world.month_stamp, f"{self.avatar.name} 在 {region.name} 开始狩猎")

    # TimedAction 已统一 step 逻辑

    def finish(self) -> list[Event]:
        return []


