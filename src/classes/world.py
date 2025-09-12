from dataclasses import dataclass

from src.classes.map import Map
from src.classes.calendar import Year, Month, MonthStamp

@dataclass
class World():
    map: Map
    month_stamp: MonthStamp

    def get_info(self) -> str:
        map_intro = "世界上的区域为："
        map_info = self.map.get_info()
        info = f"{map_intro}\n{map_info}"
        return info