from __future__ import annotations

from typing import TYPE_CHECKING

from src.i18n import t
from .mutual_action import InvitationAction
from src.classes.action.cooldown import cooldown_action
from src.classes.event import Event
from src.classes.story_event_service import StoryEventKind, StoryEventService
from src.classes.close_relation_event_service import (
    apply_positive_bond_warmth,
    configure_positive_bond_event,
)
from src.classes.relation.relation_delta_service import RelationDeltaService
from src.classes.relation.relation import Relation

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar


@cooldown_action
class Confess(InvitationAction):
    """表白：向交互范围内的修士表白，若对方接受则结为道侣。
    """
    
    # 多语言 ID
    ACTION_NAME_ID = "confess_action_name"
    DESC_ID = "confess_description"
    REQUIREMENTS_ID = "confess_requirements"
    STORY_PROMPT_ID = "confess_story_prompt"
    
    # 不需要翻译的常量
    EMOJI = "💌"
    PARAMS = {"target_avatar": "AvatarName"}
    RESPONSE_ACTIONS = ["Accept", "Reject"]
    
    # 表白的社交冷却：避免频繁请求
    ACTION_CD_MONTHS: int = 6
    # 表白是大事（长期记忆）
    IS_MAJOR: bool = True

    def _can_start(self, target: "Avatar") -> tuple[bool, str]:
        """检查表白特有的启动条件"""
        from src.classes.observe import is_within_observation
        if not is_within_observation(self.avatar, target):
            return False, t("Target not within interaction range")
            
        if self.avatar.has_identity_relation(target, Relation.IS_LOVER_OF) or self.avatar.get_relation(target) == Relation.IS_LOVER_OF:
            return False, t("Already lovers")
            
        return True, ""

    def start(self, target_avatar: "Avatar|str") -> Event:
        target = self._get_target_avatar(target_avatar)
        target_name = target.name if target is not None else str(target_avatar)
        rel_ids = [self.avatar.id]
        if target is not None:
            rel_ids.append(target.id)
        
        content = t("{initiator} confesses their love to {target}",
                   initiator=self.avatar.name, target=target_name)
        event = Event(self.world.month_stamp, content, related_avatars=rel_ids, is_major=False)
        
        # 记录开始文本用于故事生成
        self._start_event_content = event.content
        # 初始化内部标记
        self._confess_success = False
        return event

    def _settle_response(self, target_avatar: "Avatar", response_name: str) -> None:
        fb = str(response_name).strip()
        if fb == "Accept":
            # 接受则结为道侣
            self.avatar.become_lovers_with(target_avatar)
            self._confess_success = True
        else:
            # 拒绝
            self._confess_success = False

    async def finish(self, target_avatar: "Avatar|str", **kwargs) -> list[Event]:
        target = self._get_target_avatar(target_avatar)
        events: list[Event] = []
        if target is None:
            return events

        if self._confess_success:
            result_text = t("{target} accepted {initiator}'s confession, they became lovers",
                          target=target.name, initiator=self.avatar.name)
            a_to_b, b_to_a = RelationDeltaService.get_fixed_delta("confess", "accepted")
        else:
            result_text = t("{target} rejected {initiator}'s confession",
                          target=target.name, initiator=self.avatar.name)
            a_to_b, b_to_a = RelationDeltaService.get_fixed_delta("confess", "rejected")

        RelationDeltaService.apply_bidirectional_delta(self.avatar, target, a_to_b, b_to_a)
            
        event_type = "bond_lovers_formed" if self._confess_success else "bond_lovers_rejected"
        result_event = Event(
            self.world.month_stamp,
            result_text,
            related_avatars=[self.avatar.id, target.id],
            is_major=True,
            event_type=event_type,
        )
        if self._confess_success:
            configure_positive_bond_event(result_event, avatar_a=self.avatar, avatar_b=target)
            apply_positive_bond_warmth(subject=self.avatar, other_party=target, event_type=event_type)
            apply_positive_bond_warmth(subject=target, other_party=self.avatar, event_type=event_type)
        
        events.append(result_event)

        # 生成表白小故事
        start_text = getattr(self, "_start_event_content", "") or result_event.content
        story_event = await StoryEventService.maybe_create_story(
            kind=StoryEventKind.RELATIONSHIP_MAJOR,
            month_stamp=self.world.month_stamp,
            start_text=start_text,
            result_text=result_event.content,
            actors=[self.avatar, target],
            related_avatar_ids=[self.avatar.id, target.id],
            prompt=self.get_story_prompt(),
            allow_relation_changes=True,
        )
        if story_event is not None:
            events.append(story_event)

        return events
