from __future__ import annotations

from src.classes.action import InstantAction, Move
from src.classes.event import Event
from src.classes.action.move_helper import clamp_manhattan_with_diagonal_priority


class MoveAwayFromRegion(InstantAction):
    COMMENT = "离开指定区域"
    DOABLES_REQUIREMENTS = "任何时候都可以执行"
    PARAMS = {"region": "RegionName"}

    def _execute(self, region: str) -> None:
        # 策略：朝最近的边界方向移动，曼哈顿步长限制，优先斜向
        width = self.world.map.width
        height = self.world.map.height
        x = self.avatar.pos_x
        y = self.avatar.pos_y

        # 离四边的距离
        dist_left = x
        dist_right = width - 1 - x
        dist_top = y
        dist_bottom = height - 1 - y

        # 选择更近的两个边界方向组成一个大致“远离区域”的方向
        # 简化：朝左右中更近的一侧+上下中更近的一侧移动
        dir_x = -1 if dist_left < dist_right else (1 if dist_right < dist_left else 0)
        dir_y = -1 if dist_top < dist_bottom else (1 if dist_bottom < dist_top else 0)

        step = getattr(self.avatar, "move_step_length", 1)
        dx, dy = clamp_manhattan_with_diagonal_priority(dir_x * step, dir_y * step, step)
        Move(self.avatar, self.world).execute(dx, dy)

    def can_start(self, region: str | None = None) -> bool:
        return True

    def start(self, region: str) -> Event:
        return Event(self.world.month_stamp, f"{self.avatar.name} 开始离开 {region}")

    # InstantAction 已实现 step 完成

    def finish(self, region: str) -> list[Event]:
        return []


