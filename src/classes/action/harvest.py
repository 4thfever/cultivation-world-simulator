from __future__ import annotations

from src.classes.action import TimedAction
from src.classes.event import Event
from src.utils.gather import execute_gather, check_can_start_gather


class Harvest(TimedAction):
    """
    采集动作，在有植物的区域进行采集，持续6个月
    可以获得植物对应的材料
    """

    ACTION_NAME = "采集"
    EMOJI = "🌾"
    DESC = "在当前区域采集植物，获取植物材料"
    DOABLES_REQUIREMENTS = "在有植物的普通区域，且avatar的境界必须大于等于植物的境界"
    PARAMS = {}

    duration_months = 6

    def __init__(self, avatar, world):
        super().__init__(avatar, world)
        self.gained_materials: dict[str, int] = {}

    def _execute(self) -> None:
        """
        执行采集动作
        """
        gained = execute_gather(self.avatar, "plants", "extra_harvest_materials")
        for name, count in gained.items():
            self.gained_materials[name] = self.gained_materials.get(name, 0) + count

    def can_start(self) -> tuple[bool, str]:
        return check_can_start_gather(self.avatar, "plants", "植物")

    def start(self) -> Event:
        return Event(self.world.month_stamp, f"{self.avatar.name} 在 {self.avatar.tile.location_name} 开始采集", related_avatars=[self.avatar.id])

    # TimedAction 已统一 step 逻辑

    async def finish(self) -> list[Event]:
        # 必定有产出
        materials_desc = "、".join([f"{k}x{v}" for k, v in self.gained_materials.items()])
        return [Event(
            self.world.month_stamp,
            f"{self.avatar.name} 结束了采集，获得了：{materials_desc}",
            related_avatars=[self.avatar.id]
        )]
