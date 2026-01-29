from dataclasses import dataclass, asdict
from typing import List, Optional
from enum import Enum
from src.classes.calendar import MonthStamp


class MetricTag(Enum):
    """預設的度量標籤"""
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
    Avatar 狀態快照，用於追蹤角色成長軌跡。

    設計原則：
    - 輕量：僅記錄關鍵指標
    - 不可變：快照一旦創建不修改
    - 可選：不影響現有功能
    """
    timestamp: MonthStamp
    age: int

    # 修為相關
    cultivation_level: int
    cultivation_progress: int

    # 資源相關
    hp: float
    hp_max: float
    spirit_stones: int

    # 社會相關
    relations_count: int
    known_regions_count: int

    # 標記
    tags: List[str]

    def to_save_dict(self) -> dict:
        """轉換為可序列化的字典（用於存檔）"""
        return asdict(self)

    @classmethod
    def from_save_dict(cls, data: dict) -> "AvatarMetrics":
        """從字典重建（用於讀檔）"""
        return cls(**data)
