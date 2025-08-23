import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from src.classes.calendar import Month, Year
from src.classes.action import Action
from src.classes.world import World
from src.classes.tile import Tile
from src.classes.cultivation import CultivationProgress
from src.classes.root import Root
from src.utils.strings import to_snake_case

class Gender(Enum):
    MALE = "male"
    FEMALE = "female"

    def __str__(self) -> str:
        return gender_strs.get(self, self.value)

gender_strs = {
    Gender.MALE: "男",
    Gender.FEMALE: "女",
}

@dataclass
class Avatar:
    """
    NPC的类。
    包含了这个角色的一切信息。
    """
    world: World
    name: str
    id: int
    birth_month: Month
    birth_year: Year
    age: int
    gender: Gender
    cultivation_progress: CultivationProgress = field(default_factory=lambda: CultivationProgress(0))
    pos_x: int = 0
    pos_y: int = 0
    tile: Optional[Tile] = None
    actions: dict[str, Action] = field(default_factory=dict)
    root: Root = field(default_factory=lambda: random.choice(list(Root)))


    def bind_action(self, action_class: type[Action]):
        """
        绑定一个action到avatar
        """
        # 以类名为键保存实例，保持可追踪性
        self.actions[action_class.__name__] = action_class(self, self.world)

        # 同时挂载一个便捷方法，名称为蛇形（MoveFast -> move_fast），并转发参数
        method_name = to_snake_case(action_class.__name__)

        def _wrapper(*args, **kwargs):
            return self.actions[action_class.__name__].execute(*args, **kwargs)

        setattr(self, method_name, _wrapper)


    def act(self):
        """
        角色执行动作。
        实际上分为两步：决定做什么（decide）和实习上去做（do）
        """
        action_name, action_args = self.decide()
        action = self.actions[action_name]
        action.execute(**action_args)

    def decide(self):
        """
        决定做什么。
        """
        # 目前只做一个事情，就是随机移动。
        return "Move", {"delta_x": random.randint(-1, 1), "delta_y": random.randint(-1, 1)}