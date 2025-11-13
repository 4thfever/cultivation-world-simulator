from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from src.classes.map import Map
from src.classes.calendar import Year, Month, MonthStamp
from src.classes.avatar_manager import AvatarManager
from src.classes.event_manager import EventManager

if TYPE_CHECKING:
    from src.classes.avatar import Avatar
    from src.classes.celestial_phenomenon import CelestialPhenomenon


@dataclass
class World():
    map: Map
    month_stamp: MonthStamp
    avatar_manager: AvatarManager = field(default_factory=AvatarManager)
    # 全局事件管理器
    event_manager: EventManager = field(default_factory=EventManager)
    # 当前天地灵机（世界级buff/debuff）
    current_phenomenon: Optional["CelestialPhenomenon"] = None
    # 天地灵机开始年份（用于计算持续时间）
    phenomenon_start_year: int = 0

    def get_info(self, detailed: bool = False) -> dict:
        """
        返回世界信息（dict），其中包含地图信息（dict）。
        """
        map_info = self.map.get_info(detailed=detailed)
        return map_info

    def get_avatars_in_same_region(self, avatar: "Avatar"):
        return self.avatar_manager.get_avatars_in_same_region(avatar)

    def get_observable_avatars(self, avatar: "Avatar"):
        return self.avatar_manager.get_observable_avatars(avatar)