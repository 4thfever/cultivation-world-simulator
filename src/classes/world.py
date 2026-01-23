from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from src.classes.map import Map
from src.classes.calendar import Year, Month, MonthStamp
from src.classes.avatar_manager import AvatarManager
from src.classes.event_manager import EventManager
from src.classes.circulation import CirculationManager
from src.classes.gathering.gathering import GatheringManager
from src.classes.history import History
from src.utils.df import game_configs
from src.classes.language import language_manager, LanguageType

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
    # 出世物品流通管理器
    circulation: CirculationManager = field(default_factory=CirculationManager)
    # Gathering 管理器
    gathering_manager: GatheringManager = field(default_factory=GatheringManager)
    # 世界历史
    history: "History" = field(default_factory=lambda: History())

    def get_info(self, detailed: bool = False, avatar: Optional["Avatar"] = None) -> dict:
        """
        返回世界信息（dict），其中包含地图信息（dict）。
        如果指定了 avatar，将传给 map.get_info 用于过滤区域和计算距离。
        """
        static_info = self.static_info
        map_info = self.map.get_info(detailed=detailed, avatar=avatar)
        world_info = {**map_info, **static_info}

        if self.current_phenomenon:
            world_info["当前天地灵机"] = f"【{self.current_phenomenon.name}】{self.current_phenomenon.desc}"

        return world_info

    def get_avatars_in_same_region(self, avatar: "Avatar"):
        return self.avatar_manager.get_avatars_in_same_region(avatar)

    def get_observable_avatars(self, avatar: "Avatar"):
        return self.avatar_manager.get_observable_avatars(avatar)

    def set_history(self, history_text: str):
        """设置世界历史文本"""
        self.history.text = history_text
        
    def record_modification(self, category: str, id_str: str, changes: dict):
        """
        记录历史修改差分
        
        Args:
            category: 修改类别 (sects, regions, techniques, weapons, auxiliaries)
            id_str: 对象 ID 字符串
            changes: 修改的属性字典
        """
        if category not in self.history.modifications:
            self.history.modifications[category] = {}
            
        if id_str not in self.history.modifications[category]:
            self.history.modifications[category][id_str] = {}
            
        # 累加修改（后来的覆盖前面的）
        self.history.modifications[category][id_str].update(changes)

    @property
    def static_info(self) -> dict:
        info_list = game_configs.get("world_info", [])
        desc = {}
        for row in info_list:
            t = row.get("title")
            d = row.get("desc")
            if t and d:
                desc[t] = d
        
        if self.history.text:
            key = "History" if language_manager.current == LanguageType.EN_US else "历史"
            desc[key] = self.history.text
        return desc

    @classmethod
    def create_with_db(
        cls,
        map: "Map",
        month_stamp: MonthStamp,
        events_db_path: Path,
    ) -> "World":
        """
        工厂方法：创建使用 SQLite 持久化事件的 World 实例。

        Args:
            map: 地图对象。
            month_stamp: 时间戳。
            events_db_path: 事件数据库文件路径。

        Returns:
            配置好的 World 实例。
        """
        event_manager = EventManager.create_with_db(events_db_path)
        return cls(
            map=map,
            month_stamp=month_stamp,
            event_manager=event_manager,
        )