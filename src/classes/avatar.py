from dataclasses import dataclass
from enum import Enum

from src.classes.calendar import Month, Year

class Gender(Enum):
    MALE = "male"
    FEMALE = "female"

@dataclass
class Avatar:
    name: str
    id: int
    brith_month: Month
    birth_year: Year
    age: int
    gender: Gender
