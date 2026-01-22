from __future__ import annotations

from src.i18n import t
from src.classes.action import TimedAction
from src.classes.event import Event
from src.utils.gather import execute_gather, check_can_start_gather


class Hunt(TimedAction):
    """
    狩猎动作，在有动物的区域进行狩猎，持续6个月
    可以获得动物对应的材料
    """
    
    # 多语言 ID
    ACTION_NAME_ID = "hunt_action_name"
    DESC_ID = "hunt_description"
    REQUIREMENTS_ID = "hunt_requirements"
    
    # 不需要翻译的常量
    EMOJI = "🏹"
    PARAMS = {}

    duration_months = 6

    def __init__(self, avatar, world):
        super().__init__(avatar, world)
        self.gained_materials: dict[str, int] = {}

    def _execute(self) -> None:
        """
        执行狩猎动作
        """
        gained = execute_gather(self.avatar, "animals", "extra_hunt_materials")
        for name, count in gained.items():
            self.gained_materials[name] = self.gained_materials.get(name, 0) + count

    def can_start(self) -> tuple[bool, str]:
        return check_can_start_gather(self.avatar, "animals", "动物")

    def start(self) -> Event:
        content = t("{avatar} begins hunting at {location}",
                   avatar=self.avatar.name, location=self.avatar.tile.location_name)
        return Event(self.world.month_stamp, content, related_avatars=[self.avatar.id])

    # TimedAction 已统一 step 逻辑

    async def finish(self) -> list[Event]:
        # 必定有产出
        materials_desc = ", ".join([f"{k}x{v}" for k, v in self.gained_materials.items()])
        content = t("{avatar} finished hunting, obtained: {materials}",
                   avatar=self.avatar.name, materials=materials_desc)
        return [Event(
            self.world.month_stamp,
            content,
            related_avatars=[self.avatar.id]
        )]
