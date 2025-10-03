from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from enum import Enum
import random

from src.classes.root import Root, get_essence_types_for_root, extra_breakthrough_success_rate
from src.classes.region import Region, CultivateRegion, NormalRegion, CityRegion
from src.classes.alignment import Alignment
from src.classes.event import Event, NULL_EVENT
from src.classes.item import Item, items_by_name
from src.classes.prices import prices
from src.classes.hp_and_mp import HP_MAX_BY_REALM, MP_MAX_BY_REALM
from src.classes.battle import decide_battle, get_escape_success_rate
from src.utils.config import CONFIG

if TYPE_CHECKING:
    from src.classes.avatar import Avatar
    from src.classes.world import World
    from src.classes.animal import Animal
    from src.classes.plant import Plant


def long_action(step_month: int):
    """
    长态动作装饰器，用于为动作类自动添加时间管理功能
    
    Args:
        step_month: 动作需要的月份数
    """
    def decorator(cls):
        # 设置类属性，供基类使用
        cls._step_month = step_month
        
        def is_finished(self, *args, **kwargs) -> bool:
            """
            根据时间差判断动作是否完成
            接受但忽略额外的参数以保持与其他动作类型的兼容性
            """
            if self.start_monthstamp is None:
                return False
            # 修正逻辑：使用 >= step_month - 1 而不是 >= step_month
            # 这样1个月的动作在第1个月完成（时间差0 >= 0），10个月的动作在第10个月完成（时间差9 >= 9）
            # 避免了原来多执行一个月的bug
            return (self.world.month_stamp - self.start_monthstamp) >= self.step_month - 1
        
        # 只添加 is_finished 方法
        cls.is_finished = is_finished
        
        return cls
    
    return decorator

class Action(ABC):
    """
    角色可以执行的动作。
    比如，移动、攻击、采集、建造、etc。
    """
    def __init__(self, avatar: Avatar, world: World):
        """
        传一个avatar的ref
        这样子实际执行的时候，可以知道avatar的能力和状态
        可选传入world；若不传，则尝试从avatar.world获取。
        """
        self.avatar = avatar
        self.world = world

    @abstractmethod
    def execute(self) -> None:
        pass


    @property
    def name(self) -> str:
        """
        获取动作名称
        """
        return str(self.__class__.__name__)


class DefineAction(Action):
    def __init__(self, avatar: Avatar, world: World):
        """
        初始化动作，处理长态动作的属性设置
        """
        super().__init__(avatar, world)
        
        # 如果是长态动作，初始化相关属性
        if hasattr(self.__class__, '_step_month'):
            self.step_month = self.__class__._step_month
            self.start_monthstamp = None
    
    def execute(self, *args, **kwargs) -> None:
        """
        执行动作，处理时间管理逻辑，然后调用具体的_execute实现
        """
        # 如果是长态动作且第一次执行，记录开始时间
        if hasattr(self, 'step_month') and self.start_monthstamp is None:
            self.start_monthstamp = self.world.month_stamp
        
        self._execute(*args, **kwargs)
    
    @abstractmethod
    def _execute(self, *args, **kwargs) -> None:
        """
        具体的动作执行逻辑，由子类实现
        """
        pass 

class LLMAction(Action):
    """
    基于LLM的action，这种action一般是不需要实际的规则定义。
    而是一种抽象的，仅有社会层面的后果的定义。
    比如“折辱”“恶狠狠地盯着”“退婚”等
    这种action会通过LLM生成并被执行，让NPC记忆并产生后果。
    但是不需要规则侧做出反应来。
    """
    pass

class ChunkActionMixin():
    """
    动作片，可以理解成只是一种切分出来的动作。
    不能被avatar直接执行，而是成为avatar执行某个动作的步骤。
    """
    pass

class ActualActionMixin():
    """
    实际的可以被规则/LLM调用，让avatar去执行的动作。
    不一定是多个step，也有可能就一个step。

    新接口：子类必须实现 can_start/start/step/finish。
    """
    @abstractmethod
    def can_start(self, **params) -> bool:
        pass

    @abstractmethod
    def start(self, **params) -> Event | None:
        pass

    @abstractmethod
    def step(self, **params) -> tuple["StepStatus", list[Event]]:
        pass

    @abstractmethod
    def finish(self, **params) -> list[Event]:
        pass


