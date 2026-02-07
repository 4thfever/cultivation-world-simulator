from dataclasses import dataclass, field
from src.classes.gender import Gender
from src.systems.time import MonthStamp

@dataclass
class Mortal:
    """
    轻量级的凡人/子女数据结构。
    仅用于存储非修仙者的子女信息，不参与复杂模拟。
    """
    id: str                 # 唯一标识
    name: str               # 姓名
    gender: Gender          # 性别
    birth_month_stamp: MonthStamp  # 出生时间戳
    parents: list[str] = field(default_factory=list)      # 父母的 Avatar ID
    born_region_id: int = -1  # 出身地区域ID (-1表示未知)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "gender": self.gender.value,
            "birth_month_stamp": int(self.birth_month_stamp),
            "parents": self.parents,
            "born_region_id": self.born_region_id
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Mortal":
        """从字典还原"""
        return cls(
            id=data["id"],
            name=data["name"],
            gender=Gender(data["gender"]),
            birth_month_stamp=MonthStamp(data["birth_month_stamp"]),
            parents=data.get("parents", []),
            born_region_id=data.get("born_region_id", -1)
        )
