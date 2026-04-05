from __future__ import annotations
from typing import TYPE_CHECKING
import random

from src.classes.event import Event
from src.classes.mutual_action.mutual_action import InvitationAction
from src.classes.story_event_service import StoryEventKind, StoryEventService
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

class TeaParty(InvitationAction):
    """茶会：双人互动"""
    ACTION_NAME_ID = "action_tea_party"
    DESC_ID = "action_tea_party_desc"
    STORY_PROMPT_ID = "action_tea_party_story_prompt"
    REQUIREMENTS_ID = "play_requirements"
    EMOJI = "🍵"
    RESPONSE_ACTIONS = ["Accept", "Reject"] 

    def __init__(self, avatar: Avatar, world: World):
        super().__init__(avatar, world)
        self._play_success = False
    
    def _settle_response(self, target_avatar: Avatar, response_name: str) -> None:
        if response_name == "Accept":
            # 尝试给双方触发收益
            try_trigger_play_benefit(self.avatar)
            try_trigger_play_benefit(target_avatar)
            self._play_success = True
        else:
            self._play_success = False

    async def finish(self, target_avatar: "Avatar|str") -> list:
        target = self._get_target_avatar(target_avatar)
        if target is None or not self._play_success:
            return []

        result_text = t(
            "{initiator} and {target} enjoyed a tea gathering",
            initiator=self.avatar.name,
            target=target.name,
        )
        result_event = Event(
            self.world.month_stamp,
            result_text,
            related_avatars=[self.avatar.id, target.id],
        )
        story_event = await StoryEventService.maybe_create_story(
            kind=StoryEventKind.DAILY_SOCIAL,
            month_stamp=self.world.month_stamp,
            start_text=getattr(self, "_start_event_content", ""),
            result_text=result_text,
            actors=[self.avatar, target],
            related_avatar_ids=[self.avatar.id, target.id],
            prompt=self.get_story_prompt(),
            allow_relation_changes=False,
        )
        events = [result_event]
        if story_event is not None:
            events.append(story_event)
        return events

class Chess(InvitationAction):
    """下棋：双人互动"""
    ACTION_NAME_ID = "action_chess"
    DESC_ID = "action_chess_desc"
    STORY_PROMPT_ID = "action_chess_story_prompt"
    REQUIREMENTS_ID = "play_requirements"
    EMOJI = "♟️"
    RESPONSE_ACTIONS = ["Accept", "Reject"]

    def __init__(self, avatar: Avatar, world: World):
        super().__init__(avatar, world)
        self._play_success = False

    def _settle_response(self, target_avatar: Avatar, response_name: str) -> None:
        if response_name == "Accept":
            # 尝试给双方触发收益
            try_trigger_play_benefit(self.avatar)
            try_trigger_play_benefit(target_avatar)
            self._play_success = True
        else:
            self._play_success = False

    async def finish(self, target_avatar: "Avatar|str") -> list:
        target = self._get_target_avatar(target_avatar)
        if target is None or not self._play_success:
            return []

        result_text = t(
            "{initiator} and {target} played a game of chess",
            initiator=self.avatar.name,
            target=target.name,
        )
        result_event = Event(
            self.world.month_stamp,
            result_text,
            related_avatars=[self.avatar.id, target.id],
        )
        story_event = await StoryEventService.maybe_create_story(
            kind=StoryEventKind.DAILY_SOCIAL,
            month_stamp=self.world.month_stamp,
            start_text=getattr(self, "_start_event_content", ""),
            result_text=result_text,
            actors=[self.avatar, target],
            related_avatar_ids=[self.avatar.id, target.id],
            prompt=self.get_story_prompt(),
            allow_relation_changes=False,
        )
        events = [result_event]
        if story_event is not None:
            events.append(story_event)
        return events
