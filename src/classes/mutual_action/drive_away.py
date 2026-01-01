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
    EMOJI = "😤"
    DESC = "以武力威慑对方离开此地。"
    DOABLES_REQUIREMENTS = "目标在交互范围内；不能连续执行"
    PARAMS = {"target_avatar": "AvatarName"}
    FEEDBACK_ACTIONS = ["MoveAwayFromRegion", "Attack"]
    STORY_PROMPT: str = ""
    # 驱赶冷却：避免反复驱赶刷屏
    ACTION_CD_MONTHS: int = 3

    def _can_start(self, target: "Avatar") -> tuple[bool, str]:
        """驱赶无额外检查条件"""
        # 必须在有效区域内才能驱赶（因为需要指定 MoveAwayFromRegion 的目标区域）
        if self.avatar.tile.region is None:
            return False, "荒野之中无法驱赶"
            
        from src.classes.observe import is_within_observation
        if not is_within_observation(self.avatar, target):
            return False, "目标不在交互范围内"
        return True, ""

    def _settle_feedback(self, target_avatar: "Avatar", feedback_name: str) -> None:
        fb = str(feedback_name).strip()
        if fb == "MoveAwayFromRegion":
            # 驱赶选择离开：必定成功，不涉及概率
            params = {"region": self.avatar.tile.location_name}
            self._set_target_immediate_action(target_avatar, fb, params)
        elif fb == "Attack":
            params = {"avatar_name": self.avatar.name}
            self._set_target_immediate_action(target_avatar, fb, params)


