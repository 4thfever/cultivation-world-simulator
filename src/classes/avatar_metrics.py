from dataclasses import dataclass, asdict
from typing import List, Optional
from enum import Enum
from src.classes.calendar import MonthStamp


class MetricTag(Enum):
    """预定义的度量标签"""
    BREAKTHROUGH = "breakthrough"
    INJURED = "injured"
    RECOVERED = "recovered"
    SECT_JOIN = "sect_join"
    SECT_LEAVE = "sect_leave"
    TECHNIQUE_LEARN = "technique_learn"
    DEATH = "death"
    BATTLE = "battle"
    DUNGEON = "dungeon"


@dataclass
class AvatarMetrics:
    """
    Avatar 状态快照，用于追踪角色成长轨迹。

    设计原则：
    - 轻量：仅记录关键指标
    - 不可变：快照一旦创建不修改
    - 可选：不影响现有功能
    """
    timestamp: MonthStamp
    age: int

    # 修为相关
    cultivation_level: int
    cultivation_progress: int

    # 资源相关
    hp: float
    hp_max: float
    spirit_stones: int

    # 社会相关
    relations_count: int
    known_regions_count: int

    # 标记
    tags: List[str]

    def to_save_dict(self) -> dict:
        """转换为可序列化的字典（用于存档）"""
        return asdict(self)

    @classmethod
    def from_save_dict(cls, data: dict) -> "AvatarMetrics":
        """从字典重建（用于读档）"""
        return cls(**data)
