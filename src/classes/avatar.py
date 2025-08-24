import random
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from src.classes.calendar import Month, Year
from src.classes.action import Action, Move, Cultivate
from src.classes.world import World
from src.classes.tile import Tile
from src.classes.cultivation import CultivationProgress, Realm
from src.classes.root import Root
from src.classes.age import Age
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
    id: str
    birth_month: Month
    birth_year: Year
    age: Age
    gender: Gender
    cultivation_progress: CultivationProgress = field(default_factory=lambda: CultivationProgress(0))
    pos_x: int = 0
    pos_y: int = 0
    tile: Optional[Tile] = None
    actions: dict[str, Action] = field(default_factory=dict)
    root: Root = field(default_factory=lambda: random.choice(list(Root)))

    def __post_init__(self):
        """
        在Avatar创建后自动绑定基础动作
        """
        self._bind_basic_actions()

    def _bind_basic_actions(self):
        """
        绑定基础动作，如移动等
        """
        self.bind_action(Move)
        self.bind_action(Cultivate)


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
    
    def update_cultivation(self, new_level: int):
        """
        更新修仙进度，并在境界提升时更新寿命
        """
        old_realm = self.cultivation_progress.realm
        self.cultivation_progress.level = new_level
        self.cultivation_progress.realm = self.cultivation_progress.get_realm(new_level)
        
        # 如果境界提升了，更新寿命期望
        if self.cultivation_progress.realm != old_realm:
            self.age.update_realm(self.cultivation_progress.realm)
    
    def death_by_old_age(self) -> bool:
        """
        检查是否老死
        
        返回:
            如果老死返回True，否则返回False
        """
        return self.age.death_by_old_age(self.cultivation_progress.realm)

    def update_age(self, current_month: Month, current_year: Year):
        """
        更新年龄
        """
        self.age.update_age(current_month, current_year, self.birth_month, self.birth_year)
    
    def get_age_info(self) -> dict:
        """
        获取年龄相关信息
        
        返回:
            包含年龄、期望寿命、死亡概率等信息的字典
        """
        current_age, expected_lifespan = self.age.get_lifespan_progress()
        death_probability = self.age.get_death_probability()
        
        return {
            "current_age": round(current_age, 2),
            "expected_lifespan": expected_lifespan,
            "is_elderly": self.age.is_elderly(),
            "death_probability": round(death_probability, 4),
            "realm": self.cultivation_progress.realm.value
        }

def get_new_avatar_from_ordinary(world: World, current_year: Year, name: str, age: Age):
    """
    从凡人中来的新修士
    这代表其境界为最低
    """
    # 利用uuid功能生成id
    avatar_id = str(uuid.uuid4())

    birth_year = current_year - age.age
    birth_month = random.choice(list(Month))
    cultivation_progress = CultivationProgress(0)
    pos_x = random.randint(0, world.map.width)
    pos_y = random.randint(0, world.map.height)
    gender = random.choice(list(Gender))

    return Avatar(
        world=world,
        name=name,
        id=avatar_id,
        birth_month=birth_month,
        birth_year=birth_year,
        age=age,
        gender=gender,
        cultivation_progress=cultivation_progress,
        pos_x=pos_x,
        pos_y=pos_y,
    )