class StepStatus(Enum):
    RUNNING = "running"
    COMPLETED = "completed"


class Move(DefineAction, ChunkActionMixin):
    """
    最基础的移动动作，在tile之间进行切换。
    """
    COMMENT = "移动到某个相对位置"
    PARAMS = {"delta_x": "int", "delta_y": "int"}
    def _execute(self, delta_x: int, delta_y: int) -> None:
        """
        移动到某个tile
        """
        world = self.world
        # 基于境界的移动步长：每轴最多移动 move_step_length 格
        step = getattr(self.avatar, "move_step_length", 1)
        clamped_dx = max(-step, min(step, delta_x))
        clamped_dy = max(-step, min(step, delta_y))

        new_x = self.avatar.pos_x + clamped_dx
        new_y = self.avatar.pos_y + clamped_dy

        # 边界检查：越界则不移动
        if world.map.is_in_bounds(new_x, new_y):
            self.avatar.pos_x = new_x
            self.avatar.pos_y = new_y
            target_tile = world.map.get_tile(new_x, new_y)
            self.avatar.tile = target_tile
        else:
            # 超出边界：不改变位置与tile
            pass

class MoveToRegion(DefineAction, ActualActionMixin):
    """
    移动到某个region
    """
    COMMENT = "移动到某个区域"
    DOABLES_REQUIREMENTS = "任何时候都可以执行"
    PARAMS = {"region": "region_name"}
    def _execute(self, region: Region|str) -> None:
        """
        移动到某个region
        """
        if isinstance(region, str):
            from src.classes.region import regions_by_name
            region = regions_by_name[region]
        cur_loc = (self.avatar.pos_x, self.avatar.pos_y)
        region_center_loc = region.center_loc
        delta_x = region_center_loc[0] - cur_loc[0]
        delta_y = region_center_loc[1] - cur_loc[1]
        # 横纵向一次最多移动 move_step_length 格（可以同时横纵移动）
        step = getattr(self.avatar, "move_step_length", 1)
        delta_x = max(-step, min(step, delta_x))
        delta_y = max(-step, min(step, delta_y))
        Move(self.avatar, self.world).execute(delta_x, delta_y)

    def can_start(self, region: Region|str|None = None) -> bool:
        return True

    def start(self, region: Region|str) -> Event:
        if isinstance(region, str):
            region_name = region
            from src.classes.region import regions_by_name
            if region in regions_by_name:
                region_name = regions_by_name[region].name
        elif hasattr(region, 'name'):
            region_name = region.name
        else:
            region_name = str(region)
        return Event(self.world.month_stamp, f"{self.avatar.name} 开始移动向 {region_name}")

    def step(self, region: Region|str) -> tuple[StepStatus, list[Event]]:
        self.execute(region=region)
        # 完成条件：到达目标区域
        if isinstance(region, str):
            from src.classes.region import regions_by_name
            region = regions_by_name[region]
        done = self.avatar.is_in_region(region)
        return (StepStatus.COMPLETED if done else StepStatus.RUNNING), []

    def finish(self, region: Region|str) -> list[Event]:
        return []


class MoveToAvatar(DefineAction, ActualActionMixin):
    """
    朝另一个角色当前位置移动。
    """
    COMMENT = "移动到某个角色所在位置"
    DOABLES_REQUIREMENTS = "任何时候都可以执行"
    PARAMS = {"avatar_name": "str"}

    def _get_target(self, avatar_name: str):
        """
        根据名字查找目标角色；找不到返回 None。
        """
        for v in self.world.avatar_manager.avatars.values():
            if v.name == avatar_name:
                return v
        return None

    def _execute(self, avatar_name: str) -> None:
        target = self._get_target(avatar_name)
        if target is None:
            return
        cur_loc = (self.avatar.pos_x, self.avatar.pos_y)
        target_loc = (target.pos_x, target.pos_y)
        delta_x = target_loc[0] - cur_loc[0]
        delta_y = target_loc[1] - cur_loc[1]
        step = getattr(self.avatar, "move_step_length", 1)
        delta_x = max(-step, min(step, delta_x))
        delta_y = max(-step, min(step, delta_y))
        Move(self.avatar, self.world).execute(delta_x, delta_y)

    def can_start(self, avatar_name: str|None = None) -> bool:
        target = self._get_target(avatar_name)
        if target is None:
            return False
        return True

    def start(self, avatar_name: str) -> Event:
        target = self._get_target(avatar_name)
        target_name = target.name if target is not None else avatar_name
        return Event(self.world.month_stamp, f"{self.avatar.name} 开始移动向 {target_name}")

    def step(self, avatar_name: str) -> tuple[StepStatus, list[Event]]:
        self.execute(avatar_name=avatar_name)
        target = None
        try:
            target = self._get_target(avatar_name)
        except Exception:
            target = None
        if target is None:
            return StepStatus.COMPLETED, []
        done = self.avatar.tile == target.tile
        return (StepStatus.COMPLETED if done else StepStatus.RUNNING), []

    def finish(self, avatar_name: str) -> list[Event]:
        return []


