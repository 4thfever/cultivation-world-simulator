from __future__ import annotations

from src.i18n import t
from src.classes.action import TimedAction
from src.classes.event import Event
from src.utils.gather import execute_gather, check_can_start_gather
from src.classes.race import is_yao_avatar


class Harvest(TimedAction):
    """
    采集动作，在有植物的区域进行采集，持续6个月
    可以获得植物对应的材料
    """
    
    # 多语言 ID
    ACTION_NAME_ID = "harvest_action_name"
    DESC_ID = "harvest_description"
    REQUIREMENTS_ID = "harvest_requirements"
    
    # 不需要翻译的常量
    EMOJI = "🌾"
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
        if is_yao_avatar(self.avatar):
            content = t("{avatar} follows wild instincts to seek spiritual herbs at {location}",
                       avatar=self.avatar.name, location=self.avatar.tile.location_name)
        else:
            content = t("{avatar} begins harvesting at {location}",
                       avatar=self.avatar.name, location=self.avatar.tile.location_name)
        return Event(self.world.month_stamp, content, related_avatars=[self.avatar.id])

    # TimedAction 已统一 step 逻辑

    async def finish(self) -> list[Event]:
        # 必定有产出
        materials_desc = ", ".join([f"{k}x{v}" for k, v in self.gained_materials.items()])
        if is_yao_avatar(self.avatar):
            content = t("{avatar} finished foraging through the wilds, obtained: {materials}",
                       avatar=self.avatar.name, materials=materials_desc)
        else:
            content = t("{avatar} finished harvesting, obtained: {materials}",
                       avatar=self.avatar.name, materials=materials_desc)
        return [Event(
            self.world.month_stamp,
            content,
            related_avatars=[self.avatar.id]
        )]
