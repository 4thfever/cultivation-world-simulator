"""
event class
"""
from dataclasses import dataclass

from src.classes.calendar import Month, Year

@dataclass
class Event:
    year: Year
    month: Month
    content: str

    def __str__(self) -> str:
        return f"{self.year}年{self.month}月: {self.content}"