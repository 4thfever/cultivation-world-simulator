"""
event class
"""
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, List, Optional
import uuid
import time

from src.systems.time import Month, Year, MonthStamp, get_date_str

if TYPE_CHECKING:
    from src.classes.event_observation import EventObservation

@dataclass
class Event:
    month_stamp: MonthStamp
    content: str
    # 相关角色ID列表；若与任何角色无关则为 None
    related_avatars: Optional[List[str]] = None
    # 相关宗门ID列表；若与任何宗门无关则为 None
    related_sects: Optional[List[int]] = None
    # 是否为大事（长期记忆），默认False（小事/短期记忆）
    is_major: bool = False
    # 是否为故事事件（不进入记忆索引），默认False
    is_story: bool = False
    # 事实事件类型，用于传播与渲染
    event_type: str = ""
    # 前端可本地化渲染用的模板 key
    render_key: Optional[str] = None
    # 前端模板渲染参数
    render_params: Optional[dict[str, Any]] = None
    # 唯一ID，用于去重
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    # 创建时间戳 (Unix timestamp float)
    created_at: float = field(default_factory=time.time)
    # 运行时挂载的 observation，统一由 EventManager 持久化
    observations: List["EventObservation"] = field(default_factory=list, repr=False, compare=False)

    def __str__(self) -> str:
        return f"{get_date_str(int(self.month_stamp))}: {self.content}"
    
    def to_dict(self) -> dict:
        """转换为可序列化的字典"""
        return {
            "month_stamp": int(self.month_stamp),
            "content": self.content,
            "related_avatars": self.related_avatars,
            "related_sects": self.related_sects,
            "is_major": self.is_major,
            "is_story": self.is_story,
            "event_type": self.event_type,
            "render_key": self.render_key,
            "render_params": self.render_params,
            "id": self.id,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Event":
        """从字典重建Event"""
        return cls(
            month_stamp=MonthStamp(data["month_stamp"]),
            content=data["content"],
            related_avatars=data.get("related_avatars"),
            related_sects=data.get("related_sects"),
            is_major=data.get("is_major", False),
            is_story=data.get("is_story", False),
            event_type=data.get("event_type", ""),
            render_key=data.get("render_key"),
            render_params=data.get("render_params"),
            id=data.get("id", str(uuid.uuid4())),
            created_at=data.get("created_at", time.time())
        )

class NullEvent:
    """
    空事件单例类，保持与 Event 相同的最小接口，避免调用方访问属性时报错。
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # 初始化一次即可
            cls._instance.month_stamp = MonthStamp(0)
            cls._instance.content = ""
            cls._instance.related_avatars = None
            cls._instance.related_sects = None
            cls._instance.is_major = False
            cls._instance.is_story = False
            cls._instance.event_type = ""
            cls._instance.render_key = None
            cls._instance.render_params = None
            cls._instance.id = "NULL_EVENT"
            cls._instance.observations = []
        return cls._instance
    
    def __str__(self) -> str:
        return ""
    
    def __bool__(self) -> bool:
        """使NullEvent实例在布尔上下文中为False"""
        return False
    
    def to_dict(self) -> dict:
        """保持序列化接口"""
        return {
            "month_stamp": int(self.month_stamp),
            "content": self.content,
            "related_avatars": self.related_avatars,
            "related_sects": self.related_sects,
            "is_major": self.is_major,
            "is_story": self.is_story,
            "event_type": self.event_type,
            "render_key": self.render_key,
            "render_params": self.render_params,
            "id": self.id,
        }

# 全局单例实例
NULL_EVENT = NullEvent()

def is_null_event(event) -> bool:
    """检查事件是否为空事件的便捷函数"""
    return event is NULL_EVENT
