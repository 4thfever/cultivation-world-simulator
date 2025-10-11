from __future__ import annotations

from typing import Dict, TYPE_CHECKING

from src.utils.config import CONFIG
from src.utils.llm import get_prompt_and_call_llm


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
            try:
                infos[av.name] = av.get_info(detailed=True)
            except Exception:
                infos[av.name] = getattr(av, "name", "未知角色")
        return infos

    @staticmethod
    def tell_story(avatar_infos: Dict[str, dict], event: str, res: str) -> str:
        """
        基于 `static/templates/story.txt` 模板生成小故事。
        始终使用 fast 模式以提升速度。
        失败时返回降级版文案，避免中断流程。
        """
        template_path = CONFIG.paths.templates / "story.txt"
        infos = {
            "avatar_infos": avatar_infos,
            "event": event,
            "res": res,
        }
        try:
            data = get_prompt_and_call_llm(template_path, infos, mode="fast")
            story = str(data.get("story", "")).strip()
            if story:
                return story
        except Exception:
            return (res or event or "")
        return (res or event or "")


__all__ = ["StoryTeller"]



if TYPE_CHECKING:
    # 仅用于类型检查，避免循环导入
    from src.classes.avatar import Avatar

