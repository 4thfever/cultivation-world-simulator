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
from src.classes.region import Region
from src.classes.root import corres_essence_type
from src.classes.event import Event, NULL_EVENT
from src.utils.llm import get_ai_prompt_and_call_llm_async
from src.classes.typings import ACTION_NAME, ACTION_PARAMS, ACTION_PAIR, ACTION_NAME_PARAMS_PAIRS
from src.utils.config import CONFIG
from src.classes.action import ACTION_INFOS_STR

if TYPE_CHECKING:
    from src.classes.avatar import Avatar

class AI(ABC):
    """
    抽象AI：统一采用批量接口。
    原先的 GroupAI（多个角色的AI）语义被保留并上移到此基类。
    子类需实现 _decide(world, avatars) 返回每个 Avatar 的 (action_name, action_params, thinking)。
    """

    @abstractmethod
    async def _decide(self, world: World, avatars_to_decide: list[Avatar]) -> dict[Avatar, tuple]:
        pass

    async def decide(self, world: World, avatars_to_decide: list[Avatar]) -> dict[Avatar, tuple[ACTION_NAME_PARAMS_PAIRS, str, str, Event]]:
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
            # 兼容：RuleAI 返回单动作，LLMAI 返回动作链
            if result and isinstance(result[0], list):
                action_name_params_pairs, avatar_thinking, objective = result  # type: ignore
            else:
                action_name, action_params, avatar_thinking, objective = result  # type: ignore
                action_name_params_pairs = [(action_name, action_params)]
            # 只为队列中的第一个动作生成事件
            first_action_name, first_action_params = action_name_params_pairs[0]
            action = avatar.create_action(first_action_name)
            event = action.get_event(**first_action_params)
            results[avatar] = (action_name_params_pairs, avatar_thinking, objective, event)

        return results

class RuleAI(AI):
    """
    规则AI（批量接口，内部逐个决策）
    """

    def __decide(self, world: World, avatar: "Avatar", regions: list[Region]) -> tuple[ACTION_NAME, ACTION_PARAMS, str, str]:
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
            return ("Play", {}, "", "放松一下，缓解修行压力")

        best_region = self.get_best_region_for_avatar(avatar, regions)

        if avatar.is_in_region(best_region):
            if avatar.cultivation_progress.can_break_through():
                return ("Breakthrough", {}, "", "尽快突破到更高境界")
            else:
                return ("Cultivate", {}, "", "稳步提升修为")
        else:
            return ("MoveToRegion", {"region": best_region.name}, "", f"前往{best_region.name}修行")

    async def _decide(self, world: World, avatars_to_decide: list[Avatar]) -> dict[Avatar, tuple[ACTION_NAME, ACTION_PARAMS, str, str]]:
        """
        决策逻辑：批量接口的实现上，逐个 Avatar 调用 __decide 进行独立决策，
        以保持规则AI的可控性与可测试性。
        """
        results: dict[Avatar, tuple[ACTION_NAME, ACTION_PARAMS, str, str]] = {}
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

    async def _decide(self, world: World, avatars_to_decide: list[Avatar]) -> dict[Avatar, tuple[ACTION_NAME_PARAMS_PAIRS, str, str]]:
        """
        异步决策逻辑：通过LLM决定执行什么动作和参数
        """
        global_info = world.get_info()
        avatar_infos = {avatar.name: avatar.get_prompt_info() for avatar in avatars_to_decide}
        general_action_infos = ACTION_INFOS_STR
        info = {
            "avatar_infos": avatar_infos,
            "global_info": global_info,
            "general_action_infos": general_action_infos,
        }
        res = await get_ai_prompt_and_call_llm_async(info)
        results: dict[Avatar, tuple[ACTION_NAME_PARAMS_PAIRS, str, str]] = {}
        for avatar in avatars_to_decide:
            r = res[avatar.name]
            # 仅接受 action_name_params_pairs，不再支持单个 action_name/action_params
            raw_pairs = r["action_name_params_pairs"]
            pairs: ACTION_NAME_PARAMS_PAIRS = []
            for p in raw_pairs:
                if isinstance(p, list) and len(p) == 2:
                    pairs.append((p[0], p[1]))
                elif isinstance(p, dict) and "action_name" in p and "action_params" in p:
                    pairs.append((p["action_name"], p["action_params"]))
                else:
                    # 跳过无法解析的项
                    continue
            # 至少有一个
            if not pairs:
                raise ValueError(f"LLM未返回有效的action_name_params_pairs: {r}")

            avatar_thinking = r.get("avatar_thinking", r.get("thinking", ""))
            objective = r.get("objective", "")
            results[avatar] = (pairs, avatar_thinking, objective)
        return results

llm_ai = LLMAI()
rule_ai = RuleAI()