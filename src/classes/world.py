from dataclasses import dataclass

from src.classes.tile import Map
from src.classes.calendar import Year, Month

@dataclass
class World():
    map: Map
    year: Year
    month: Month