@long_action(step_month=6)
class MoveAwayFromAvatar(DefineAction, ActualActionMixin):
    """
    持续远离指定角色，持续6个月。
    - 规则：每月尝试使与目标的曼哈顿距离增大一步
    - 任何时候都可以启动
    """
    COMMENT = "持续远离指定角色"
    DOABLES_REQUIREMENTS = "任何时候都可以执行"
    PARAMS = {"avatar_name": "AvatarName"}

    def _find_avatar_by_name(self, name: str) -> "Avatar|None":
        for v in self.world.avatar_manager.avatars.values():
            if v.name == name:
                return v
        return None

    def _execute(self, avatar_name: str) -> None:
        target = self._find_avatar_by_name(avatar_name)
        if target is None:
            return
        # 计算远离方向：使曼哈顿距离尽量增大
        dx = 1 if self.avatar.pos_x >= target.pos_x else -1
        dy = 1 if self.avatar.pos_y >= target.pos_y else -1
        nx = self.avatar.pos_x + dx
        ny = self.avatar.pos_y + dy
        if self.world.map.is_in_bounds(nx, ny):
            self.avatar.pos_x = nx
            self.avatar.pos_y = ny
            self.avatar.tile = self.world.map.get_tile(nx, ny)

    def can_start(self, avatar_name: str | None = None) -> bool:
        return True

    def start(self, avatar_name: str) -> Event:
        target_name = avatar_name
        try:
            t = self._find_avatar_by_name(avatar_name)
            if t is not None:
                target_name = t.name
        except Exception:
            pass
        return Event(self.world.month_stamp, f"{self.avatar.name} 开始远离 {target_name}")

    def step(self, avatar_name: str) -> tuple[StepStatus, list[Event]]:
        self.execute(avatar_name=avatar_name)
        done = getattr(self, "is_finished")()
        return (StepStatus.COMPLETED if done else StepStatus.RUNNING), []

    def finish(self, avatar_name: str) -> list[Event]:
        return []


class MoveAwayFromRegion(DefineAction, ActualActionMixin):
    COMMENT = "离开指定区域"
    DOABLES_REQUIREMENTS = "任何时候都可以执行"
    PARAMS = {"region": "RegionName"}

    def _execute(self, region: str) -> None:
        # 简化：向地图边缘移动一步
        dx = 1 if self.avatar.pos_x < self.world.map.width - 1 else -1
        dy = 1 if self.avatar.pos_y < self.world.map.height - 1 else -1
        nx = max(0, min(self.world.map.width - 1, self.avatar.pos_x + dx))
        ny = max(0, min(self.world.map.height - 1, self.avatar.pos_y + dy))
        if self.world.map.is_in_bounds(nx, ny):
            self.avatar.pos_x = nx
            self.avatar.pos_y = ny
            self.avatar.tile = self.world.map.get_tile(nx, ny)

    def can_start(self, region: str | None = None) -> bool:
        return True

    def start(self, region: str) -> Event:
        return Event(self.world.month_stamp, f"{self.avatar.name} 开始离开 {region}")

    def step(self, region: str) -> tuple[StepStatus, list[Event]]:
        self.execute(region=region)
        return StepStatus.COMPLETED, []

    def finish(self, region: str) -> list[Event]:
        return []


