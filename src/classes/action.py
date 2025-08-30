from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
import random
import json

from src.classes.essence import Essence, EssenceType
from src.classes.root import Root, corres_essence_type
from src.classes.tile import Region
from src.classes.event import Event, NullEvent

if TYPE_CHECKING:
    from src.classes.avatar import Avatar
    from src.classes.world import World

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
    def execute(self) -> Event|NullEvent:
        pass

class DefineAction(Action):
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


class Move(DefineAction):
    """
    最基础的移动动作，在tile之间进行切换。
    """
    COMMENT = "移动到某个相对位置"
    def execute(self, delta_x: int, delta_y: int) -> Event|NullEvent:
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
        return NullEvent()

class MoveToRegion(DefineAction):
    """
    移动到某个region
    """
    COMMENT = "移动到某个区域"
    def execute(self, region: Region|str) -> Event|NullEvent:
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
        return Event(self.world.year, self.world.month, f"{self.avatar.name} 移动向 {region.name}")

class Cultivate(DefineAction):
    """
    修炼动作，可以增加修仙进度。
    """
    COMMENT = "修炼，增进修为"
    def execute(self) -> Event|NullEvent:
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
        return Event(self.world.year, self.world.month, f"{self.avatar.name} 在 {self.avatar.tile.region.name} 修炼")

    def get_exp(self, essence_density: int) -> int:
        """
        根据essence的密度，计算获得的exp。
        公式为：base * essence_density
        """
        base = 100
        return base * essence_density


# 突破境界class
class Breakthrough(DefineAction):
    """
    突破境界
    """
    COMMENT = "尝试突破境界"
    def calc_success_rate(self) -> float:
        """
        计算突破境界的成功率
        """
        return 0.5

    def execute(self) -> Event|NullEvent:
        """
        突破境界
        """
        assert self.avatar.cultivation_progress.can_break_through()   
        success_rate = self.calc_success_rate()
        if random.random() < success_rate:
            self.avatar.cultivation_progress.break_through()
            is_success = True
        else:
            is_success = False
        res = "成功" if is_success else "失败"
        return Event(self.world.year, self.world.month, f"{self.avatar.name} 突破境界{res}")


ALL_ACTION_CLASSES = [Move, Cultivate, Breakthrough, MoveToRegion]
# 不包括Move
ACTION_SPACE = [
    # {"action": "Move", "params": {"delta_x": int, "delta_y": int}, "comment": Move.COMMENT},
    {"action": "Cultivate", "params": {}, "comment": Cultivate.COMMENT},
    {"action": "Breakthrough", "params": {}, "comment": Breakthrough.COMMENT},
    {"action": "MoveToRegion", "params": {"region": "region_name"}, "comment": MoveToRegion.COMMENT},
]
ACTION_SPACE_STR = json.dumps(ACTION_SPACE, ensure_ascii=False) 