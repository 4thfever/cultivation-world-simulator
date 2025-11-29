from __future__ import annotations

from src.classes.action import InstantAction
from src.classes.event import Event
from src.classes.battle import get_escape_success_rate
from src.classes.action.event_helper import EventHelper
from src.classes.normalize import normalize_avatar_name


class Escape(InstantAction):
    """
    逃离：尝试从对方身边脱离（有成功率）。
    成功：抢占并进入 MoveAwayFromAvatar(6个月)。
    失败：抢占并进入 Attack。
    """

    COMMENT = "逃离对方（基于成功率判定）"
    DOABLES_REQUIREMENTS = "任何时候都可以执行"
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

    def _add_event_pair(self, event: Event, initiator: "Avatar", target: "Avatar|None") -> None:
        initiator.add_event(event)
        if target is not None:
            target.add_event(event, to_sidebar=False)

    def _execute(self, avatar_name: str) -> None:
        target = self._find_avatar_by_name(avatar_name)
        if target is None:
            return
        escape_rate = float(get_escape_success_rate(target, self.avatar))
        import random as _r

        success = _r.random() < escape_rate
        result_text = "成功" if success else "失败"
        result_event = Event(self.world.month_stamp, f"{self.avatar.name} 试图从 {target.name} 逃离：{result_text}", related_avatars=[self.avatar.id, target.id])
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

    def can_start(self, avatar_name: str | None = None) -> tuple[bool, str]:
        return True, ""

    def start(self, avatar_name: str) -> Event:
        target = self._find_avatar_by_name(avatar_name)
        target_name = target.name if target is not None else avatar_name
        rel_ids = [self.avatar.id]
        if target is not None:
            rel_ids.append(target.id)
        return Event(self.world.month_stamp, f"{self.avatar.name} 尝试从 {target_name} 逃离", related_avatars=rel_ids)

    # InstantAction 已实现 step 完成

    async def finish(self, avatar_name: str) -> list[Event]:
        return []