class Escape(DefineAction, ActualActionMixin):
    """
    逃离：尝试从对方身边脱离（有成功率）。
    成功：抢占并进入 MoveAwayFromAvatar(6个月)。
    失败：抢占并进入 Battle。
    """
    COMMENT = "逃离对方（基于成功率判定）"
    DOABLES_REQUIREMENTS = "任何时候都可以执行"
    PARAMS = {"avatar_name": "AvatarName"}

    def _find_avatar_by_name(self, name: str) -> "Avatar|None":
        for v in self.world.avatar_manager.avatars.values():
            if v.name == name:
                return v
        return None

    def _preempt_avatar(self, avatar: "Avatar") -> None:
        avatar.clear_plans()
        avatar.current_action = None

    def _add_event_pair(self, event: Event, initiator: "Avatar", target: "Avatar|None") -> None:
        initiator.add_event(event)
        if target is not None:
            target.add_event(event, to_sidebar=False)

    def _execute(self, avatar_name: str) -> None:
        target = self._find_avatar_by_name(avatar_name)
        if target is None:
            return
        escape_rate = float(get_escape_success_rate(target, self.avatar))
        import random as _r
        success = _r.random() < escape_rate
        result_text = "成功" if success else "失败"
        result_event = Event(self.world.month_stamp, f"{self.avatar.name} 试图从 {target.name} 逃离：{result_text}")
        self._add_event_pair(result_event, initiator=self.avatar, target=target)
        if success:
            self._preempt_avatar(self.avatar)
            self.avatar.load_decide_result_chain([("MoveAwayFromAvatar", {"avatar_name": avatar_name})], self.avatar.thinking, "")
            start_event = self.avatar.commit_next_plan()
            if start_event is not None:
                self._add_event_pair(start_event, initiator=self.avatar, target=target)
        else:
            self._preempt_avatar(self.avatar)
            self.avatar.load_decide_result_chain([("Battle", {"avatar_name": avatar_name})], self.avatar.thinking, "")
            start_event = self.avatar.commit_next_plan()
            if start_event is not None:
                self._add_event_pair(start_event, initiator=self.avatar, target=target)

    def can_start(self, avatar_name: str | None = None) -> bool:
        return True

    def start(self, avatar_name: str) -> Event:
        target = self._find_avatar_by_name(avatar_name)
        target_name = target.name if target is not None else avatar_name
        return Event(self.world.month_stamp, f"{self.avatar.name} 尝试从 {target_name} 逃离")

    def step(self, avatar_name: str) -> tuple[StepStatus, list[Event]]:
        self.execute(avatar_name=avatar_name)
        return StepStatus.COMPLETED, []

    def finish(self, avatar_name: str) -> list[Event]:
        return []

@long_action(step_month=10)
class Cultivate(DefineAction, ActualActionMixin):
    """
    修炼动作，可以增加修仙进度。
    """
    COMMENT = "修炼，增进修为"
    DOABLES_REQUIREMENTS = "在修炼区域中，修炼区域的灵气为角色的灵根之一，且角色未到瓶颈。"
    PARAMS = {}
    def _execute(self) -> None:
        """
        修炼
        获得的exp增加取决于essence的对应灵根的大小。
        """
        root = self.avatar.root
        essence = self.avatar.tile.region.essence
        # 多元素：取与角色灵根任一匹配元素的最大密度
        essence_types = get_essence_types_for_root(root)
        essence_density = max((essence.get_density(et) for et in essence_types), default=0)
        exp = self.get_exp(essence_density)
        self.avatar.cultivation_progress.add_exp(exp)

    def get_exp(self, essence_density: int) -> int:
        """
        根据essence的密度，计算获得的exp。
        公式为：base * essence_density
        """
        if self.avatar.cultivation_progress.is_in_bottleneck():
            return 0
        base = 100
        return base * essence_density
    
    def can_start(self) -> bool:
        root = self.avatar.root
        region = self.avatar.tile.region
        essence_types = get_essence_types_for_root(root)
        if not self.avatar.cultivation_progress.can_cultivate():
            return False
        if not isinstance(region, CultivateRegion):
            return False
        if all(region.essence.get_density(et) == 0 for et in essence_types):
            return False
        return True

    def start(self) -> Event:
        return Event(self.world.month_stamp, f"{self.avatar.name} 在 {self.avatar.tile.region.name} 开始修炼")

    def step(self) -> tuple[StepStatus, list[Event]]:
        self.execute()
        # 使用 long_action 注入的 is_finished
        done = getattr(self, "is_finished")()
        return (StepStatus.COMPLETED if done else StepStatus.RUNNING), []

    def finish(self) -> list[Event]:
        return []

