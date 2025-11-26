"""
Nickname 数据类
"""
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class Nickname:
    """
    绰号数据类
    包含绰号本身及其来源原因
    """
    value: str
    reason: str
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "Nickname":
        if not data:
            return None
        return cls(
            value=data["value"],
            reason=data["reason"]
        )
    
    def __str__(self) -> str:
        return self.value

