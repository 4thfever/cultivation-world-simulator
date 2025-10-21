from __future__ import annotations

from src.classes.action import DefineAction, ActualActionMixin
from src.classes.event import Event
from src.classes.region import Region, resolve_region
from src.classes.action import Move
from src.classes.action_runtime import ActionResult, ActionStatus
from src.classes.action.move_helper import clamp_manhattan_with_diagonal_priority


class MoveToRegion(DefineAction, ActualActionMixin):
    """
    移动到某个region
    """

    COMMENT = "移动到某个区域"
    DOABLES_REQUIREMENTS = "任何时候都可以执行"
    PARAMS = {"region": "region_name"}

    def _execute(self, region: Region | str) -> None:
        """
        移动到某个region
        """
        region = self._resolve_region(region)
        cur_loc = (self.avatar.pos_x, self.avatar.pos_y)
        region_center_loc = region.center_loc
        raw_dx = region_center_loc[0] - cur_loc[0]
        raw_dy = region_center_loc[1] - cur_loc[1]
        step = getattr(self.avatar, "move_step_length", 1)
        dx, dy = clamp_manhattan_with_diagonal_priority(raw_dx, raw_dy, step)
        Move(self.avatar, self.world).execute(dx, dy)

    def can_start(self, region: Region | str | None = None) -> tuple[bool, str]:
        if region is None:
            return False, "缺少参数 region"
        try:
            resolve_region(self.world, region)
            return True, ""
        except Exception:
            return False, f"无法解析区域: {region}"

    def start(self, region: Region | str) -> Event:
        r = resolve_region(self.world, region)
        region_name = r.name  # 仅使用规范化后的区域名
        return Event(self.world.month_stamp, f"{self.avatar.name} 开始移动向 {region_name}", related_avatars=[self.avatar.id])

    def step(self, region: Region | str) -> ActionResult:
        self.execute(region=region)
        # 完成条件：到达目标区域
        r = resolve_region(self.world, region)
        # 常规：基于 tile.region 精确判定；兜底：当前位置坐标属于目标区域的格点集合
        done = self.avatar.is_in_region(r) or ((self.avatar.pos_x, self.avatar.pos_y) in getattr(r, "cors", ()))
        return ActionResult(status=(ActionStatus.COMPLETED if done else ActionStatus.RUNNING), events=[])

    def finish(self, region: Region | str) -> list[Event]:
        return []