# 突破境界class
@long_action(step_month=1)
class Breakthrough(DefineAction, ActualActionMixin):
    """
    突破境界。
    成功率由 `CultivationProgress.get_breakthrough_success_rate()` 决定；
    失败时按 `CultivationProgress.get_breakthrough_fail_reduce_lifespan()` 减少寿元（年）。
    """
    COMMENT = "尝试突破境界（成功增加寿元上限，失败折损寿元上限；境界越高，成功率越低。）"
    DOABLES_REQUIREMENTS = "角色处于瓶颈时"
    PARAMS = {}
    def calc_success_rate(self) -> float:
        """
        计算突破境界的成功率（由修为进度给出）
        """
        base = self.avatar.cultivation_progress.get_breakthrough_success_rate()
        bonus = extra_breakthrough_success_rate[self.avatar.root]
        # 夹紧到 [0, 1]
        return max(0.0, min(1.0, base + bonus))

    def _execute(self) -> None:
        """
        突破境界
        """
        assert self.avatar.cultivation_progress.can_break_through()   
        success_rate = self.calc_success_rate()
        # 记录本次尝试的基础信息
        self._success_rate_cached = success_rate
        if random.random() < success_rate:
            old_realm = self.avatar.cultivation_progress.realm
            self.avatar.cultivation_progress.break_through()
            new_realm = self.avatar.cultivation_progress.realm
            
            # 突破成功时更新HP和MP的最大值
            if new_realm != old_realm:
                self._update_hp_mp_on_breakthrough(new_realm)
                # 成功：确保最大寿元至少达到新境界的基线
                self.avatar.age.ensure_max_lifespan_at_least_realm_base(new_realm)
            # 记录结果用于 finish 事件
            self._last_result = ("success", getattr(old_realm, "value", str(old_realm)), getattr(new_realm, "value", str(new_realm)))
        else:
            # 突破失败：减少最大寿元上限
            reduce_years = self.avatar.cultivation_progress.get_breakthrough_fail_reduce_lifespan()
            self.avatar.age.decrease_max_lifespan(reduce_years)
            # 记录结果用于 finish 事件
            self._last_result = ("fail", int(reduce_years))
    
    def _update_hp_mp_on_breakthrough(self, new_realm):
        """
        突破境界时更新HP和MP的最大值并完全恢复
        
        Args:
            new_realm: 新的境界
        """
        new_max_hp = HP_MAX_BY_REALM.get(new_realm, 100)
        new_max_mp = MP_MAX_BY_REALM.get(new_realm, 100)
        
        # 计算增加的最大值
        hp_increase = new_max_hp - self.avatar.hp.max
        mp_increase = new_max_mp - self.avatar.mp.max
        
        # 更新最大值并恢复相应的当前值
        self.avatar.hp.add_max(hp_increase)
        self.avatar.hp.recover(hp_increase)  # 突破时完全恢复HP
        self.avatar.mp.add_max(mp_increase)
        self.avatar.mp.recover(mp_increase)  # 突破时完全恢复MP
    
    def can_start(self) -> bool:
        return self.avatar.cultivation_progress.can_break_through()

    def start(self) -> Event:
        # 清理上次残留的结果状态（防御性）
        self._last_result = None
        self._success_rate_cached = None
        return Event(self.world.month_stamp, f"{self.avatar.name} 开始尝试突破境界")

    def step(self) -> tuple[StepStatus, list[Event]]:
        self.execute()
        done = getattr(self, "is_finished")()
        return (StepStatus.COMPLETED if done else StepStatus.RUNNING), []

    def finish(self) -> list[Event]:
        # 根据执行阶段记录的 _last_result 生成简洁完成事件
        res = getattr(self, "_last_result", None)
        if isinstance(res, tuple) and res:
            if res[0] == "success":
                return [Event(self.world.month_stamp, f"{self.avatar.name} 突破成功")]
            elif res[0] == "fail":
                return [Event(self.world.month_stamp, f"{self.avatar.name} 突破失败")]
            else:
                raise ValueError(f"Unknown result: {res}")

