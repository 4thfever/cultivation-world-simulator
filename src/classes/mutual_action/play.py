from __future__ import annotations
from typing import TYPE_CHECKING
import random

from src.classes.mutual_action.mutual_action import MutualAction
from src.i18n import t
from src.utils.config import CONFIG

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar
    from src.classes.core.world import World

def try_trigger_play_benefit(avatar: Avatar) -> str:
    """
    尝试触发消遣收益 (复用单人消遣的逻辑)
    """
    prob = CONFIG.play.base_benefit_probability if hasattr(CONFIG, 'play') else 0.05
    
    if random.random() < prob:
        rate = 0.2
        avatar.add_breakthrough_rate(rate)
        return t("breakthrough probability increased by {val:.1%}", val=rate)
    return ""

class TeaParty(MutualAction):
    """茶会：双人互动"""
    ACTION_NAME_ID = "action_tea_party"
    DESC_ID = "action_tea_party_desc"
    STORY_PROMPT_ID = "action_tea_party_story_prompt"
    REQUIREMENTS_ID = "play_requirements"
    EMOJI = "🍵"
    FEEDBACK_ACTIONS = ["Accept", "Reject"] 
    
    def _settle_feedback(self, target_avatar: Avatar, feedback_name: str) -> None:
        if feedback_name == "Accept":
            # 尝试给双方触发收益
            try_trigger_play_benefit(self.avatar)
            try_trigger_play_benefit(target_avatar)

class Chess(MutualAction):
    """下棋：双人互动"""
    ACTION_NAME_ID = "action_chess"
    DESC_ID = "action_chess_desc"
    STORY_PROMPT_ID = "action_chess_story_prompt"
    REQUIREMENTS_ID = "play_requirements"
    EMOJI = "♟️"
    FEEDBACK_ACTIONS = ["Accept", "Reject"]

    def _settle_feedback(self, target_avatar: Avatar, feedback_name: str) -> None:
        if feedback_name == "Accept":
            # 尝试给双方触发收益
            try_trigger_play_benefit(self.avatar)
            try_trigger_play_benefit(target_avatar)
