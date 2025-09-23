import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List
import json

from src.classes.calendar import MonthStamp
from src.classes.action import Action
from src.classes.actions import ALL_ACTUAL_ACTION_CLASSES, ALL_ACTION_CLASSES, ALL_ACTUAL_ACTION_NAMES
from src.classes.world import World
from src.classes.tile import Tile
from src.classes.region import Region
from src.classes.cultivation import CultivationProgress
from src.classes.root import Root
from src.classes.age import Age
from src.classes.event import NULL_EVENT, Event
from src.classes.typings import ACTION_NAME, ACTION_PARAMS, ACTION_PAIR, ACTION_NAME_PARAMS_PAIRS, ACTION_NAME_PARAMS_PAIR

from src.classes.persona import Persona, personas_by_id, get_random_compatible_personas
from src.classes.item import Item
from src.classes.magic_stone import MagicStone
from src.classes.hp_and_mp import HP, MP, HP_MAX_BY_REALM, MP_MAX_BY_REALM
from src.utils.id_generator import get_avatar_id
from src.utils.config import CONFIG
from src.classes.relation import Relation

persona_num = CONFIG.avatar.persona_num

class Gender(Enum):
    MALE = "male"
    FEMALE = "female"

    def __str__(self) -> str:
        return gender_strs.get(self, self.value)

gender_strs = {
    Gender.MALE: "男",
    Gender.FEMALE: "女",
}

