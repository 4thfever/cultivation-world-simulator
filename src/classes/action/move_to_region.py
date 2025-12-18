from __future__ import annotations

import random
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

    ACTION_NAME = "移动到区域"
    DESC = "移动到某个区域"
    DOABLES_REQUIREMENTS = "无限制"
    PARAMS = {"region": "region_name"}

    def __init__(self, avatar, world):
        super().__init__(avatar, world)
        self.target_loc = None

    def _get_target_loc(self, region: Region) -> tuple[int, int]:
        """
        获取或生成本次移动的目标坐标。
        如果尚未生成，则从区域坐标集合中随机选取一个。
        """
        if self.target_loc is not None:
            # 简单的校验：确保目标点属于该区域（防止区域变动等极端情况，可选）
            return self.target_loc

        if hasattr(region, "cors") and region.cors:
            self.target_loc = random.choice(region.cors)
        else:
            # 兜底：如果区域没有坐标集合，使用中心点
            self.target_loc = region.center_loc
        
        return self.target_loc

    def _execute(self, region: Region | str) -> None:
        """
        移动到某个region
        """
        region = resolve_region(self.world, region)
        target_loc = self._get_target_loc(region)
        
        cur_loc = (self.avatar.pos_x, self.avatar.pos_y)
        raw_dx = target_loc[0] - cur_loc[0]
        raw_dy = target_loc[1] - cur_loc[1]
        
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
        region_name = r.name
        # 在开始时就确定目标点
        self._get_target_loc(r)
        return Event(self.world.month_stamp, f"{self.avatar.name} 开始移动向 {region_name}", related_avatars=[self.avatar.id])

    def step(self, region: Region | str) -> ActionResult:
        self.execute(region=region)
        
        r = resolve_region(self.world, region)
        target_loc = self._get_target_loc(r)
        
        # 完成条件：到达具体的随机目标点
        cur_loc = (self.avatar.pos_x, self.avatar.pos_y)
        done = (cur_loc == target_loc)
        
        return ActionResult(status=(ActionStatus.COMPLETED if done else ActionStatus.RUNNING), events=[])

    async def finish(self, region: Region | str) -> list[Event]:
        return []


