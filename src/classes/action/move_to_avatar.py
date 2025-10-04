from __future__ import annotations

from src.classes.action import DefineAction, ActualActionMixin
from src.classes.event import Event
from src.classes.action import Move
from src.classes.action_runtime import ActionResult, ActionStatus


class MoveToAvatar(DefineAction, ActualActionMixin):
    """
    朝另一个角色当前位置移动。
    """

    COMMENT = "移动到某个角色所在位置"
    DOABLES_REQUIREMENTS = "任何时候都可以执行"
    PARAMS = {"avatar_name": "str"}

    def _get_target(self, avatar_name: str):
        """
        根据名字查找目标角色；找不到返回 None。
        """
        for v in self.world.avatar_manager.avatars.values():
            if v.name == avatar_name:
                return v
        return None

    def _execute(self, avatar_name: str) -> None:
        target = self._get_target(avatar_name)
        if target is None:
            return
        cur_loc = (self.avatar.pos_x, self.avatar.pos_y)
        target_loc = (target.pos_x, target.pos_y)
        delta_x = target_loc[0] - cur_loc[0]
        delta_y = target_loc[1] - cur_loc[1]
        step = getattr(self.avatar, "move_step_length", 1)
        delta_x = max(-step, min(step, delta_x))
        delta_y = max(-step, min(step, delta_y))
        Move(self.avatar, self.world).execute(delta_x, delta_y)

    def can_start(self, avatar_name: str | None = None) -> bool:
        target = self._get_target(avatar_name)
        if target is None:
            return False
        return True

    def start(self, avatar_name: str) -> Event:
        target = self._get_target(avatar_name)
        target_name = target.name if target is not None else avatar_name
        return Event(self.world.month_stamp, f"{self.avatar.name} 开始移动向 {target_name}")

    def step(self, avatar_name: str) -> ActionResult:
        self.execute(avatar_name=avatar_name)
        target = self._get_target(avatar_name)
        if target is None:
            return ActionResult(status=ActionStatus.COMPLETED, events=[])
        done = self.avatar.tile == target.tile
        return ActionResult(status=(ActionStatus.COMPLETED if done else ActionStatus.RUNNING), events=[])

    def finish(self, avatar_name: str) -> list[Event]:
        return []


