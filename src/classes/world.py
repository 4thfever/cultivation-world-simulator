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

    def get_info(self, detailed: bool = False, avatar: Optional["Avatar"] = None) -> dict:
        """
        返回世界信息（dict），其中包含地图信息（dict）。
        如果指定了 avatar，将传给 map.get_info 用于过滤区域和计算距离。
        """
        static_info = self.static_info
        map_info = self.map.get_info(detailed=detailed, avatar=avatar)
        world_info = {**map_info, **static_info}

        if self.current_phenomenon:
            world_info["天地灵机"] = f"【{self.current_phenomenon.name}】{self.current_phenomenon.desc}"

        return world_info

    def get_avatars_in_same_region(self, avatar: "Avatar"):
        return self.avatar_manager.get_avatars_in_same_region(avatar)

    def get_observable_avatars(self, avatar: "Avatar"):
        return self.avatar_manager.get_observable_avatars(avatar)

    @property
    def static_info(self) -> dict:
        return {"世界描述": "这是一个修仙世界，修仙的境界有：练气、筑基、金丹、元婴。"}