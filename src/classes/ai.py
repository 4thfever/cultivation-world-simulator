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
from src.classes.event import Event, NULL_EVENT
from src.utils.llm import get_ai_prompt_and_call_llm_async
from src.classes.typings import ACTION_NAME, ACTION_PARAMS, ACTION_PAIR
from src.utils.config import CONFIG

if TYPE_CHECKING:
    from src.classes.avatar import Avatar

class AI(ABC):
    """
    抽象AI：统一采用批量接口。
    原先的 GroupAI（多个角色的AI）语义被保留并上移到此基类。
    子类需实现 _decide(world, avatars) 返回每个 Avatar 的 (action_name, action_params, thinking)。
    """

    @abstractmethod
    async def _decide(self, world: World, avatars_to_decide: list[Avatar]) -> dict[Avatar, tuple[ACTION_NAME, ACTION_PARAMS, str]]:
        pass

    async def decide(self, world: World, avatars_to_decide: list[Avatar]) -> dict[Avatar, tuple[ACTION_NAME, ACTION_PARAMS, str, Event]]:
        """
        决定做什么，同时生成对应的事件。
        一个ai支持批量生成多个avatar的动作。
        这对LLM AI节省时间和token非常有意义。
        """
        results = {}
        max_decide_num = CONFIG.ai.max_decide_num
        for i in range(0, len(avatars_to_decide), max_decide_num):
            results.update(await self._decide(world, avatars_to_decide[i:i+max_decide_num]))

        for avatar, result in list(results.items()):
            action_name, action_params, avatar_thinking = result
            action = avatar.create_action(action_name)
            event = action.get_event(**action_params)
            results[avatar] = (action_name, action_params, avatar_thinking, event)

        return results

class RuleAI(AI):
    """
    规则AI（批量接口，内部逐个决策）
    """

    def __decide(self, world: World, avatar: "Avatar", regions: list[Region]) -> tuple[ACTION_NAME, ACTION_PARAMS, str]:
        """
        单个 Avatar 的决策逻辑。
        先做一个简单的：
        1. 找到自己灵根对应的最好的区域
        2. 检测自己是否在最好的区域
        3. 如果不在，则移动到最好的区域
        4. 如果已经到达最好的区域，则进行修炼
        5. 如果需要突破境界了，则突破境界
        """
        if random.random() < 0.1:
            return ("Play", {}, "")

        best_region = self.get_best_region_for_avatar(avatar, regions)

        if avatar.is_in_region(best_region):
            if avatar.cultivation_progress.can_break_through():
                return ("Breakthrough", {}, "")
            else:
                return ("Cultivate", {}, "")
        else:
            return ("MoveToRegion", {"region": best_region.name}, "")

    async def _decide(self, world: World, avatars_to_decide: list[Avatar]) -> dict[Avatar, tuple[ACTION_NAME, ACTION_PARAMS, str]]:
        """
        决策逻辑：批量接口的实现上，逐个 Avatar 调用 __decide 进行独立决策，
        以保持规则AI的可控性与可测试性。
        """
        results: dict[Avatar, tuple[ACTION_NAME, ACTION_PARAMS, str]] = {}
        regions: list[Region] = list(world.map.regions.values())

        for avatar in avatars_to_decide:
            results[avatar] = self.__decide(world, avatar, regions)

        return results

    def get_best_region_for_avatar(self, avatar: "Avatar", regions: list[Region]) -> Region:
        """
        根据avatar的灵根找到最适合的区域
        """
        essence_type = corres_essence_type[avatar.root]
        region_with_best_essence = max(
            regions, key=lambda region: region.essence.get_density(essence_type)
        )
        return region_with_best_essence

class LLMAI(AI):
    """
    LLM AI
    一些思考：
    AI动作应该分两类：
        1. 长期动作，比如要持续很长一段时间的行为
        2. 突发应对动作，比如突然有人要攻击NPC，这个时候的反应
    """

    async def _decide(self, world: World, avatars_to_decide: list[Avatar]) -> dict[Avatar, tuple[ACTION_NAME, ACTION_PARAMS, str]]:
        """
        异步决策逻辑：通过LLM决定执行什么动作和参数
        """
        global_info = world.get_prompt()
        avatar_infos = {avatar.id: avatar.get_prompt() for avatar in avatars_to_decide}
        info = {
            "avatar_infos": avatar_infos,
            "global_info": global_info,
        }
        res = await get_ai_prompt_and_call_llm_async(info)
        results: dict[Avatar, tuple[ACTION_NAME, ACTION_PARAMS, str]] = {}
        for avatar in avatars_to_decide:
            action_name = res[avatar.id]["action_name"]
            action_params = res[avatar.id]["action_params"]
            avatar_thinking = res[avatar.id]["avatar_thinking"]
            results[avatar] = (action_name, action_params, avatar_thinking)
        return results

llm_ai = LLMAI()
rule_ai = RuleAI()