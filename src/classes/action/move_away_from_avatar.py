from __future__ import annotations

from src.classes.action import TimedAction, Move
from src.classes.event import Event
from src.classes.action.move_helper import clamp_manhattan_with_diagonal_priority
from src.classes.normalize import normalize_avatar_name
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.classes.avatar import Avatar


class MoveAwayFromAvatar(TimedAction):
    """
    持续远离指定角色，持续6个月。
    - 规则：每月尝试使与目标的曼哈顿距离增大一步
    - 任何时候都可以启动
    """

    ACTION_NAME = "远离角色"
    EMOJI = "🏃"
    DESC = "持续远离指定角色"
    DOABLES_REQUIREMENTS = "无限制"
    PARAMS = {"avatar_name": "AvatarName"}

    def _find_avatar_by_name(self, name: str) -> "Avatar | None":
        """
        根据名字查找角色；找不到返回 None。
        会自动规范化名字（去除括号等附加信息）以提高容错性。
        """
        normalized_name = normalize_avatar_name(name)
        for v in self.world.avatar_manager.avatars.values():
            if v.name == normalized_name:
                return v
        return None

    duration_months = 6

    def _execute(self, avatar_name: str) -> None:
        target = self._find_avatar_by_name(avatar_name)
        if target is None:
            return
        # 远离方向：以目标到自身的向量取反
        raw_dx = -(target.pos_x - self.avatar.pos_x)
        raw_dy = -(target.pos_y - self.avatar.pos_y)
        step = getattr(self.avatar, "move_step_length", 1)
        dx, dy = clamp_manhattan_with_diagonal_priority(raw_dx, raw_dy, step)
        Move(self.avatar, self.world).execute(dx, dy)

    def can_start(self, avatar_name: str | None = None) -> tuple[bool, str]:
        return True, ""

    def start(self, avatar_name: str) -> Event:
        target_name = avatar_name
        try:
            t = self._find_avatar_by_name(avatar_name)
            if t is not None:
                target_name = t.name
        except Exception:
            pass
        rel_ids = [self.avatar.id]
        try:
            t = self._find_avatar_by_name(avatar_name)
            if t is not None:
                rel_ids.append(t.id)
        except Exception:
            pass
        return Event(self.world.month_stamp, f"{self.avatar.name} 开始远离 {target_name}", related_avatars=rel_ids)

    # TimedAction 已统一 step 逻辑

    async def finish(self, avatar_name: str) -> list[Event]:
        return []