@long_action(step_month=6)
class Play(DefineAction, ActualActionMixin):
    """
    游戏娱乐动作，持续半年时间
    """
    COMMENT = "游戏娱乐，放松身心"
    DOABLES_REQUIREMENTS = "任何时候都可以执行"
    PARAMS = {}
    
    def _execute(self) -> None:
        """
        进行游戏娱乐活动
        """
        # 游戏娱乐的具体逻辑可以在这里实现
        # 比如增加心情值、减少压力等
        pass
    
    def can_start(self) -> bool:
        return True

    def start(self) -> Event:
        return Event(self.world.month_stamp, f"{self.avatar.name} 开始玩耍")

    def step(self) -> tuple[StepStatus, list[Event]]:
        self.execute()
        done = getattr(self, "is_finished")()
        return (StepStatus.COMPLETED if done else StepStatus.RUNNING), []

    def finish(self) -> list[Event]:
        return []


@long_action(step_month=6)
class Hunt(DefineAction, ActualActionMixin):
    """
    狩猎动作，在有动物的区域进行狩猎，持续6个月
    可以获得动物对应的物品
    """
    COMMENT = "在当前区域狩猎动物，获取动物材料"
    DOABLES_REQUIREMENTS = "在有动物的普通区域，且avatar的境界必须大于等于动物的境界"
    PARAMS = {}

    def get_available_animals(self) -> list[Animal]:
        """
        获取avatar境界足够的动物
        """
        region = self.avatar.tile.region
        avatar_realm = self.avatar.cultivation_progress.realm
        return [animal for animal in region.animals if avatar_realm >= animal.realm]
    
    def _execute(self) -> None:
        """
        执行狩猎动作
        """
        success_rate = self.get_success_rate()
        available_animals = self.get_available_animals()
        if len(available_animals) == 0:
            # TODO: 我的doable检查有问题，之后看看问题在哪里
            return
        
        if random.random() < success_rate:
            # 成功狩猎，从avatar境界足够的动物中随机选择一种
            target_animal = random.choice(available_animals)
            # 随机选择该动物的一种物品
            item = random.choice(target_animal.items)
            self.avatar.add_item(item, 1)
    
    def get_success_rate(self) -> float:
        """
        获取狩猎成功率，预留接口，目前固定为100%
        """
        return 1.0  # 100%成功率
    
    def can_start(self) -> bool:
        region = self.avatar.tile.region
        if not isinstance(region, NormalRegion):
            return False
        available_animals = self.get_available_animals()
        if len(available_animals) == 0:
            return False
        return True

    def start(self) -> Event:
        region = self.avatar.tile.region
        return Event(self.world.month_stamp, f"{self.avatar.name} 在 {region.name} 开始狩猎")

    def step(self) -> tuple[StepStatus, list[Event]]:
        self.execute()
        done = getattr(self, "is_finished")()
        return (StepStatus.COMPLETED if done else StepStatus.RUNNING), []

    def finish(self) -> list[Event]:
        return []


@long_action(step_month=6)
class Harvest(DefineAction, ActualActionMixin):
    """
    采集动作，在有植物的区域进行采集，持续6个月
    可以获得植物对应的物品
    """
    COMMENT = "在当前区域采集植物，获取植物材料"
    DOABLES_REQUIREMENTS = "在有植物的普通区域，且avatar的境界必须大于等于植物的境界"
    PARAMS = {}

    def get_available_plants(self) -> list[Plant]:
        """
        获取avatar境界足够的植物
        """
        region = self.avatar.tile.region
        avatar_realm = self.avatar.cultivation_progress.realm
        return [plant for plant in region.plants if avatar_realm >= plant.realm]
    
    def _execute(self) -> None:
        """
        执行采集动作
        """
        success_rate = self.get_success_rate()
        available_plants = self.get_available_plants()
        if len(available_plants) == 0:
            # TODO: 我的doable检查有问题，之后看看问题在哪里
            return

        if random.random() < success_rate:
            # 成功采集，从avatar境界足够的植物中随机选择一种
            target_plant = random.choice(available_plants)
            # 随机选择该植物的一种物品
            item = random.choice(target_plant.items)
            self.avatar.add_item(item, 1)
    
    def get_success_rate(self) -> float:
        """
        获取采集成功率，预留接口，目前固定为100%
        """
        return 1.0  # 100%成功率
    
    def can_start(self) -> bool:
        region = self.avatar.tile.region
        if not isinstance(region, NormalRegion):
            return False
        avaliable_plants = self.get_available_plants()
        if len(avaliable_plants) == 0:
            return False
        return True

    def start(self) -> Event:
        region = self.avatar.tile.region
        return Event(self.world.month_stamp, f"{self.avatar.name} 在 {region.name} 开始采集")

    def step(self) -> tuple[StepStatus, list[Event]]:
        self.execute()
        done = getattr(self, "is_finished")()
        return (StepStatus.COMPLETED if done else StepStatus.RUNNING), []

    def finish(self) -> list[Event]:
        return []


