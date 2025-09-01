import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from src.classes.calendar import MonthStamp
from src.classes.action import Action, ALL_ACTION_CLASSES
from src.classes.world import World
from src.classes.tile import Tile, Region
from src.classes.cultivation import CultivationProgress
from src.classes.root import Root
from src.classes.age import Age
from src.classes.event import NULL_EVENT
from src.classes.typings import ACTION_NAME, ACTION_PARAMS, ACTION_PAIR

from src.classes.ai import AI, RuleAI, LLMAI
from src.classes.persona import Persona, personas_by_id
from src.utils.id_generator import get_avatar_id

class Gender(Enum):
    MALE = "male"
    FEMALE = "female"

    def __str__(self) -> str:
        return gender_strs.get(self, self.value)

gender_strs = {
    Gender.MALE: "男",
    Gender.FEMALE: "女",
}

# 历史动作对的最大数量
MAX_HISTORY_ACTIONS = 3

@dataclass
class Avatar:
    """
    NPC的类。
    包含了这个角色的一切信息。
    """
    world: World
    name: str
    id: str
    birth_month_stamp: MonthStamp
    age: Age
    gender: Gender
    cultivation_progress: CultivationProgress = field(default_factory=lambda: CultivationProgress(0))
    pos_x: int = 0
    pos_y: int = 0
    tile: Optional[Tile] = None

    root: Root = field(default_factory=lambda: random.choice(list(Root)))
    persona: Persona = field(default_factory=lambda: random.choice(list(personas_by_id.values())))
    ai: AI = None
    cur_action_pair: Optional[ACTION_PAIR] = None
    history_action_pairs: list[ACTION_PAIR] = field(default_factory=list)

    def __post_init__(self):
        """
        在Avatar创建后自动初始化tile和AI
        """
        self.tile = self.world.map.get_tile(self.pos_x, self.pos_y)
        # self.ai = LLMAI(self)
        self.ai = RuleAI(self)

    def __str__(self) -> str:
        """
        获取avatar的详细信息
        尽量多打一些，因为会用来给LLM进行决策
        """
        return f"Avatar(id={self.id}, 性别={self.gender}, 年龄={self.age}, name={self.name}, 区域={self.tile.region.name}, 灵根={self.root.value}, 境界={self.cultivation_progress})"

    def create_action(self, action_name: ACTION_NAME) -> Action:
        """
        根据动作名称创建新的action实例
        
        Args:
            action_name: 动作类的名称（如 'Cultivate', 'Breakthrough' 等）
        
        Returns:
            新创建的Action实例
        
        Raises:
            ValueError: 如果找不到对应的动作类
        """
        # 在所有动作类中查找对应的类
        for action_class in ALL_ACTION_CLASSES:
            if action_class.__name__ == action_name:
                return action_class(self, self.world)
        
        raise ValueError(f"未找到名为 '{action_name}' 的动作类")


    def act(self):
        """
        角色执行动作。
        实际上分为两步：决定做什么（decide）和实际去做（do）
        事件只在决定动作时产生，执行过程不产生事件
        """
        event = NULL_EVENT
        
        if self.cur_action_pair is None:
            # 决定动作时生成事件
            action_name, action_args, event = self.ai.decide(self.world)
            action = self.create_action(action_name)
            self.cur_action_pair = (action, action_args)
        
        # 纯粹执行动作，不产生事件
        action, action_params = self.cur_action_pair
        action.execute(**action_params)
        
        if action.is_finished(**action_params):
            # 将完成的动作对添加到历史记录中
            self._add_to_history(self.cur_action_pair)
        
        return event
    
    def _add_to_history(self, action_pair: ACTION_PAIR) -> None:
        """
        将完成的动作对添加到历史记录中
        
        Args:
            action_pair: 要添加的动作对
            
        注意:
            - 如果历史记录达到上限，会丢弃最老的记录
            - 新的记录会被添加到列表末尾
        """
        # 添加新的动作对到历史记录
        self.history_action_pairs.append(action_pair)
        self.cur_action_pair = None
        
        # 如果超过上限，移除最老的记录
        if len(self.history_action_pairs) > MAX_HISTORY_ACTIONS:
            self.history_action_pairs.pop(0)
    
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

    def update_age(self, current_month_stamp: MonthStamp):
        """
        更新年龄
        """
        self.age.update_age(current_month_stamp, self.birth_month_stamp)
    
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

    def is_in_region(self, region: Region) -> bool:
        return self.tile.region == region

def get_new_avatar_from_ordinary(world: World, current_month_stamp: MonthStamp, name: str, age: Age):
    """
    从凡人中来的新修士
    这代表其境界为最低
    """
    # 生成短ID，替代UUID4
    avatar_id = get_avatar_id()

    birth_month_stamp = current_month_stamp - age.age * 12 + random.randint(0, 11)  # 在出生年内随机选择月份
    cultivation_progress = CultivationProgress(0)
    pos_x = random.randint(0, world.map.width - 1)
    pos_y = random.randint(0, world.map.height - 1)
    gender = random.choice(list(Gender))

    return Avatar(
        world=world,
        name=name,
        id=avatar_id,
        birth_month_stamp=MonthStamp(birth_month_stamp),
        age=age,
        gender=gender,
        cultivation_progress=cultivation_progress,
        pos_x=pos_x,
        pos_y=pos_y,
    )
