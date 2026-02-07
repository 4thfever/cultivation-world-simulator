from __future__ import annotations

import random
from src.i18n import t
from src.classes.action import DefineAction, ActualActionMixin
from src.classes.event import Event
from src.classes.environment.region import Region
from src.classes.environment.sect_region import SectRegion
from src.classes.action import Move
from src.classes.action_runtime import ActionResult, ActionStatus
from src.classes.action.move_helper import clamp_manhattan_with_diagonal_priority
from src.utils.resolution import resolve_query


class MoveToRegion(DefineAction, ActualActionMixin):
    """
    移动到某个region
    """
    
    # 多语言 ID
    ACTION_NAME_ID = "move_to_region_action_name"
    DESC_ID = "move_to_region_description"
    REQUIREMENTS_ID = "move_to_region_requirements"
    
    # 不需要翻译的常量
    EMOJI = "🏃"
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
        target_region = resolve_query(region, self.world, expected_types=[Region]).obj
        if not target_region:
            return

        target_loc = self._get_target_loc(target_region)
        
        cur_loc = (self.avatar.pos_x, self.avatar.pos_y)
        raw_dx = target_loc[0] - cur_loc[0]
        raw_dy = target_loc[1] - cur_loc[1]
        
        step = getattr(self.avatar, "move_step_length", 1)
        dx, dy = clamp_manhattan_with_diagonal_priority(raw_dx, raw_dy, step)
        Move(self.avatar, self.world).execute(dx, dy)

    def can_start(self, region: Region | str) -> tuple[bool, str]:
        r = resolve_query(region, self.world, expected_types=[Region]).obj
        if not r:
            return False, t("Cannot resolve region: {region}", region=region)
            
        # 宗门总部限制：非本门弟子禁止入内
        if isinstance(r, SectRegion):
            if self.avatar.sect is None or self.avatar.sect.id != r.sect_id:
                return False, t("[{region}] is another sect's territory, you are not a disciple of that sect", region=r.name)
        
        return True, ""

    def start(self, region: Region | str) -> Event:
        r = resolve_query(region, self.world, expected_types=[Region]).obj
        # 这里理论上在 can_start 已经校验过，但为了安全再校验一次，如果None则不处理（实际上不会发生）
        if r:
            region_name = r.name
            # 在开始时就确定目标点
            self._get_target_loc(r)
            content = t("{avatar} begins moving toward {region}",
                       avatar=self.avatar.name, region=region_name)
            return Event(self.world.month_stamp, content, related_avatars=[self.avatar.id])
        content = t("{avatar} attempted to move but target is invalid", avatar=self.avatar.name)
        return Event(self.world.month_stamp, content, related_avatars=[self.avatar.id])

    def step(self, region: Region | str) -> ActionResult:
        self.execute(region=region)
        
        r = resolve_query(region, self.world, expected_types=[Region]).obj
        if not r:
             return ActionResult(status=ActionStatus.FAILED, events=[])

        target_loc = self._get_target_loc(r)
        
        # 完成条件：到达具体的随机目标点
        cur_loc = (self.avatar.pos_x, self.avatar.pos_y)
        done = (cur_loc == target_loc)
        
        return ActionResult(status=(ActionStatus.COMPLETED if done else ActionStatus.RUNNING), events=[])

    async def finish(self, region: Region | str) -> list[Event]:
        return []