@long_action(step_month=1)
class Sold(DefineAction, ActualActionMixin):
    """
    在城镇出售指定名称的物品，一次性卖出持有的全部数量。
    收益为 item_price * item_num，动作耗时1个月。
    """
    COMMENT = "在城镇出售持有的某类物品的全部"
    DOABLES_REQUIREMENTS = "在城镇且背包非空"
    PARAMS = {"item_name": "str"}

    def _execute(self, item_name: str) -> None:
        region = self.avatar.tile.region
        if not isinstance(region, CityRegion):
            return

        # 找到物品
        item = items_by_name.get(item_name)
        if item is None:
            return

        # 检查持有数量
        quantity = self.avatar.get_item_quantity(item)
        if quantity <= 0:
            return

        # 计算价格并结算
        price_per = prices.get_price(item)
        total_gain = price_per * quantity

        # 扣除物品并增加灵石
        removed = self.avatar.remove_item(item, quantity)
        if not removed:
            return

        self.avatar.magic_stone = self.avatar.magic_stone + total_gain

    def can_start(self, item_name: str|None = None) -> bool:
        region = self.avatar.tile.region
        if not isinstance(region, CityRegion):
            return False
        if item_name is None:
            # 用于动作空间：只要背包非空即可
            return bool(self.avatar.items)
        item = items_by_name.get(item_name)
        if item is None:
            return False
        return self.avatar.get_item_quantity(item) > 0

    def start(self, item_name: str) -> Event:
        return Event(self.world.month_stamp, f"{self.avatar.name} 在城镇出售 {item_name}")

    def step(self, item_name: str) -> tuple[StepStatus, list[Event]]:
        self.execute(item_name=item_name)
        # 一次性动作
        return StepStatus.COMPLETED, []

    def finish(self, item_name: str) -> list[Event]:
        return []


class Battle(DefineAction, ActualActionMixin):
    COMMENT = "与目标进行对战，判定胜负"
    DOABLES_REQUIREMENTS = "任何时候都可以执行"
    PARAMS = {"avatar_name": "AvatarName"}

    def _get_target(self, avatar_name: str):
        for v in self.world.avatar_manager.avatars.values():
            if v.name == avatar_name:
                return v
        return None

    def _execute(self, avatar_name: str) -> None:
        target = self._get_target(avatar_name)
        if target is None:
            return
        winner, loser, damage = decide_battle(self.avatar, target)
        loser.hp.reduce(damage)
        self._last_result = (winner.name, loser.name)

    def can_start(self, avatar_name: str | None = None) -> bool:
        if avatar_name is None:
            return False
        return self._get_target(avatar_name) is not None

    def start(self, avatar_name: str) -> Event:
        target = self._get_target(avatar_name)
        target_name = target.name if target is not None else avatar_name
        return Event(self.world.month_stamp, f"{self.avatar.name} 对 {target_name} 发起战斗")

    def step(self, avatar_name: str) -> tuple[StepStatus, list[Event]]:
        self.execute(avatar_name=avatar_name)
        return StepStatus.COMPLETED, []

    def finish(self, avatar_name: str) -> list[Event]:
        res = self._last_result
        if isinstance(res, tuple) and len(res) == 2:
            winner, loser = res
            return [Event(self.world.month_stamp, f"{winner} 战胜了 {loser}")]
        return []


