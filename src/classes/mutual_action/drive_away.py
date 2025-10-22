from __future__ import annotations

from .mutual_action import MutualAction
from src.classes.action.cooldown import cooldown_action
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.classes.avatar import Avatar


@cooldown_action
class DriveAway(MutualAction):
    """驱赶：试图让对方离开当前区域。"""

    ACTION_NAME = "驱赶"
    COMMENT = "以武力威慑对方离开此地。"
    DOABLES_REQUIREMENTS = "目标在交互范围内；不能连续执行"
    PARAMS = {"target_avatar": "AvatarName"}
    FEEDBACK_ACTIONS = ["MoveAwayFromRegion", "Battle"]
    STORY_PROMPT: str = ""
    # 驱赶冷却：避免反复驱赶刷屏
    ACTION_CD_MONTHS: int = 3

    def _settle_feedback(self, target_avatar: "Avatar", feedback_name: str) -> None:
        fb = str(feedback_name).strip()
        if fb == "MoveAwayFromRegion":
            # 驱赶选择离开：必定成功，不涉及概率
            params = {"region": self.avatar.tile.region.name}
            self._set_target_immediate_action(target_avatar, fb, params)
        elif fb == "Battle":
            params = {"avatar_name": self.avatar.name}
            self._set_target_immediate_action(target_avatar, fb, params)


