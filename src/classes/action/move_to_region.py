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

    def _resolve_region(self, region: Region | str) -> Region:
        """
        将字符串或全局Region实例解析为当前world.map中的Region实例：
        - 优先使用 world.map.region_names
        - 若传入是 Region 实例，按 id 映射到 world.map.regions
        - 兜底返回原对象（避免KeyError中断）
        """
        try:
            if isinstance(region, str):
                return self.world.map.region_names.get(region) or region  # type: ignore[return-value]
            # 非字符串：按 id 在 map 中取对应实例
            rid = getattr(region, "id", None)
            if rid is not None and rid in self.world.map.regions:
                return self.world.map.regions[rid]
            return region
        except Exception:
            return region

    def _execute(self, region: Region | str) -> None:
        """
        移动到某个region
        """
        region = self._resolve_region(region)
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
        r = self._resolve_region(region)
        region_name = getattr(r, "name", str(region))
        return Event(self.world.month_stamp, f"{self.avatar.name} 开始移动向 {region_name}")

    def step(self, region: Region | str) -> ActionResult:
        self.execute(region=region)
        # 完成条件：到达目标区域
        r = self._resolve_region(region)
        done = self.avatar.is_in_region(r if isinstance(r, Region) else None)
        return ActionResult(status=(ActionStatus.COMPLETED if done else ActionStatus.RUNNING), events=[])

    def finish(self, region: Region | str) -> list[Event]:
        return []


