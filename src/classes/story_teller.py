from __future__ import annotations

from typing import Dict, TYPE_CHECKING
import random

if TYPE_CHECKING:
    from src.classes.avatar import Avatar

from src.utils.config import CONFIG
from src.utils.llm import call_llm_with_task_name
from src.classes.relations import (
    process_relation_changes,
    get_relation_change_context
)

story_styles = [
    "平淡叙述：语句克制、少修饰、像旁观者记录。",
    "寓情于景：以景见情，情随境迁，情景交融。",
    "写意古风：重意象与比兴，点到为止，少生僻文言。",
    "市井烟火：行文接地气，多用口语化表达，朴实自然，不拿腔拿调。",
    "诗意抒情：短句与对仗点缀，少量用典，不堆砌辞藻。",
    "哲思寓言：借事设问，含一两句点睛之语，不说教。",
    "编年纪事：近史官笔法，记事有序，少形容词。",
    "景物拟人：对景施以轻微拟人，景中含志，不滥。",
    "道法自然：以道家语汇点染，不艰涩，收束于一念。",
    "佛理空相：无常、空相的领悟穿插事中，轻淡不玄。",
    "民间说书：似说书人口吻但用书面语，叙事节奏明快，生动有趣。",
    "雅致书卷：书卷气、引文气息浅尝辄止，不显摆。",
    "豪放旷达：用词大开大合，气势磅礴，不拘小节，直抒胸臆。",
    "绮丽诡谲：重感官描写，辞藻华丽妖冶，强调光影与色彩的奇异感。",
    "冷峻简练：短句为主，字字珠玑，如金石相击，不做多余情感渲染。",
    "细笔白描：不加藻饰，通过捕捉极细微的动作与神态来传神，真实细腻。",
]


class StoryTeller:
    """
    故事生成器：基于模板与 LLM，将给定事件扩展为简短的小故事。
    同时负责处理可能的后天关系变化。
    """
    
    TEMPLATE_SINGLE_PATH = CONFIG.paths.templates / "story_single.txt"
    TEMPLATE_DUAL_PATH = CONFIG.paths.templates / "story_dual.txt"

    @staticmethod
    def _build_avatar_infos(*actors: "Avatar") -> Dict[str, dict]:
        """
        构建角色信息字典。
        - 双人故事：第一个角色使用 expanded_info（包含共同事件），第二个使用普通 info
        - 单人故事：使用 expanded_info
        """
        non_null = [a for a in actors if a is not None]
        avatar_infos: Dict[str, dict] = {}
        
        if len(non_null) >= 2:
            avatar_infos[non_null[0].name] = non_null[0].get_expanded_info(other_avatar=non_null[1], detailed=True)
            avatar_infos[non_null[1].name] = non_null[1].get_info(detailed=True)
        elif non_null:
            avatar_infos[non_null[0].name] = non_null[0].get_expanded_info(detailed=True)
        
        return avatar_infos

    @staticmethod
    def _build_template_data(event: str, res: str, avatar_infos: Dict[str, dict], prompt: str, *actors: "Avatar") -> dict:
        """构建模板渲染所需的数据字典"""
        
        # 默认空关系列表
        avatar_name_1 = ""
        avatar_name_2 = ""
        
        world_info = actors[0].world.static_info
        
        # 如果有两个有效角色，计算可能的关系
        non_null = [a for a in actors if a is not None]
        if len(non_null) >= 2:
            avatar_name_1 = non_null[0].name
            avatar_name_2 = non_null[1].name

        return {
            "world_info": world_info,
            "avatar_infos": avatar_infos,
            "avatar_name_1": avatar_name_1,
            "avatar_name_2": avatar_name_2,
            "event": event,
            "res": res,
            "style": random.choice(story_styles),
            "story_prompt": prompt,
        }

    @staticmethod
    def _make_fallback_story(event: str, res: str, style: str) -> str:
        """生成降级文案"""
        # 不再显示 style，避免出戏
        return f"{event}。{res}。"

    @staticmethod
    async def tell_story(event: str, res: str, *actors: "Avatar", prompt: str = "", allow_relation_changes: bool = False) -> str:
        """
        生成小故事（异步版本）。
        根据 allow_relation_changes 参数选择模板：
        - True: 使用 story_dual.txt，支持关系变化（需要至少2个角色）
        - False: 使用 story_single.txt，仅生成故事（无论角色数量）
        
        Args:
            event: 事件描述
            res: 结果描述
            *actors: 参与的角色（1-2个）
            prompt: 可选的故事提示词
            allow_relation_changes: 是否允许故事导致关系变化，默认为False（单人模式）
        """
        non_null = [a for a in actors if a is not None]
        
        # 只有当允许关系变化且有至少2个角色时，才使用双人模板
        is_dual = allow_relation_changes and len(non_null) >= 2
        
        template_path = StoryTeller.TEMPLATE_DUAL_PATH if is_dual else StoryTeller.TEMPLATE_SINGLE_PATH
        
        avatar_infos = StoryTeller._build_avatar_infos(*actors)
        infos = StoryTeller._build_template_data(event, res, avatar_infos, prompt, *actors)
        
        # 移除了 try-except 块，允许异常向上冒泡，以便 Fail Fast
        data = await call_llm_with_task_name("story_teller", template_path, infos)
        story = data.get("story", "").strip()

        if story:
            return story
        
        return StoryTeller._make_fallback_story(event, res, infos["style"])


__all__ = ["StoryTeller"]
