from dataclasses import dataclass

from src.classes.tile import Map
from src.classes.calendar import Year, Month, MonthStamp

@dataclass
class World():
    map: Map
    month_stamp: MonthStamp