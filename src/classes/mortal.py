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