@long_action(step_month=3)
class PlunderMortals(DefineAction, ActualActionMixin):
    """
    在城镇对凡人进行搜刮，获取少量灵石。
    仅邪阵营可执行。
    """
    COMMENT = "在城镇搜刮凡人，获取少量灵石"
    DOABLES_REQUIREMENTS = "仅限城市区域，且角色阵营为‘邪’"
    PARAMS = {}
    GAIN = 20

    def _execute(self) -> None:
        region = self.avatar.tile.region
        if not isinstance(region, CityRegion):
            return
        gain = self.GAIN
        self.avatar.magic_stone = self.avatar.magic_stone + gain

    def can_start(self) -> bool:
        region = self.avatar.tile.region
        if not isinstance(region, CityRegion):
            return False
        return self.avatar.alignment == Alignment.EVIL

    def start(self) -> Event:
        return Event(self.world.month_stamp, f"{self.avatar.name} 在城镇开始搜刮凡人")

    def step(self) -> tuple[StepStatus, list[Event]]:
        self.execute()
        return (StepStatus.COMPLETED if getattr(self, "is_finished")() else StepStatus.RUNNING), []

    def finish(self) -> list[Event]:
        return []


@long_action(step_month=3)
class HelpMortals(DefineAction, ActualActionMixin):
    """
    在城镇帮助凡人，消耗少量灵石。
    仅正阵营可执行。
    """
    COMMENT = "在城镇帮助凡人，消耗少量灵石"
    DOABLES_REQUIREMENTS = "仅限城市区域，且角色阵营为‘正’，并且灵石足够"
    PARAMS = {}
    COST = 10

    def _execute(self) -> None:
        region = self.avatar.tile.region
        if not isinstance(region, CityRegion):
            return
        cost = self.COST
        if getattr(self.avatar.magic_stone, "value", 0) >= cost:
            self.avatar.magic_stone = self.avatar.magic_stone - cost

    def can_start(self) -> bool:
        region = self.avatar.tile.region
        if not isinstance(region, CityRegion):
            return False
        if self.avatar.alignment != Alignment.RIGHTEOUS:
            return False
        cost = self.COST
        return self.avatar.magic_stone >= cost

    def start(self) -> Event:
        return Event(self.world.month_stamp, f"{self.avatar.name} 在城镇开始帮助凡人")

    def step(self) -> tuple[StepStatus, list[Event]]:
        self.execute()
        return (StepStatus.COMPLETED if getattr(self, "is_finished")() else StepStatus.RUNNING), []

    def finish(self) -> list[Event]:
        return []


class Talk(DefineAction, ActualActionMixin):
    """
    攀谈：尝试与同区域内的某个NPC进行交谈。
    - can_start：同区域内存在其他NPC
    - 发起后：随机寻找“同一tile”的NPC，若不存在则本次无法攀谈
    - 若找到，则进入 MutualAction: Conversation（允许建立关系）
    """

    COMMENT = "与同区域内的NPC发起攀谈，若同一tile有人则进入交谈"
    DOABLES_REQUIREMENTS = "同区域内存在其他NPC"
    PARAMS = {}

    def _get_same_region_others(self) -> list["Avatar"]:
        return self.world.avatar_manager.get_avatars_in_same_region(self.avatar)

    def _get_same_tile_others(self) -> list["Avatar"]:
        same_tile: list["Avatar"] = []
        my_tile = self.avatar.tile
        if my_tile is None:
            return []
        for v in self.world.avatar_manager.avatars.values():
            if v is self.avatar or v.tile is None:
                continue
            if v.tile == my_tile:
                same_tile.append(v)
        return same_tile

    def _execute(self) -> None:
        # Talk 本身不做长期效果，主要在 step 中驱动 Conversation
        return

    def can_start(self) -> bool:
        # 是否同区域存在其他NPC（用于展示在动作空间）
        return len(self._get_same_region_others()) > 0

    def start(self) -> Event:
        # 记录开始事件
        return Event(self.world.month_stamp, f"{self.avatar.name} 尝试与同区域的他人攀谈")

    def step(self) -> tuple[StepStatus, list[Event]]:
        same_region_others = self._get_same_region_others()

        import random
        target = random.choice(same_region_others)

        # 进入交谈：由概率决定本次是否允许建立关系
        from src.classes.mutual_action import Conversation
        # 由配置决定本次是否有“有机会进入关系”标记
        prob = float(getattr(CONFIG.social, "talk_into_relation_probability", 0.0))
        can_into_relation = (random.random() < prob)

        conv = Conversation(self.avatar, self.world)
        # 启动事件写入历史，不入侧边栏
        conv.start(target_avatar=target)
        conv.step(target_avatar=target, can_into_relation=can_into_relation)
        return StepStatus.COMPLETED, []

    def finish(self) -> list[Event]:
        return []
