"""
NPC AI的类。
这里指的不是LLM或者Machine Learning，而是NPC的决策机制
分为两类：规则AI和LLM AI
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
import random

from src.classes.world import World
from src.classes.tile import Region
from src.classes.root import corres_essence_type
from src.classes.action import ACTION_SPACE_STR
from src.classes.event import Event, NULL_EVENT
from src.utils.llm import get_ai_prompt_and_call_llm
from src.classes.typings import ACTION_NAME, ACTION_PARAMS, ACTION_PAIR

if TYPE_CHECKING:
    from src.classes.avatar import Avatar

class AI(ABC):
    """
    AI的基类
    """
    def __init__(self, avatar: Avatar):
        self.avatar = avatar

    def decide(self, world: World) -> tuple[ACTION_NAME, ACTION_PARAMS, Event]:
        """
        决定做什么，同时生成对应的事件
        """
        # 先决定动作和参数
        action_name, action_params = self._decide(world)
        
        # 获取动作对象并生成事件
        action = self.avatar.create_action(action_name)
        event = action.get_event(**action_params)
        
        return action_name, action_params, event

    @abstractmethod
    def _decide(self, world: World) -> ACTION_PAIR:
        """
        决策逻辑：决定执行什么动作和参数
        由子类实现具体的决策逻辑
        """
        pass

class RuleAI(AI):
    """
    规则AI
    """
    def _decide(self, world: World) -> ACTION_PAIR:
        """
        决策逻辑：决定执行什么动作和参数
        先做一个简单的：
        1. 找到自己灵根对应的最好的区域
        2. 检测自己是否在最好的区域
        3. 如果不在，则移动到最好的区域
        4. 如果已经到达最好的区域，则进行修炼
        5. 如果需要突破境界了，则突破境界
        """
        if random.random() < 0.1:
            return "Play", {}
        best_region = self.get_best_region(list(world.map.regions.values()))
        if self.avatar.is_in_region(best_region):
            if self.avatar.cultivation_progress.can_break_through():
                return "Breakthrough", {}
            else:
                return "Cultivate", {}
        else:
            return "MoveToRegion", {"region": best_region}
    
    def get_best_region(self, regions: list[Region]) -> Region:
        """
        根据avatar的灵根找到最适合的区域
        """
        root = self.avatar.root
        essence_type = corres_essence_type[root]
        region_with_best_essence = max(regions, key=lambda region: region.essence.get_density(essence_type))
        return region_with_best_essence
        
class LLMAI(AI):
    """
    LLM AI
    """
    # TODO：动作链
    """
    AI动作应该分两类：
        1. 动作链，一定时间内的长期规划，动作按照这个动作链来执行（以及何时终止并执行下一个动作）
        2. 突发情况，比如突然有人要攻击NPC，这个时候的反应
        不能每个单步step都调用一次LLM来决定下一步做什么。这样子一方面动作一直乱变，另一方面也太费token了。
        decide的作用是，拉取既有的动作链（如果没有了就call_llm），再根据动作链决定动作，以及动作之间的衔接。
    """
    def _decide(self, world: World) -> ACTION_PAIR:
        """
        决策逻辑：通过LLM决定执行什么动作和参数
        """
        action_space_str = ACTION_SPACE_STR
        avatar_infos_str = str(self.avatar)
        regions_str = "\n".join([str(region) for region in world.map.regions.values()])
        avatar_persona = self.avatar.persona.prompt
        dict_info = {
            "action_space": action_space_str,
            "avatar_infos": avatar_infos_str,
            "regions": regions_str,
            "avatar_persona": avatar_persona
        }
        res = get_ai_prompt_and_call_llm(dict_info)
        action_name, action_params = res["action_name"], res["action_params"]
        return action_name, action_params