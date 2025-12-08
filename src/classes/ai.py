"""
NPC AI 的类。
这里指的是 NPC 的决策机制。
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
import asyncio

from src.classes.world import World
from src.classes.event import Event, NULL_EVENT
from src.utils.llm import call_ai_action
from src.classes.typings import ACTION_NAME_PARAMS_PAIRS
from src.utils.config import CONFIG
from src.classes.actions import ACTION_INFOS_STR

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
        一个 AI 支持批量生成多个 avatar 的动作。
        这对 LLM AI 节省时间和 token 非常有意义。
        """
        results = {}
        max_decide_num = CONFIG.ai.max_decide_num
        
        # 使用 asyncio.gather 并行执行多个批次的决策
        tasks = []
        for i in range(0, len(avatars_to_decide), max_decide_num):
             tasks.append(self._decide(world, avatars_to_decide[i:i+max_decide_num]))
             
        if tasks:
            batch_results_list = await asyncio.gather(*tasks)
            for batch_result in batch_results_list:
                results.update(batch_result)

        for avatar, result in list(results.items()):
            action_name_params_pairs, avatar_thinking, short_term_objective = result  # type: ignore
            # 不在决策阶段生成开始事件，提交阶段统一触发
            results[avatar] = (action_name_params_pairs, avatar_thinking, short_term_objective, NULL_EVENT)

        return results

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
        改动：支持每个角色仅获取其已知区域的世界信息，并发调用 LLM。
        """
        general_action_infos = ACTION_INFOS_STR
        async def decide_one(avatar: Avatar):
            # 获取基于该角色已知区域的世界信息（包含距离计算）
            world_info = world.get_info(avatar=avatar, detailed=True)
            
            # 在提示中包含处于角色观测范围内的其他角色
            observed = world.get_observable_avatars(avatar)
            avatar_info = avatar.get_expanded_info(co_region_avatars=observed)
            
            info = {
                "avatar_info": avatar_info,
                "world_info": world_info,
                "general_action_infos": general_action_infos,
            }
            res = await call_ai_action(info)
            return avatar, res

        tasks = [decide_one(avatar) for avatar in avatars_to_decide]
        results_list = await asyncio.gather(*tasks)
        
        results: dict[Avatar, tuple[ACTION_NAME_PARAMS_PAIRS, str, str]] = {}
        for avatar, res in results_list:
            if not res or avatar.name not in res:
                continue
                
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
            short_term_objective = r.get("short_term_objective", "")
            results[avatar] = (pairs, avatar_thinking, short_term_objective)
            
        return results

llm_ai = LLMAI()