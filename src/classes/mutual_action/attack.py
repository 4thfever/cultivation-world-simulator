from __future__ import annotations

from .mutual_action import PressureAction
from src.i18n import t
from src.classes.action.cooldown import cooldown_action
from src.classes.relation.relation_delta_service import RelationDeltaService
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar


@cooldown_action
class MutualAttack(PressureAction):
    """攻击另一个NPC"""
    
    # 多语言 ID
    ACTION_NAME_ID = "mutual_attack_action_name"
    DESC_ID = "mutual_attack_description"
    REQUIREMENTS_ID = "mutual_attack_requirements"
    
    # 不需要翻译的常量
    EMOJI = "⚔️"
    PARAMS = {"target_avatar": "AvatarName"}
    RESPONSE_ACTIONS = ["Escape", "Attack"]
    # 攻击冷却：避免同月连刷攻击
    ACTION_CD_MONTHS: int = 3
    # 攻击是大事（长期记忆）
    IS_MAJOR: bool = True

    def _can_start(self, target: "Avatar") -> tuple[bool, str]:
        """攻击无额外检查条件"""
        from src.classes.observe import is_within_observation
        if not is_within_observation(self.avatar, target):
            return False, t("Target not within interaction range")
        return True, ""

    def _settle_response(self, target_avatar: "Avatar", response_name: str) -> None:
        fb = str(response_name).strip()
        a_to_b, b_to_a = RelationDeltaService.get_fixed_delta("attack", "started")
        RelationDeltaService.apply_bidirectional_delta(self.avatar, target_avatar, a_to_b, b_to_a)
        
        # 此处不产生新事件，仅改变目标行为
        # 目标的行为改变会通过 _set_target_immediate_action -> commit_next_plan 产生新事件
        # 且 commit_next_plan 内部会处理事件分发（理论上）
        # 但我们看看基类的 _set_target_immediate_action 实现
        
        if fb == "Escape":
            params = {"avatar_name": self.avatar.name}
            self._set_target_immediate_action(target_avatar, fb, params, push_start_event=False)
        elif fb == "Attack":
            params = {"avatar_name": self.avatar.name}
            self._set_target_immediate_action(target_avatar, fb, params, push_start_event=False)
