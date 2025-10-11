from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.classes.map import Map
from src.classes.calendar import Year, Month, MonthStamp
from src.classes.avatar_manager import AvatarManager

if TYPE_CHECKING:
    from src.classes.avatar import Avatar


@dataclass
class World():
    map: Map
    month_stamp: MonthStamp
    avatar_manager: AvatarManager = field(default_factory=AvatarManager)

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