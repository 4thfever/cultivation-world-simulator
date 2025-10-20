"""
event class
"""
from dataclasses import dataclass
from typing import List, Optional

from src.classes.calendar import Month, Year, MonthStamp

@dataclass
class Event:
    month_stamp: MonthStamp
    content: str
    # 相关角色ID列表；若与任何角色无关则为 None
    related_avatars: Optional[List[str]] = None

    def __str__(self) -> str:
        year = self.month_stamp.get_year()
        month = self.month_stamp.get_month()
        return f"{year}年{month}月: {self.content}"

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