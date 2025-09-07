from dataclasses import dataclass

from src.classes.tile import Map
from src.classes.calendar import Year, Month, MonthStamp

@dataclass
class World():
    map: Map
    month_stamp: MonthStamp

    def get_prompt(self) -> str:
        regions_str = "\n".join([str(region) for region in self.map.regions.values()])
        return f"世界地图上存在的区域为：{regions_str}"