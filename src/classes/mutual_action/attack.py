from __future__ import annotations

from .mutual_action import MutualAction


class Attack(MutualAction):
    """攻击另一个NPC"""

    ACTION_NAME = "攻击"
    COMMENT = "对目标进行攻击。"
    DOABLES_REQUIREMENTS = "与目标处于同一区域"
    PARAMS = {"target_avatar": "AvatarName"}
    FEEDBACK_ACTIONS = ["Escape", "Battle"]
    STORY_PROMPT: str = ""

    def _settle_feedback(self, target_avatar: "Avatar", feedback_name: str) -> None:
        fb = str(feedback_name).strip()
        if fb == "Escape":
            params = {"avatar_name": self.avatar.name}
            self._set_target_immediate_action(target_avatar, fb, params)
        elif fb == "Battle":
            params = {"avatar_name": self.avatar.name}
            self._set_target_immediate_action(target_avatar, fb, params)


