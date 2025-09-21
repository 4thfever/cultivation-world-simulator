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

    def get_info(self) -> str:
        map_intro = "世界上的区域为："
        map_info = self.map.get_info()
        info = f"{map_intro}\n{map_info}"
        return info

    def get_avatars_in_same_region(self, avatar: "Avatar"):
        return self.avatar_manager.get_avatars_in_same_region(avatar)