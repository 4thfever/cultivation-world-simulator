"""
event class
"""
from dataclasses import dataclass, field
from typing import List, Optional
import uuid

from src.classes.calendar import Month, Year, MonthStamp

@dataclass
class Event:
    month_stamp: MonthStamp
    content: str
    # 相关角色ID列表；若与任何角色无关则为 None
    related_avatars: Optional[List[str]] = None
    # 是否为大事（长期记忆），默认False（小事/短期记忆）
    is_major: bool = False
    # 是否为故事事件（不进入记忆索引），默认False
    is_story: bool = False
    # 唯一ID，用于去重
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __str__(self) -> str:
        year = self.month_stamp.get_year()
        month = self.month_stamp.get_month()
        return f"{year}年{month}月: {self.content}"
    
    def to_dict(self) -> dict:
        """转换为可序列化的字典"""
        return {
            "month_stamp": int(self.month_stamp),
            "content": self.content,
            "related_avatars": self.related_avatars,
            "is_major": self.is_major,
            "is_story": self.is_story,
            "id": self.id
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Event":
        """从字典重建Event"""
        return cls(
            month_stamp=MonthStamp(data["month_stamp"]),
            content=data["content"],
            related_avatars=data.get("related_avatars"),
            is_major=data.get("is_major", False),
            is_story=data.get("is_story", False),
            id=data.get("id", str(uuid.uuid4()))
        )

class NullEvent:
    """
    空事件单例类
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __str__(self) -> str:
        return ""
    
    def __bool__(self) -> bool:
        """使NullEvent实例在布尔上下文中为False"""
        return False

# 全局单例实例
NULL_EVENT = NullEvent()

def is_null_event(event) -> bool:
    """检查事件是否为空事件的便捷函数"""
    return event is NULL_EVENT
