import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List
from collections import defaultdict
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
from src.classes.effect import _merge_effects
from src.classes.alignment import Alignment
from src.classes.persona import Persona, personas_by_id, get_random_compatible_personas
from src.classes.item import Item
from src.classes.treasure import Treasure
from src.classes.magic_stone import MagicStone
from src.classes.hp_and_mp import HP, MP, HP_MAX_BY_REALM, MP_MAX_BY_REALM
from src.utils.id_generator import get_avatar_id
from src.utils.config import CONFIG
from src.classes.relation import Relation, get_reciprocal
from src.run.log import get_logger
from src.classes.alignment import Alignment
from src.utils.params import filter_kwargs_for_callable
from src.classes.sect import Sect
from src.classes.appearance import Appearance, get_random_appearance
from src.classes.battle import get_base_strength

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
    # 外貌（1~10级），创建时随机生成
    appearance: Appearance = field(default_factory=get_random_appearance)
    # 装备的法宝（仅一个）
    treasure: Optional[Treasure] = None
    # 当月/当步新设动作标记：在 commit_next_plan 设为 True，首次 tick_action 后清为 False
    _new_action_set_this_step: bool = False
    # 不缓存 effects；实时从宗门与功法合并

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

        # effects 改为实时属性，不在此初始化

    @property
    def effects(self) -> dict[str, object]:
        merged: dict[str, object] = defaultdict(str)
        # 来自宗门
        if self.sect is not None:
            merged = _merge_effects(merged, self.sect.effects)
        # 来自功法
        merged = _merge_effects(merged, self.technique.effects)
        # 来自灵根
        merged = _merge_effects(merged, self.root.effects)
        # 来自法宝
        if self.treasure is not None:
            merged = _merge_effects(merged, self.treasure.effects)
        # 评估动态效果表达式：值以 "eval(...)" 形式给出
        evaluated: dict[str, object] = {}
        for k, v in merged.items():
            if isinstance(v, str):
                s = v.strip()
                if s.startswith("eval(") and s.endswith(")"):
                    expr = s[5:-1]
                    evaluated[k] = eval(expr, {"__builtins__": {}}, {"avatar": self})
                    continue
            evaluated[k] = v
        return evaluated


    def __hash__(self) -> int:
        return hash(self.id)

    def get_info(self, detailed: bool = False) -> dict:
        """
        获取 avatar 的信息，返回 dict；根据 detailed 控制信息粒度。
        """
        region = self.tile.region if self.tile is not None else None
        relations_info = self._get_relations_summary_str()
        magic_stone_info = str(self.magic_stone)

        if detailed:
            treasure_info = self.treasure.get_detailed_info() if self.treasure is not None else "无"
            sect_info = self.sect.get_detailed_info() if self.sect is not None else "散修"
            alignment_info = self.alignment.get_detailed_info() if self.alignment is not None else "未知"
            region_info = region.get_detailed_info() if region is not None else "无"
            root_info = self.root.get_detailed_info()
            technique_info = self.technique.get_detailed_info() if self.technique is not None else "无"
            cultivation_info = self.cultivation_progress.get_detailed_info()
            personas_info = ", ".join([p.get_detailed_info() for p in self.personas]) if self.personas else "无"
            items_info = "，".join([f"{item.get_detailed_info()}x{quantity}" for item, quantity in self.items.items()]) if self.items else "无"
            appearance_info = self.appearance.get_detailed_info(self.gender)
        else:
            treasure_info = self.treasure.get_info() if self.treasure is not None else "无"
            # personas和sect一致返回detailed，因为这俩太重要了
            sect_info = self.sect.get_detailed_info() if self.sect is not None else "散修"
            region_info = region.get_info() if region is not None else "无"
            alignment_info = self.alignment.get_info() if self.alignment is not None else "未知"
            root_info = self.root.get_info()
            technique_info = self.technique.get_info() if self.technique is not None else "无"
            cultivation_info = self.cultivation_progress.get_info()
            personas_info = ", ".join([p.get_detailed_info() for p in self.personas]) if self.personas else "无"
            items_info = "，".join([f"{item.get_info()}x{quantity}" for item, quantity in self.items.items()]) if self.items else "无"
            appearance_info = self.appearance.get_info()

        return {
            "id": self.id,
            "名字": self.name,
            "性别": str(self.gender),
            "年龄": str(self.age),
            "hp": str(self.hp),
            "mp": str(self.mp),
            "灵石": magic_stone_info,
            "关系": relations_info,
            "宗门": sect_info,
            "阵营": alignment_info,
            "地区": region_info,
            "灵根": root_info,
            "功法": technique_info,
            "境界": cultivation_info,
            "个性": personas_info,
            "物品": items_info,
            "外貌": appearance_info,
            "法宝": treasure_info,
        }

    def __str__(self) -> str:
        return str(self.get_info(detailed=False))

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

    def get_prompt_info(self, co_region_avatars: Optional[List["Avatar"]] = None) -> dict:
        """
        获取角色提示词信息，返回 dict。
        """
        info = self.get_info(detailed=False)

        observed: list[str] = []
        if co_region_avatars:
            for other in co_region_avatars[:8]:
                observed.append(f"{other.name}(境界：{other.cultivation_progress.get_info()})")

        if self.history_events:
            history_list = [str(e) for e in self.history_events[-8:]]
        else:
            history_list = []

        action_space = self.get_action_space()

        info["动作空间"] = action_space
        info["观察到的角色"] = observed
        info["历史事件"] = history_list
        return info

    def get_hover_info(self) -> list[str]:
        """
        返回用于前端悬浮提示的多行信息。
        """
        def add_kv(lines: list[str], key: str, value: object) -> None:
            lines.append(f"{key}: {value}")

        def add_section(lines: list[str], title: str, body: list[str]) -> None:
            lines.append("")
            lines.append(f"{title}:")
            lines.extend(body)

        lines: list[str] = []
        # 基础信息
        lines.append(f"{self.name}")
        add_kv(lines, "性别", self.gender)
        add_kv(lines, "年龄", self.age)
        add_kv(lines, "外貌", self.appearance.get_info())
        add_kv(lines, "阵营", self.alignment)
        add_kv(lines, "境界", str(self.cultivation_progress))
        add_kv(lines, "HP", self.hp)
        add_kv(lines, "MP", self.mp)
        add_kv(lines, "战斗力", int(get_base_strength(self)))
        add_kv(lines, "宗门", self.get_sect_str())

        from src.classes.root import format_root_cn
        add_kv(lines, "灵根", format_root_cn(self.root))

        if self.technique is not None:
            tech_str = f"{self.technique.name}（{self.technique.attribute}·{self.technique.grade.value}）"
        else:
            tech_str = "无"
        add_kv(lines, "功法", tech_str)

        if self.personas:
            add_kv(lines, "个性", ", ".join([p.name for p in self.personas]))

        add_kv(lines, "位置", f"({self.pos_x}, {self.pos_y})")
        add_kv(lines, "灵石", str(self.magic_stone))

        # 物品
        if self.items:
            items_lines = [f"  {item.name} x{quantity}" for item, quantity in self.items.items()]
            add_section(lines, "物品", items_lines)
        else:
            add_kv(lines, "物品", "无")

        # 思考与目标
        if self.thinking:
            from src.utils.text_wrap import wrap_text
            add_section(lines, "思考", wrap_text(self.thinking, 28))
        if getattr(self, "objective", None):
            from src.utils.text_wrap import wrap_text
            add_section(lines, "目标", wrap_text(self.objective, 28))

        # 法宝（仅名字）
        if self.treasure is not None:
            add_section(lines, "法宝", [self.treasure.get_info()])
        else:
            add_kv(lines, "法宝", "无")

        # 关系
        relations_list = [f"{other.name}({str(relation)})" for other, relation in getattr(self, "relations", {}).items()]
        if relations_list:
            add_section(lines, "关系", [f"  {s}" for s in relations_list[:6]])
        else:
            add_kv(lines, "关系", "无")

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
        仅显示几个字段：名字、境界、关系、宗门、阵营、外貌。
        """
        relation = self.get_relation(other_avatar)
        relation_str = str(relation)
        sect_str = other_avatar.sect.name if other_avatar.sect is not None else "散修"
        tr_str = other_avatar.treasure.get_info() if other_avatar.treasure is not None else "无"
        return f"{other_avatar.name}，境界：{other_avatar.cultivation_progress.get_info()}，关系：{relation_str}，阵营：{other_avatar.alignment}，宗门：{sect_str}，法宝：{tr_str}，外貌：{other_avatar.appearance.get_info()}"

    def update_time_effect(self) -> None:
        """
        随时间更新的被动效果。
        当前实现：当 HP 未满时，回复最大生命值的 1%。
        """
        if self.hp.cur < self.hp.max:
            recover_amount = int(self.hp.max * 0.01)
            self.hp.recover(recover_amount)

    @property
    def move_step_length(self) -> int:
        """
        获取角色的移动步长
        """
        return self.cultivation_progress.get_move_step()

    