# 历史事件的最大数量
MAX_HISTORY_EVENTS = 10

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
    personas: List[Persona] = field(default_factory=list)
    cur_action_pair: Optional[ACTION_PAIR] = None
    history_events: List[Event] = field(default_factory=list)
    _pending_events: List[Event] = field(default_factory=list)
    next_actions: ACTION_NAME_PARAMS_PAIRS = field(default_factory=list)
    thinking: str = ""
    objective: str = ""
    magic_stone: MagicStone = field(default_factory=lambda: MagicStone(0)) # 灵石，即货币
    items: dict[Item, int] = field(default_factory=dict)
    hp: HP = field(default_factory=lambda: HP(0, 0))  # 将在__post_init__中初始化
    mp: MP = field(default_factory=lambda: MP(0, 0))  # 将在__post_init__中初始化
    relations: dict["Avatar", Relation] = field(default_factory=dict)

    def __post_init__(self):
        """
        在Avatar创建后自动初始化tile和HP/MP
        """
        self.tile = self.world.map.get_tile(self.pos_x, self.pos_y)
        
        # 根据当前境界初始化HP和MP
        max_hp = HP_MAX_BY_REALM.get(self.cultivation_progress.realm, 100)
        max_mp = MP_MAX_BY_REALM.get(self.cultivation_progress.realm, 100)
        self.hp = HP(max_hp, max_hp)
        self.mp = MP(max_mp, max_mp)

        # 最大寿元已在 Age 构造时基于境界初始化
        
        # 如果personas列表为空，则随机分配两个不互斥的persona
        if not self.personas:
            self.personas = get_random_compatible_personas(persona_num)

    def __hash__(self) -> int:
        return hash(self.id)

    def get_info(self) -> str:
        """
        获取avatar的详细信息
        尽量多打一些，因为会用来给LLM进行决策
        """
        personas_str = ", ".join([persona.name for persona in self.personas])
        return f"Avatar(id={self.id}, 性别={self.gender}, 年龄={self.age}, name={self.name}, 区域={self.tile.region.name}, 灵根={str(self.root)}, 境界={self.cultivation_progress}, HP={self.hp}, MP={self.mp}, 个性={personas_str})"

    def __str__(self) -> str:
        return self.get_info()

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

    def load_decide_result_chain(self, action_name_params_pairs: ACTION_NAME_PARAMS_PAIRS, avatar_thinking: str, objective: str):
        """
        加载AI的决策结果（动作链），立即设置第一个为当前动作，其余进入队列。
        """
        if not action_name_params_pairs:
            return
        first_action_name, first_action_params = action_name_params_pairs[0]
        action = self.create_action(first_action_name)
        self.thinking = avatar_thinking
        self.objective = objective
        self.cur_action_pair = (action, first_action_params)
        # 余下的动作进入队列
        if len(action_name_params_pairs) > 1:
            self.next_actions.extend(action_name_params_pairs[1:])

    def clear_next_actions(self) -> None:
        """
        清空后续动作队列（不影响当前动作）。
        """
        self.next_actions.clear()

    def has_next_actions(self) -> bool:
        return len(self.next_actions) > 0

    def pop_next_action_and_set_current(self) -> Optional[Event]:
        """
        从队列中取出下一个动作并设置为当前动作，同时返回开始事件。
        若队列为空则返回None。
        """
        if not self.next_actions:
            return None
        action_name, action_params = self.next_actions.pop(0)
        action = self.create_action(action_name)
        while not action.is_doable and self.next_actions:
            action_name, action_params = self.next_actions.pop(0)
            action = self.create_action(action_name)

        if not action.is_doable:
            return None

        self.cur_action_pair = (action, action_params)
        try:
            event = action.get_event(**action_params)
        except TypeError:
            # 兼容无参数的 get_event 定义
            event = action.get_event()
        return event

    def peek_next_action(self) -> Optional[ACTION_NAME_PARAMS_PAIR]:
        """
        查看下一个动作但不弹出。
        """
        if not self.next_actions:
            return None
        return self.next_actions[0]

    def is_next_action_doable(self) -> bool:
        """
        判断队列中的下一个动作当前是否可执行。
        若没有下一个动作，返回False。
        """
        pair = self.peek_next_action()
        if pair is None:
            return False
        action_name, _ = pair
        action = self.create_action(action_name)
        doable = action.is_doable
        assert isinstance(doable, bool)
        del action
        return doable

    async def act(self) -> List[Event]:
        """
        角色执行动作。
        注意这里只负责执行，不负责决定做什么动作。
        事件只在决定动作时产生，执行过程不产生事件
        """
        
        # 纯粹执行动作。具体事件由决定阶段或动作内部通过 add_event 添加
        action, action_params = self.cur_action_pair
        action.execute(**action_params)
        
        if action.is_finished(**action_params):
            # 完成后清空当前动作
            self.cur_action_pair = None
        # 返回并清空待派发事件
        events, self._pending_events = self._pending_events, []
        return events
    
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
    
    def add_item(self, item: Item, quantity: int = 1) -> None:
        """
        添加物品到背包
        
        Args:
            item: 要添加的物品
            quantity: 添加数量，默认为1
        """
        if quantity <= 0:
            return
            
        if item in self.items:
            self.items[item] += quantity
        else:
            self.items[item] = quantity
    
    def remove_item(self, item: Item, quantity: int = 1) -> bool:
        """
        从背包移除物品
        
        Args:
            item: 要移除的物品
            quantity: 移除数量，默认为1
            
        Returns:
            bool: 是否成功移除（如果物品不足则返回False）
        """
        if quantity <= 0:
            return True
            
        if item not in self.items:
            return False
            
        if self.items[item] < quantity:
            return False
            
        self.items[item] -= quantity
        
        # 如果数量为0，从字典中移除该物品
        if self.items[item] == 0:
            del self.items[item]
            
        return True
    
    def has_item(self, item: Item, quantity: int = 1) -> bool:
        """
        检查是否拥有足够数量的物品
        
        Args:
            item: 要检查的物品
            quantity: 需要的数量，默认为1
            
        Returns:
            bool: 是否拥有足够数量的物品
        """
        return item in self.items and self.items[item] >= quantity
    
    def get_item_quantity(self, item: Item) -> int:
        """
        获取指定物品的数量
        
        Args:
            item: 要查询的物品
            
        Returns:
            int: 物品数量，如果没有该物品则返回0
        """
        return self.items.get(item, 0)

    def add_event(self, event: Event, *, to_sidebar: bool = True, to_history: bool = True) -> None:
        """
        添加事件：
        - to_sidebar: 是否进入全局侧边栏（通过 Simulator 收集）
        - to_history: 是否进入本角色的历史事件（最多保留 MAX_HISTORY_EVENTS 条）
        """
        if to_sidebar:
            self._pending_events.append(event)
        if to_history:
            self.history_events.append(event)
            if len(self.history_events) > MAX_HISTORY_EVENTS:
                self.history_events = self.history_events[-MAX_HISTORY_EVENTS:]

    def get_action_space_str(self) -> str:
        action_space = self.get_action_space()
        action_space_str = json.dumps(action_space, ensure_ascii=False)
        return action_space_str
    
    def get_action_space(self) -> list[dict]:
        """
        获取动作空间
        """
        actual_actions = [self.create_action(action_cls_name) for action_cls_name in ALL_ACTUAL_ACTION_NAMES]
        doable_actions = [action for action in actual_actions if action.is_doable]
        action_space = [action.name for action in doable_actions]
        return action_space

    def get_prompt_info(self, co_region_avatars: Optional[List["Avatar"]] = None) -> str:
        """
        获取角色提示词信息
        """
        info = self.get_info()
        action_space = self.get_action_space_str()
        
        # 构建personas的提示词信息
        personas_prompts = []
        for i, persona in enumerate(self.personas, 1):
            personas_prompts.append(f"个性{i}：{persona.prompt}")
        personas_info = "\n".join(personas_prompts)
        
        # 添加灵石信息
        magic_stone_info = f"灵石持有情况：{str(self.magic_stone)}"
        
        # 添加物品信息
        if self.items:
            items_info = "物品持有情况：" + "，".join([f"{item.name}x{quantity}" for item, quantity in self.items.items()])
        else:
            items_info = "物品持有情况：无"
        
        # 同区域角色（可选）
        co_region_info = ""
        if co_region_avatars:
            entries: list[str] = []
            for other in co_region_avatars[:8]:
                entries.append(f"{other.name}(境界：{other.cultivation_progress.get_simple_info()})")
            co_region_info = "\n同区域角色：" + ("，".join(entries) if entries else "无")

        # 关系摘要
        relations_summary = self._get_relations_summary_str()

        # 历史事件摘要
        if self.history_events:
            history_lines = "；".join([str(e) for e in self.history_events[-8:]])
            history_info = f"历史事件：{history_lines}"
        else:
            history_info = "历史事件：无"

        return f"{info}\n{personas_info}\n{magic_stone_info}\n{items_info}\n{history_info}\n关系：{relations_summary}\n{co_region_info}\n该角色的目前合法动作为：{action_space}"

    def set_relation(self, other: "Avatar", relation: Relation) -> None:
        """
        设置与另一个角色的关系（对称）。
        """
        if other is self:
            return
        self.relations[other] = relation
        # 保持对称
        if getattr(other, "relations", None) is not None:
            other.relations[self] = relation

    def get_relation(self, other: "Avatar") -> Optional[Relation]:
        return self.relations.get(other)

    def clear_relation(self, other: "Avatar") -> None:
        self.relations.pop(other, None)
        if getattr(other, "relations", None) is not None:
            other.relations.pop(self, None)

    def _get_relations_summary_str(self, max_count: int = 8) -> str:
        entries: list[str] = []
        for other in self.relations.keys():
            entries.append(self.get_other_avatar_info(other))
        if not entries:
            return "无"
        return "，".join(entries[:max_count])

    def get_co_region_avatars(self, avatars: List["Avatar"]) -> List["Avatar"]:
        """
        返回与自己处于同一区域的角色列表（不含自己）。
        """
        if self.tile is None:
            return []
        same_region: list[Avatar] = []
        for other in avatars:
            if other is self or other.tile is None:
                continue
            if other.tile.region == self.tile.region:
                same_region.append(other)
        return same_region

    def get_other_avatar_info(self, other_avatar: "Avatar") -> str:
        """
        仅显示三个字段：名字、境界、关系。
        """
        relation = self.get_relation(other_avatar)
        relation_str = str(relation)
        return f"{other_avatar.name}，境界：{other_avatar.cultivation_progress.get_simple_info()}，关系：{relation_str}"

    @property
    def move_step_length(self) -> int:
        """
        获取角色的移动步长
        """
        return self.cultivation_progress.get_move_step()

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
