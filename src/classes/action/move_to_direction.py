from __future__ import annotations

import random
from src.i18n import t
from src.classes.action import DefineAction, ActualActionMixin, Move
from src.classes.event import Event
from src.classes.action_runtime import ActionResult, ActionStatus
from src.utils.distance import manhattan_distance
from src.classes.environment.region import Region

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
        "north": (0, -1),
        "south": (0, 1),
        "west": (-1, 0),
        "east": (1, 0),
        "北": (0, -1),
        "南": (0, 1),
        "西": (-1, 0),
        "东": (1, 0),
        "東": (1, 0),
    }
    
    # 中文名称映射
    _CN_NAMES = {
        "North": "北",
        "South": "南",
        "West": "西",
        "East": "东",
        "north": "北",
        "south": "南",
        "west": "西",
        "east": "东",
        "北": "北",
        "南": "南",
        "西": "西",
        "东": "东",
        "東": "东",
    }

    _MSGIDS = {
        "North": "north",
        "South": "south",
        "West": "west",
        "East": "east",
        "north": "north",
        "south": "south",
        "west": "west",
        "east": "east",
        "北": "north",
        "南": "south",
        "西": "west",
        "东": "east",
        "東": "east",
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

    @classmethod
    def get_msgid(cls, direction: str) -> str:
        return cls._MSGIDS.get(direction, direction)


class MoveToDirection(DefineAction, ActualActionMixin):
    """
    向某个方向移动探索（固定时长6个月）
    """
    
    # 多语言 ID
    ACTION_NAME_ID = "move_to_direction_action_name"
    DESC_ID = "move_to_direction_description"
    REQUIREMENTS_ID = "move_to_direction_requirements"
    
    # 不需要翻译的常量
    EMOJI = "🧭"
    PARAMS = {"direction": "direction (north/south/east/west)"}
    IS_MAJOR = False
    
    # 固定持续时间
    DURATION = 6

    def __init__(self, avatar, world):
        super().__init__(avatar, world)
        # 记录本次动作的开始状态
        self.start_monthstamp = None
        self.direction = None

    def can_start(self, direction: str) -> tuple[bool, str]:
        if not Direction.is_valid(direction):
            return False, t("Invalid direction: {direction}", direction=direction)
        return True, ""

    def start(self, direction: str) -> Event:
        self.start_monthstamp = self.world.month_stamp
        self.direction = direction
        direction_translated = t(Direction.get_msgid(direction))
        content = t("{avatar} begins moving toward {direction}",
                   avatar=self.avatar.name, direction=direction_translated)
        return Event(self.world.month_stamp, content, related_avatars=[self.avatar.id])

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
        direction_translated = t(Direction.get_msgid(direction))
        content = t("{avatar} finished moving toward {direction}",
                   avatar=self.avatar.name, direction=direction_translated)
        return [Event(self.world.month_stamp, content, related_avatars=[self.avatar.id])]

    def _execute(self, *args, **kwargs):
        pass
