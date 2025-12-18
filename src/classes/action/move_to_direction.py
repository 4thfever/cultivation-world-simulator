from __future__ import annotations

import random
from src.classes.action import DefineAction, ActualActionMixin, Move
from src.classes.event import Event
from src.classes.action_runtime import ActionResult, ActionStatus
from src.utils.distance import manhattan_distance
from src.classes.region import Region

class Direction:
    """
    方向管理类，统一管理方向的向量定义和名称转换
    """
    # 向量映射 (假设 (0,0) 在左上角)
    # North: y减小
    # South: y增加
    # West: x减小
    # East: x增加
    _VECTORS = {
        "North": (0, -1),
        "South": (0, 1),
        "West": (-1, 0),
        "East": (1, 0),
        "北": (0, -1),
        "南": (0, 1),
        "西": (-1, 0),
        "东": (1, 0)
    }
    
    # 中文名称映射
    _CN_NAMES = {
        "North": "北",
        "South": "南",
        "West": "西",
        "East": "东",
        "北": "北",
        "南": "南",
        "西": "西",
        "东": "东"
    }

    @classmethod
    def is_valid(cls, direction: str) -> bool:
        return direction in cls._VECTORS

    @classmethod
    def get_vector(cls, direction: str) -> tuple[int, int]:
        return cls._VECTORS.get(direction, (0, 0))

    @classmethod
    def get_cn_name(cls, direction: str) -> str:
        return cls._CN_NAMES.get(direction, direction)


class MoveToDirection(DefineAction, ActualActionMixin):
    """
    向某个方向移动探索（固定时长6个月）
    """
    
    ACTION_NAME = "移动探索"
    DESC = "向某个方向探索未知区域"
    DOABLES_REQUIREMENTS = "无限制"
    PARAMS = {"direction": "direction (North/South/East/West)"}
    IS_MAJOR = False
    
    # 固定持续时间
    DURATION = 6

    def __init__(self, avatar, world):
        super().__init__(avatar, world)
        # 记录本次动作的开始状态
        self.start_monthstamp = None
        self.direction = None

    def can_start(self, direction: str | None = None) -> tuple[bool, str]:
        if not direction:
            return False, "缺少方向参数"
        if not Direction.is_valid(direction):
            return False, f"无效的方向: {direction}"
        return True, ""

    def start(self, direction: str) -> Event:
        self.start_monthstamp = self.world.month_stamp
        self.direction = direction
        direction_cn = Direction.get_cn_name(direction)
        return Event(self.world.month_stamp, f"{self.avatar.name} 开始向{direction_cn}方移动", related_avatars=[self.avatar.id])

    def step(self, direction: str) -> ActionResult:
        # 确保方向已设置
        self.direction = direction
        dx_dir, dy_dir = Direction.get_vector(direction)
        
        # 计算本次移动步长
        step_len = getattr(self.avatar, "move_step_length", 1)
        
        # 计算实际位移
        dx = dx_dir * step_len
        dy = dy_dir * step_len
        
        # 执行移动
        Move(self.avatar, self.world).execute(dx, dy)
        
        # 检查是否完成（固定时长）
        # 修正：(current - start) >= duration - 1，即第1个月执行后，差值为0，如果duration=1则完成
        elapsed = self.world.month_stamp - self.start_monthstamp
        is_done = elapsed >= (self.DURATION - 1)
        
        return ActionResult(status=(ActionStatus.COMPLETED if is_done else ActionStatus.RUNNING), events=[])

    async def finish(self, direction: str) -> list[Event]:
        direction_cn = Direction.get_cn_name(direction)
        return [Event(self.world.month_stamp, f"{self.avatar.name} 结束了向{direction_cn}方的移动", related_avatars=[self.avatar.id])]

    def _execute(self, *args, **kwargs):
        pass