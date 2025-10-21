from __future__ import annotations

from src.classes.action import InstantAction, Move
from src.classes.event import Event
from src.classes.action.move_helper import clamp_manhattan_with_diagonal_priority
from src.classes.region import Region, resolve_region
from src.classes.region import resolve_region


class MoveAwayFromRegion(InstantAction):
    COMMENT = "离开指定区域"
    DOABLES_REQUIREMENTS = "任何时候都可以执行"
    PARAMS = {"region": "RegionName"}

    def _execute(self, region: str) -> None:
        # 解析目标区域，并沿“远离该区域最近格点”的方向移动一步
        r: Region = resolve_region(self.world, region)
        x = self.avatar.pos_x
        y = self.avatar.pos_y
        # 找到目标区域内距离当前坐标最近的格点
        if getattr(r, "cors", None):
            nearest = min(r.cors, key=lambda p: (p[0] - x) * (p[0] - x) + (p[1] - y) * (p[1] - y))
            away_dx = x - nearest[0]
            away_dy = y - nearest[1]
        else:
            # 无 cors（极少数异常），退化为“远离地图中心”
            cx, cy = self.world.map.width // 2, self.world.map.height // 2
            away_dx = x - cx
            away_dy = y - cy

        step = getattr(self.avatar, "move_step_length", 1)
        dx, dy = clamp_manhattan_with_diagonal_priority(away_dx, away_dy, step)
        Move(self.avatar, self.world).execute(dx, dy)

    def can_start(self, region: str | None = None) -> bool:
        if region is None:
            return True
        try:
            resolve_region(self.world, region)
            return True
        except Exception:
            return False

    def start(self, region: str) -> Event:
        r = resolve_region(self.world, region)
        return Event(self.world.month_stamp, f"{self.avatar.name} 开始离开 {r.name}", related_avatars=[self.avatar.id])

    # InstantAction 已实现 step 完成

    def finish(self, region: str) -> list[Event]:
        return []


