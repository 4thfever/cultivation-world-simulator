from __future__ import annotations

from .mutual_action import MutualAction
from src.classes.action.cooldown import cooldown_action
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.classes.avatar import Avatar


@cooldown_action
class Attack(MutualAction):
    """攻击另一个NPC"""

    ACTION_NAME = "攻击"
    COMMENT = "对目标进行攻击。"
    DOABLES_REQUIREMENTS = "目标在交互范围内；不能连续执行"
    PARAMS = {"target_avatar": "AvatarName"}
    FEEDBACK_ACTIONS = ["Escape", "Battle"]
    STORY_PROMPT: str = ""
    # 攻击冷却：避免同月连刷攻击
    ACTION_CD_MONTHS: int = 3
    # 攻击是大事（长期记忆）
    IS_MAJOR: bool = True

    def _can_start(self, target: "Avatar") -> tuple[bool, str]:
        """攻击无额外检查条件"""
        return True, ""

    def _settle_feedback(self, target_avatar: "Avatar", feedback_name: str) -> None:
        fb = str(feedback_name).strip()
        if fb == "Escape":
            params = {"avatar_name": self.avatar.name}
            self._set_target_immediate_action(target_avatar, fb, params)
        elif fb == "Battle":
            params = {"avatar_name": self.avatar.name}
            self._set_target_immediate_action(target_avatar, fb, params)


