from __future__ import annotations

from src.classes.action import InstantAction
from src.classes.event import Event


class MoveAwayFromRegion(InstantAction):
    COMMENT = "离开指定区域"
    DOABLES_REQUIREMENTS = "任何时候都可以执行"
    PARAMS = {"region": "RegionName"}

    def _execute(self, region: str) -> None:
        # 简化：向地图边缘移动一步
        dx = 1 if self.avatar.pos_x < self.world.map.width - 1 else -1
        dy = 1 if self.avatar.pos_y < self.world.map.height - 1 else -1
        nx = max(0, min(self.world.map.width - 1, self.avatar.pos_x + dx))
        ny = max(0, min(self.world.map.height - 1, self.avatar.pos_y + dy))
        if self.world.map.is_in_bounds(nx, ny):
            self.avatar.pos_x = nx
            self.avatar.pos_y = ny
            self.avatar.tile = self.world.map.get_tile(nx, ny)

    def can_start(self, region: str | None = None) -> bool:
        return True

    def start(self, region: str) -> Event:
        return Event(self.world.month_stamp, f"{self.avatar.name} 开始离开 {region}")

    # InstantAction 已实现 step 完成

    def finish(self, region: str) -> list[Event]:
        return []


