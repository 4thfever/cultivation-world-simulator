from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from src.classes.essence import Essence, EssenceType
from src.classes.root import Root, corres_essence_type

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
    def execute(self):
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
    def execute(self, delta_x: int, delta_y: int):
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

class Cultivate(DefineAction):
    """
    修炼动作，可以增加修仙进度。
    """
    def execute(self, root: Root, essence: Essence):
        """
        修炼
        获得的exp增加取决于essence的对应灵根的大小。
        """
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