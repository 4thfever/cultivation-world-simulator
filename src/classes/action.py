from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
import random
import json
import inspect

from src.classes.essence import Essence, EssenceType
from src.classes.root import Root, corres_essence_type
from src.classes.tile import Region
from src.classes.event import Event, NULL_EVENT

if TYPE_CHECKING:
    from src.classes.avatar import Avatar
    from src.classes.world import World


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
    不一定是多个step，也有可能就一个step
    """
    @abstractmethod
    def is_finished(self) -> bool:
        """
        判断动作是否完成
        """
        pass
    
    @abstractmethod
    def get_event(self, *args, **kwargs) -> Event:
        """
        获取动作开始时的事件
        """
        pass


class Move(DefineAction, ChunkActionMixin):
    """
    最基础的移动动作，在tile之间进行切换。
    """
    COMMENT = "移动到某个相对位置"
    def _execute(self, delta_x: int, delta_y: int) -> None:
        """
        移动到某个tile
        """
        world = self.world
        new_x = self.avatar.pos_x + delta_x
        new_y = self.avatar.pos_y + delta_y

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
    def _execute(self, region: Region|str) -> None:
        """
        移动到某个region
        """
        if isinstance(region, str):
            region = self.world.map.region_names[region]
        cur_loc = (self.avatar.pos_x, self.avatar.pos_y)
        region_center_loc = region.center_loc
        delta_x = region_center_loc[0] - cur_loc[0]
        delta_y = region_center_loc[1] - cur_loc[1]
        # 横纵向一次最多移动一格（可以同时横纵移动）
        delta_x = max(-1, min(1, delta_x))
        delta_y = max(-1, min(1, delta_y))
        Move(self.avatar, self.world).execute(delta_x, delta_y)

    def is_finished(self, region: Region|str) -> bool:
        """
        判断动作是否完成
        """
        if isinstance(region, str):
            region = self.world.map.region_names[region]
        return self.avatar.is_in_region(region)
    
    def get_event(self, region: Region|str) -> Event:
        """
        获取移动动作开始时的事件
        """
        if isinstance(region, str):
            region_name = region
            if region in self.world.map.region_names:
                region_name = self.world.map.region_names[region].name
        elif hasattr(region, 'name'):
            region_name = region.name
        else:
            region_name = str(region)
        return Event(self.world.month_stamp, f"{self.avatar.name} 开始移动向 {region_name}")

@long_action(step_month=10)
class Cultivate(DefineAction, ActualActionMixin):
    """
    修炼动作，可以增加修仙进度。
    """
    COMMENT = "修炼，增进修为"
    def _execute(self) -> None:
        """
        修炼
        获得的exp增加取决于essence的对应灵根的大小。
        """
        root = self.avatar.root
        essence = self.avatar.tile.region.essence
        essence_type = corres_essence_type[root]
        essence_density = essence.get_density(essence_type)
        exp = self.get_exp(essence_density)
        self.avatar.cultivation_progress.add_exp(exp)

    def get_exp(self, essence_density: int) -> int:
        """
        根据essence的密度，计算获得的exp。
        公式为：base * essence_density
        """
        base = 100
        return base * essence_density
    
    def get_event(self) -> Event:
        """
        获取修炼动作开始时的事件
        """
        return Event(self.world.month_stamp, f"{self.avatar.name} 在 {self.avatar.tile.region.name} 开始修炼")


# 突破境界class
@long_action(step_month=1)
class Breakthrough(DefineAction, ActualActionMixin):
    """
    突破境界
    """
    COMMENT = "尝试突破境界"
    def calc_success_rate(self) -> float:
        """
        计算突破境界的成功率
        """
        return 0.5

    def _execute(self) -> None:
        """
        突破境界
        """
        assert self.avatar.cultivation_progress.can_break_through()   
        success_rate = self.calc_success_rate()
        if random.random() < success_rate:
            self.avatar.cultivation_progress.break_through()
    
    def get_event(self) -> Event:
        """
        获取突破动作开始时的事件
        """
        return Event(self.world.month_stamp, f"{self.avatar.name} 开始尝试突破境界")


ALL_ACTION_CLASSES = [Move, Cultivate, Breakthrough, MoveToRegion]
# 不包括Move
ACTION_SPACE = [
    # {"action": "Move", "params": {"delta_x": int, "delta_y": int}, "comment": Move.COMMENT},
    {"action": "Cultivate", "params": {}, "comment": Cultivate.COMMENT},
    {"action": "Breakthrough", "params": {}, "comment": Breakthrough.COMMENT},
    {"action": "MoveToRegion", "params": {"region": "region_name"}, "comment": MoveToRegion.COMMENT},
]
ACTION_SPACE_STR = json.dumps(ACTION_SPACE, ensure_ascii=False) 