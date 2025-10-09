import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List
import json

from src.classes.calendar import MonthStamp
from src.classes.action import Action
from src.classes.action_runtime import ActionStatus, ActionResult
from src.classes.action.registry import ActionRegistry
from src.classes.world import World
from src.classes.tile import Tile
from src.classes.region import Region
from src.classes.cultivation import CultivationProgress
from src.classes.root import Root
from src.classes.technique import Technique, get_random_technique_for_avatar, get_technique_by_sect
from src.classes.age import Age
from src.classes.event import NULL_EVENT, Event
from src.classes.typings import ACTION_NAME, ACTION_PARAMS, ACTION_NAME_PARAMS_PAIRS, ACTION_NAME_PARAMS_PAIR
from src.classes.action_runtime import ActionPlan, ActionInstance

from src.classes.persona import Persona, personas_by_id, get_random_compatible_personas
from src.classes.item import Item
from src.classes.magic_stone import MagicStone
from src.classes.hp_and_mp import HP, MP, HP_MAX_BY_REALM, MP_MAX_BY_REALM
from src.utils.id_generator import get_avatar_id
from src.utils.config import CONFIG
from src.classes.relation import Relation, get_reciprocal
from src.run.log import get_logger
from src.classes.alignment import Alignment
from src.utils.params import filter_kwargs_for_callable
from src.classes.sect import Sect

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
    technique: Technique | None = None
    history_events: List[Event] = field(default_factory=list)
    _pending_events: List[Event] = field(default_factory=list)
    current_action: Optional[ActionInstance] = None
    planned_actions: List[ActionPlan] = field(default_factory=list)
    thinking: str = ""
    objective: str = ""
    magic_stone: MagicStone = field(default_factory=lambda: MagicStone(0)) # 灵石，即货币
    items: dict[Item, int] = field(default_factory=dict)
    hp: HP = field(default_factory=lambda: HP(0, 0))  # 将在__post_init__中初始化
    mp: MP = field(default_factory=lambda: MP(0, 0))  # 将在__post_init__中初始化
    relations: dict["Avatar", Relation] = field(default_factory=dict)
    alignment: Alignment | None = None
    # 所属宗门（可为空，表示散修/无门无派）
    sect: Sect | None = None
    # 当月/当步新设动作标记：在 commit_next_plan 设为 True，首次 tick_action 后清为 False
    _new_action_set_this_step: bool = False

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
        
        # 如果personas列表为空，则随机分配两个符合条件且不互斥的persona
        if not self.personas:
            self.personas = get_random_compatible_personas(persona_num, avatar=self)

        # 出生即按宗门分配功法：
        # - 散修：仅从无宗门功法抽样
        # - 有宗门：从“无宗门 + 本宗门”集合抽样
        if self.technique is None:
            self.technique = get_technique_by_sect(self.sect)

        # 若未设定阵营，则依据宗门/无门无派规则设置，避免后续为 None
        if self.alignment is None:
            if self.sect is not None:
                self.alignment = self.sect.alignment
            else:
                from src.classes.alignment import Alignment as _Alignment
                self.alignment = random.choice(list(_Alignment))

    def __hash__(self) -> int:
        return hash(self.id)

    def get_info(self) -> str:
        """
        获取avatar的详细信息
        尽量多打一些，因为会用来给LLM进行决策
        """
        personas_str = ", ".join([persona.name for persona in self.personas])
        technique_str = self.technique.name if self.technique is not None else "无"
        sect_str = self.get_sect_str()
        region_name = self.tile.region.name if self.tile.region is not None else "无"
        return f"Avatar(id={self.id}, 性别={self.gender}, 年龄={self.age}, name={self.name}, 宗门={sect_str}, 阵营={self.alignment.get_info()}, 区域={region_name}, 灵根={str(self.root)}, 功法={technique_str}, 境界={self.cultivation_progress}, HP={self.hp}, MP={self.mp}, 个性={personas_str})"

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
        action_cls = ActionRegistry.get(action_name)
        return action_cls(self, self.world)

    def load_decide_result_chain(self, action_name_params_pairs: ACTION_NAME_PARAMS_PAIRS, avatar_thinking: str, objective: str):
        """
        加载AI的决策结果（动作链），立即设置第一个为当前动作，其余进入队列。
        """
        if not action_name_params_pairs:
            return
        self.thinking = avatar_thinking
        self.objective = objective
        # 转为计划并入队（不立即提交，交由提交阶段统一触发开始事件）
        plans: List[ActionPlan] = [ActionPlan(name, params) for name, params in action_name_params_pairs]
        self.planned_actions.extend(plans)

    def clear_plans(self) -> None:
        self.planned_actions.clear()

    def has_plans(self) -> bool:
        return len(self.planned_actions) > 0

    def commit_next_plan(self) -> Optional[Event]:
        """
        提交下一个可启动的计划为当前动作；返回开始事件（若有）。
        """
        if self.current_action is not None:
            return None
        while self.planned_actions:
            plan = self.planned_actions.pop(0)
            action = self.create_action(plan.action_name)
            # 再验证
            params_for_can_start = filter_kwargs_for_callable(action.can_start, plan.params)
            can_start = bool(action.can_start(**params_for_can_start))
            if not can_start:
                # 记录不合法动作
                logger = get_logger().logger
                logger.warning("非法动作: Avatar(name=%s,id=%s) 的动作 %s 参数=%s 无法启动", self.name, self.id, plan.action_name, plan.params)
                continue
            # 启动
            params_for_start = filter_kwargs_for_callable(action.start, plan.params)
            start_event = action.start(**params_for_start)
            self.current_action = ActionInstance(action=action, params=plan.params, status="running")
            # 标记为“本轮新设动作”，用于本月补充执行
            self._new_action_set_this_step = True
            return start_event
        return None

    def peek_next_plan(self) -> Optional[ActionPlan]:
        if not self.planned_actions:
            return None
        return self.planned_actions[0]

    async def tick_action(self) -> List[Event]:
        """
        推进当前动作一步；返回过程中由动作内部产生的事件（通过 add_event 收集）。
        """
        if self.current_action is None:
            return []
        # 记录当前动作实例引用，用于检测执行过程中是否发生了“抢占/切换”
        action_instance_before = self.current_action
        action = action_instance_before.action
        params = action_instance_before.params
        params_for_step = filter_kwargs_for_callable(action.step, params)
        result: ActionResult = action.step(**params_for_step)
        if result.status == ActionStatus.COMPLETED:
            params_for_finish = filter_kwargs_for_callable(action.finish, params)
            finish_events = action.finish(**params_for_finish)
            # 仅当当前动作仍然是刚才执行的那个实例时才清空
            # 若在 step() 内部通过“抢占”机制切换了动作（如 Escape 失败立即切到 Battle），不要清空新动作
            if self.current_action is action_instance_before:
                self.current_action = None
            if finish_events:
                # 允许 finish 直接返回事件（极少用），统一并入 pending
                for e in finish_events:
                    self._pending_events.append(e)
        # 合并动作返回的事件（通常为空）
        if result.events:
            for e in result.events:
                self._pending_events.append(e)
        events, self._pending_events = self._pending_events, []
        # 本轮已执行过，清除“新设动作”标记
        self._new_action_set_this_step = False
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

    def is_in_region(self, region: Region|None) -> bool:
        current_region = self.tile.region
        if current_region is None:
            tile = self.world.map.get_tile(self.pos_x, self.pos_y)
            current_region = tile.region
        return current_region == region
    
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
        from src.classes.actions import ALL_ACTUAL_ACTION_NAMES
        actual_actions = [self.create_action(action_cls_name) for action_cls_name in ALL_ACTUAL_ACTION_NAMES]
        doable_actions: list[Action] = []
        for action in actual_actions:
            # 用 can_start 的无参形式，用于“是否在动作空间中显示”
            if action.can_start():
                doable_actions.append(action)
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
        
        # 观测范围内角色（沿用参数名保持兼容）
        co_region_info = ""
        if co_region_avatars:
            entries: list[str] = []
            for other in co_region_avatars[:8]:
                entries.append(f"{other.name}(境界：{other.cultivation_progress.get_simple_info()})")
            co_region_info = "\n观测范围内角色：" + ("，".join(entries) if entries else "无")

        # 关系摘要
        relations_summary = self._get_relations_summary_str()

        # 宗门信息
        sect_name = self.get_sect_str()
        if self.sect is not None:
            sect_info = f"{sect_name}，风格：{self.sect.member_act_style}，驻地：{self.sect.headquarter.name}"
        else: # 散修
            sect_info = sect_name

        # 历史事件摘要
        if self.history_events:
            history_lines = "；".join([str(e) for e in self.history_events[-8:]])
            history_info = f"历史事件：{history_lines}"
        else:
            history_info = "历史事件：无"

        return f"{info}\n{sect_info}\n{personas_info}\n{magic_stone_info}\n{items_info}\n{history_info}\n关系：{relations_summary}\n{co_region_info}\n该角色的目前合法动作为：{action_space}"

    def get_hover_info(self) -> list[str]:
        """
        返回用于前端悬浮提示的多行信息。
        """
        lines: list[str] = [
            f"{self.name}",
            f"性别: {self.gender}",
            f"年龄: {self.age}",
            f"阵营: {self.alignment}",
            f"境界: {str(self.cultivation_progress)}",
            f"HP: {self.hp}",
            f"MP: {self.mp}",
        ]
        lines.append(f"宗门: {self.get_sect_str()}")
        from src.classes.root import format_root_cn
        lines.append(f"灵根: {format_root_cn(self.root)}")
        if self.technique is not None:
            lines.append(f"功法: {self.technique.name}（{self.technique.attribute}·{self.technique.grade.value}）")
        else:
            lines.append("功法: 无")
        if self.personas:
            lines.append(f"个性: {', '.join([persona.name for persona in self.personas])}")
        lines.append(f"位置: ({self.pos_x}, {self.pos_y})")
        lines.append(f"灵石: {str(self.magic_stone)}")
        if self.items:
            lines.append("物品:")
            for item, quantity in self.items.items():
                lines.append(f"  {item.name} x{quantity}")
        else:
            lines.append("")
            lines.append("物品: 无")
        if self.thinking:
            lines.append("")
            lines.append("思考:")
            from src.utils.text_wrap import wrap_text
            lines.extend(wrap_text(self.thinking, 28))
        if getattr(self, "objective", None):
            lines.append("")
            lines.append("目标:")
            from src.utils.text_wrap import wrap_text
            lines.extend(wrap_text(self.objective, 28))

        # 关系信息
        lines.append("")
        relations_list = [f"{other.name}({str(relation)})" for other, relation in getattr(self, "relations", {}).items()]
        if relations_list:
            lines.append("关系:")
            for s in relations_list[:6]:
                lines.append(f"  {s}")
        else:
            lines.append("关系: 无")
        return lines

    def get_sect_str(self) -> str:
        """
        获取宗门显示名：有宗门则返回宗门名，否则返回"散修"。
        """
        return self.sect.name if self.sect is not None else "散修"

    def set_relation(self, other: "Avatar", relation: Relation) -> None:
        """
        设置与另一个角色的关系。
        - 对称关系（如 FRIEND/ENEMY/LOVERS/SIBLING/KIN）会在对方处写入相同的关系。
        - 有向关系（如 MASTER、APPRENTICE、PARENT、CHILD）会在对方处写入对偶关系。
        """
        if other is self:
            return
        self.relations[other] = relation
        # 写入对方的对偶关系（对称关系会得到同一枚举值）
        if getattr(other, "relations", None) is not None:
            other.relations[self] = get_reciprocal(relation)

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
        仅显示4个字段：名字、境界、关系、阵营。
        """
        relation = self.get_relation(other_avatar)
        relation_str = str(relation)
        return f"{other_avatar.name}，境界：{other_avatar.cultivation_progress.get_simple_info()}，关系：{relation_str}，阵营：{other_avatar.alignment}"

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
