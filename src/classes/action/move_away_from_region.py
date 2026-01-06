from __future__ import annotations

from src.classes.action import InstantAction, Move
from src.classes.event import Event
from src.classes.action.move_helper import clamp_manhattan_with_diagonal_priority
from src.classes.region import Region
from src.utils.distance import euclidean_distance
from src.utils.resolution import resolve_query


class MoveAwayFromRegion(InstantAction):
    ACTION_NAME = "离开区域"
    EMOJI = "🏃"
    DESC = "离开指定区域"
    DOABLES_REQUIREMENTS = "无限制"
    PARAMS = {"region": "RegionName"}

    def _execute(self, region: str) -> None:
        # 解析目标区域，并沿“远离该区域最近格点”的方向移动一步
        r = resolve_query(region, self.world, expected_types=[Region]).obj
        if not r:
            return

        x = self.avatar.pos_x
        y = self.avatar.pos_y
        # 找到目标区域内距离当前坐标最近的格点
        if getattr(r, "cors", None):
            nearest = min(r.cors, key=lambda p: euclidean_distance((x, y), p))
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

    def can_start(self, region: str) -> tuple[bool, str]:
        if resolve_query(region, self.world, expected_types=[Region]).obj:
            return True, ""
        return False, f"无法解析区域: {region}"

    def start(self, region: str) -> Event:
        r = resolve_query(region, self.world, expected_types=[Region]).obj
        region_name = r.name if r else region
        return Event(self.world.month_stamp, f"{self.avatar.name} 开始离开 {region_name}", related_avatars=[self.avatar.id])

    # InstantAction 已实现 step 完成

    async def finish(self, region: str) -> list[Event]:
        return []
