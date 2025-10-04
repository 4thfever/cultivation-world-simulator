from __future__ import annotations

from src.classes.action import TimedAction
from src.classes.event import Event


class MoveAwayFromAvatar(TimedAction):
    """
    持续远离指定角色，持续6个月。
    - 规则：每月尝试使与目标的曼哈顿距离增大一步
    - 任何时候都可以启动
    """

    COMMENT = "持续远离指定角色"
    DOABLES_REQUIREMENTS = "任何时候都可以执行"
    PARAMS = {"avatar_name": "AvatarName"}

    def _find_avatar_by_name(self, name: str) -> "Avatar|None":
        for v in self.world.avatar_manager.avatars.values():
            if v.name == name:
                return v
        return None

    duration_months = 6

    def _execute(self, avatar_name: str) -> None:
        target = self._find_avatar_by_name(avatar_name)
        if target is None:
            return
        # 计算远离方向：使曼哈顿距离尽量增大
        dx = 1 if self.avatar.pos_x >= target.pos_x else -1
        dy = 1 if self.avatar.pos_y >= target.pos_y else -1
        nx = self.avatar.pos_x + dx
        ny = self.avatar.pos_y + dy
        if self.world.map.is_in_bounds(nx, ny):
            self.avatar.pos_x = nx
            self.avatar.pos_y = ny
            self.avatar.tile = self.world.map.get_tile(nx, ny)

    def can_start(self, avatar_name: str | None = None) -> bool:
        return True

    def start(self, avatar_name: str) -> Event:
        target_name = avatar_name
        try:
            t = self._find_avatar_by_name(avatar_name)
            if t is not None:
                target_name = t.name
        except Exception:
            pass
        return Event(self.world.month_stamp, f"{self.avatar.name} 开始远离 {target_name}")

    # TimedAction 已统一 step 逻辑

    def finish(self, avatar_name: str) -> list[Event]:
        return []


