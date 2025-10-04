from __future__ import annotations

from src.classes.action import DefineAction, ActualActionMixin
from src.classes.event import Event
from src.classes.region import Region
from src.classes.action import Move
from src.classes.action_runtime import ActionResult, ActionStatus


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
        if isinstance(region, str):
            from src.classes.region import regions_by_name

            region = regions_by_name[region]
        cur_loc = (self.avatar.pos_x, self.avatar.pos_y)
        region_center_loc = region.center_loc
        delta_x = region_center_loc[0] - cur_loc[0]
        delta_y = region_center_loc[1] - cur_loc[1]
        # 横纵向一次最多移动 move_step_length 格（可以同时横纵移动）
        step = getattr(self.avatar, "move_step_length", 1)
        delta_x = max(-step, min(step, delta_x))
        delta_y = max(-step, min(step, delta_y))
        Move(self.avatar, self.world).execute(delta_x, delta_y)

    def can_start(self, region: Region | str | None = None) -> bool:
        return True

    def start(self, region: Region | str) -> Event:
        if isinstance(region, str):
            region_name = region
            from src.classes.region import regions_by_name

            if region in regions_by_name:
                region_name = regions_by_name[region].name
        elif hasattr(region, "name"):
            region_name = region.name
        else:
            region_name = str(region)
        return Event(self.world.month_stamp, f"{self.avatar.name} 开始移动向 {region_name}")

    def step(self, region: Region | str) -> ActionResult:
        self.execute(region=region)
        # 完成条件：到达目标区域
        if isinstance(region, str):
            from src.classes.region import regions_by_name

            region = regions_by_name[region]
        done = self.avatar.is_in_region(region)
        return ActionResult(status=(ActionStatus.COMPLETED if done else ActionStatus.RUNNING), events=[])

    def finish(self, region: Region | str) -> list[Event]:
        return []


