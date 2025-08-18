from dataclasses import dataclass
from enum import Enum

from src.classes.calendar import Month, Year

class Gender(Enum):
    MALE = "male"
    FEMALE = "female"

@dataclass
class Avatar:
    """
    NPC的类。
    包含了这个角色的一切信息。
    """
    name: str
    id: int
    birth_month: Month
    birth_year: Year
    age: int
    gender: Gender
