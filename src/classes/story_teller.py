from __future__ import annotations

from typing import Dict, TYPE_CHECKING
import asyncio
import random

from src.utils.config import CONFIG
from src.utils.llm import get_prompt_and_call_llm, get_prompt_and_call_llm_async

story_styles = [
    "平淡叙述：语句克制、少修饰、像旁观者记录。",
    "寓情于景：以景见情，情随境迁，情景交融。",
    "写意古风：重意象与比兴，点到为止，少生僻文言。",
    "市井烟火：接地气，含些俗语但不粗鄙，烟火气足。",
    "悬疑铺垫：埋伏笔与反转，信息递进，结尾留一丝余味。",
    "诗意抒情：短句与对仗点缀，少量用典，不堆砌辞藻。",
    "哲思寓言：借事设问，含一两句点睛之语，不说教。",
    "黑色幽默：以反差与轻描淡写呈现荒诞，克制机锋。",
    "编年纪事：近史官笔法，记事有序，少形容词。",
    "碎片蒙太奇：并置数个短镜头，以意连形，留白。",
    "景物拟人：对景施以轻微拟人，景中含志，不滥。",
    "道法自然：以道家语汇点染，不艰涩，收束于一念。",
    "佛理空相：无常、空相的领悟穿插事中，轻淡不玄。",
    "民间说书：似说书人口吻但用书面语，收尾有眼。",
    "雅致书卷：书卷气、引文气息浅尝辄止，不显摆。",
]


class StoryTeller:
    """
    故事生成器：基于模板与 LLM，将给定事件扩展为简短的小故事。
    """

    @staticmethod
    def build_avatar_infos(*avatars: "Avatar") -> Dict[str, dict]:
        """
        将若干角色信息组织为 {name: info_dict} 映射，供故事模板使用。
        战斗/小故事使用详细信息（dict 版）。
        """
        infos: Dict[str, dict] = {}
        for av in avatars:
            if av is None:
                continue
            infos[av.name] = av.get_info(detailed=True)
        return infos

    @staticmethod
    def tell_story(event: str, res: str, *actors: "Avatar", prompt: str = "") -> str:
        """
        基于 `static/templates/story.txt` 模板生成小故事。
        始终使用 fast 模式以提升速度。
        失败时返回降级版文案，避免中断流程。
        
        Args:
            event: 事件描述
            res: 结果描述
            *actors: 参与的角色（1-2个）
            prompt: 可选的故事提示词
        """
        # 构建 avatar_infos，第一个 avatar 使用 expanded_info
        non_null = [a for a in actors if a is not None]
        avatar_infos: Dict[str, dict] = {}
        
        if len(non_null) >= 2:
            # 双人故事：第一个用 expanded_info（包含共同事件），第二个用 detailed info
            avatar_infos[non_null[0].name] = non_null[0].get_expanded_info(other_avatar=non_null[1], detailed=True)
            avatar_infos[non_null[1].name] = non_null[1].get_info(detailed=True)
        elif non_null:
            # 单人故事：直接用 expanded_info
            avatar_infos[non_null[0].name] = non_null[0].get_expanded_info(detailed=True)
        
        template_path = CONFIG.paths.templates / "story.txt"
        infos = {
            "avatar_infos": avatar_infos,
            "event": event,
            "res": res,
            "style": random.choice(story_styles),
            "story_prompt": prompt,
        }
        try:
            data = get_prompt_and_call_llm(template_path, infos, mode="fast")
            story = data.get("story", "").strip()
            if story:
                return story
        except Exception:
            pass
        # 降级文案（不中断主流程）
        style = infos.get("style", "")
        return f"{event}。{res}。{style}"

    @staticmethod
    async def tell_story_async(event: str, res: str, *actors: "Avatar", prompt: str = "") -> str:
        """
        异步版本：生成小故事，失败时返回降级文案。
        
        Args:
            event: 事件描述
            res: 结果描述
            *actors: 参与的角色（1-2个）
            prompt: 可选的故事提示词
        """
        # 构建 avatar_infos，第一个 avatar 使用 expanded_info
        non_null = [a for a in actors if a is not None]
        avatar_infos: Dict[str, dict] = {}
        
        if len(non_null) >= 2:
            # 双人故事：第一个用 expanded_info（包含共同事件），第二个用 detailed info
            avatar_infos[non_null[0].name] = non_null[0].get_expanded_info(other_avatar=non_null[1], detailed=True)
            avatar_infos[non_null[1].name] = non_null[1].get_info(detailed=True)
        elif non_null:
            # 单人故事：直接用 expanded_info
            avatar_infos[non_null[0].name] = non_null[0].get_expanded_info(detailed=True)
        
        template_path = CONFIG.paths.templates / "story.txt"
        infos = {
            "avatar_infos": avatar_infos,
            "event": event,
            "res": res,
            "style": random.choice(story_styles),
            "story_prompt": prompt,
        }
        try:
            data = await get_prompt_and_call_llm_async(template_path, infos, mode="fast")
            story = str(data.get("story", "")).strip()
            if story:
                return story
        except Exception:
            pass
        style = infos.get("style", "")
        return f"{event}。{res}。{style}"

    @staticmethod
    def tell_from_actors(event: str, res: str, *actors: "Avatar", prompt: str | None = None) -> str:
        """
        便捷方法别名，保持向后兼容。直接调用 tell_story。
        """
        return StoryTeller.tell_story(event, res, *actors, prompt=prompt or "")

    @staticmethod
    async def tell_from_actors_async(event: str, res: str, *actors: "Avatar", prompt: str | None = None) -> str:
        """
        便捷方法别名，保持向后兼容。直接调用 tell_story_async。
        """
        return await StoryTeller.tell_story_async(event, res, *actors, prompt=prompt or "")


__all__ = ["StoryTeller"]



if TYPE_CHECKING:
    # 仅用于类型检查，避免循环导入
    from src.classes.avatar import Avatar

