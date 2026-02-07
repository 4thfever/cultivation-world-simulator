from __future__ import annotations

from src.i18n import t
from src.classes.action import InstantAction
from src.classes.event import Event
from src.systems.battle import get_escape_success_rate
from src.classes.action.event_helper import EventHelper
from src.utils.normalize import normalize_avatar_name


class Escape(InstantAction):
    """
    逃离：尝试从对方身边脱离（有成功率）。
    成功：抢占并进入 MoveAwayFromAvatar(6个月)。
    失败：抢占并进入 Attack。
    """
    
    # 多语言 ID
    ACTION_NAME_ID = "escape_action_name"
    DESC_ID = "escape_description"
    REQUIREMENTS_ID = "escape_requirements"
    
    # 不需要翻译的常量
    EMOJI = "💨"
    PARAMS = {"avatar_name": "AvatarName"}

    def _find_avatar_by_name(self, name: str) -> "Avatar|None":
        """
        根据名字查找角色；找不到返回 None。
        会自动规范化名字（去除括号等附加信息）以提高容错性。
        """
        normalized_name = normalize_avatar_name(name)
        for v in self.world.avatar_manager.avatars.values():
            if v.name == normalized_name:
                return v
        return None

    def _preempt_avatar(self, avatar: "Avatar") -> None:
        avatar.clear_plans()
        avatar.current_action = None

    def _execute(self, avatar_name: str) -> None:
        target = self._find_avatar_by_name(avatar_name)
        if target is None:
            return
        escape_rate = float(get_escape_success_rate(target, self.avatar))
        import random as _r

        success = _r.random() < escape_rate
        result_text = t("succeeded") if success else t("failed")
        content = t("{avatar} attempted to escape from {target}: {result}",
                   avatar=self.avatar.name, target=target.name, result=result_text)
        result_event = Event(self.world.month_stamp, content, related_avatars=[self.avatar.id, target.id])
        EventHelper.push_pair(result_event, initiator=self.avatar, target=target, to_sidebar_once=True)
        if success:
            self._preempt_avatar(self.avatar)
            self.avatar.load_decide_result_chain([("MoveAwayFromAvatar", {"avatar_name": avatar_name})], self.avatar.thinking, "")
            start_event = self.avatar.commit_next_plan()
            if start_event is not None:
                EventHelper.push_pair(start_event, initiator=self.avatar, target=target, to_sidebar_once=True)
        else:
            self._preempt_avatar(self.avatar)
            self.avatar.load_decide_result_chain([("Attack", {"avatar_name": avatar_name})], self.avatar.thinking, "")
            start_event = self.avatar.commit_next_plan()
            if start_event is not None:
                EventHelper.push_pair(start_event, initiator=self.avatar, target=target, to_sidebar_once=True)

    def can_start(self, avatar_name: str) -> tuple[bool, str]:
        return True, ""

    def start(self, avatar_name: str) -> Event:
        target = self._find_avatar_by_name(avatar_name)
        target_name = target.name if target is not None else avatar_name
        rel_ids = [self.avatar.id]
        if target is not None:
            rel_ids.append(target.id)
        content = t("{avatar} attempts to escape from {target}", 
                   avatar=self.avatar.name, target=target_name)
        return Event(self.world.month_stamp, content, related_avatars=rel_ids)

    # InstantAction 已实现 step 完成

    async def finish(self, avatar_name: str) -> list[Event]:
        return []


