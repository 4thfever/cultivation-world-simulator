from __future__ import annotations

from src.classes.action import TimedAction
from src.classes.event import Event
from src.utils.gather import execute_gather, check_can_start_gather


class Hunt(TimedAction):
    """
    狩猎动作，在有动物的区域进行狩猎，持续6个月
    可以获得动物对应的物品
    """

    ACTION_NAME = "狩猎"
    EMOJI = "🏹"
    DESC = "在当前区域狩猎动物，获取动物材料"
    DOABLES_REQUIREMENTS = "在有动物的普通区域，且avatar的境界必须大于等于动物的境界"
    PARAMS = {}

    duration_months = 6

    def __init__(self, avatar, world):
        super().__init__(avatar, world)
        self.gained_items: dict[str, int] = {}

    def _execute(self) -> None:
        """
        执行狩猎动作
        """
        gained = execute_gather(self.avatar, "animals", "extra_hunt_items")
        for name, count in gained.items():
            self.gained_items[name] = self.gained_items.get(name, 0) + count

    def can_start(self) -> tuple[bool, str]:
        return check_can_start_gather(self.avatar, "animals", "动物")

    def start(self) -> Event:
        return Event(self.world.month_stamp, f"{self.avatar.name} 在 {self.avatar.tile.location_name} 开始狩猎", related_avatars=[self.avatar.id])

    # TimedAction 已统一 step 逻辑

    async def finish(self) -> list[Event]:
        # 必定有产出
        items_desc = "、".join([f"{k}x{v}" for k, v in self.gained_items.items()])
        return [Event(
            self.world.month_stamp,
            f"{self.avatar.name} 结束了狩猎，获得了：{items_desc}",
            related_avatars=[self.avatar.id]
        )]
