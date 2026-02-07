"""
NPC AI 的类。
这里指的是 NPC 的决策机制。
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
import asyncio

from src.classes.core.world import World
from src.classes.event import Event, NULL_EVENT
from src.utils.llm import call_llm_with_task_name
from src.classes.typings import ACTION_NAME_PARAMS_PAIRS
from src.classes.actions import get_action_infos_str
from src.utils.config import CONFIG

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar

class AI(ABC):
    """
    抽象AI：统一采用批量接口。
    """

    @abstractmethod
    async def _decide(self, world: World, avatars_to_decide: list[Avatar]) -> dict[Avatar, tuple]:
        pass

    async def decide(self, world: World, avatars_to_decide: list[Avatar]) -> dict[Avatar, tuple[ACTION_NAME_PARAMS_PAIRS, str, str, Event]]:
        """
        决定做什么，同时生成对应的事件。
        由于底层 LLM 调用已接入全局任务池，此处直接并发执行所有任务即可。
        """
        # 调用具体的决策逻辑
        results = await self._decide(world, avatars_to_decide)

        # 补全 Event 字段
        for avatar in list(results.keys()):
            action_name_params_pairs, avatar_thinking, short_term_objective = results[avatar]  # type: ignore
            # 不在决策阶段生成开始事件，提交阶段统一触发
            results[avatar] = (action_name_params_pairs, avatar_thinking, short_term_objective, NULL_EVENT)

        return results

class LLMAI(AI):
    """
    LLM AI
    """

    async def _decide(self, world: World, avatars_to_decide: list[Avatar]) -> dict[Avatar, tuple[ACTION_NAME_PARAMS_PAIRS, str, str]]:
        """
        异步决策逻辑：通过LLM决定执行什么动作和参数
        """
        general_action_infos = get_action_infos_str()
        
        async def decide_one(avatar: Avatar):
            # 获取基于该角色已知区域的世界信息（包含距离计算）
            world_info = world.get_info(avatar=avatar, detailed=True)
            
            # 在提示中包含处于角色观测范围内的其他角色
            observed = world.get_observable_avatars(avatar)
            avatar_info = avatar.get_expanded_info(co_region_avatars=observed)
            
            info = {
                "avatar_name": avatar.name,
                "avatar_info": avatar_info,
                "world_info": world_info,
                "general_action_infos": general_action_infos,
            }
            template_path = CONFIG.paths.templates / "ai.txt"
            res = await call_llm_with_task_name("action_decision", template_path, info)
            return avatar, res

        # 直接并发所有任务
        tasks = [decide_one(avatar) for avatar in avatars_to_decide]
        results_list = await asyncio.gather(*tasks)
        
        results: dict[Avatar, tuple[ACTION_NAME_PARAMS_PAIRS, str, str]] = {}
        for avatar, res in results_list:
            if not res or avatar.name not in res:
                continue
                
            r = res[avatar.name]
            # 仅接受 action_name_params_pairs，不再支持单个 action_name/action_params
            raw_pairs = r.get("action_name_params_pairs", [])
            pairs: ACTION_NAME_PARAMS_PAIRS = []
            
            for p in raw_pairs:
                if isinstance(p, list) and len(p) == 2:
                    # LLM 可能返回 null 作为 params，需要转为空字典。
                    pairs.append((p[0], p[1] or {}))
                elif isinstance(p, dict) and "action_name" in p and "action_params" in p:
                    pairs.append((p["action_name"], p["action_params"] or {}))
                else:
                    continue
            
            # 至少有一个
            if not pairs:
                continue # Skip if no valid actions found

            avatar_thinking = r.get("avatar_thinking", r.get("thinking", ""))
            short_term_objective = r.get("short_term_objective", "")
            
            # 更新情绪
            from src.classes.emotions import EmotionType
            raw_emotion = r.get("current_emotion", "emotion_calm")
            try:
                # 尝试通过 value 获取枚举
                avatar.emotion = EmotionType(raw_emotion)
            except ValueError:
                avatar.emotion = EmotionType.CALM
                
            results[avatar] = (pairs, avatar_thinking, short_term_objective)
            
        return results

llm_ai = LLMAI()
