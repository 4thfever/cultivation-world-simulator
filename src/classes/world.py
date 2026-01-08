from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from src.classes.map import Map
from src.classes.calendar import Year, Month, MonthStamp
from src.classes.avatar_manager import AvatarManager
from src.classes.event_manager import EventManager
from src.classes.circulation import CirculationManager

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

    @property
    def static_info(self) -> dict:
        desc = {
            "简介": "这是一个诸多修士竞相修行的修仙世界。",
            "境界": "修仙的境界从弱到强：练气、筑基、金丹、元婴。每个境界分前期、中期、后期。境界间差距很大。",
            "寿元": "每个角色均有寿元，超过寿元后容易老死。提升境界和某些宝物、丹药能提高寿元。",
            "死亡": "HP降至0以下也会死亡。",
            "区域": "不同区域有不同效果，在适当的区域做适当的事情事半功倍。",
            "修炼": "修炼可以增加经验，直到到达突破前的瓶颈。突破是概率事件，突破后会进入下一个境界。",
            "灵根": "决定了你与天地灵气的亲和度。在与自身灵根属性匹配的区域（如火灵根在火属性洞府）修炼，效率最高。",
            "天地灵机": "世界每隔数年会有一次天象变动（如灵气潮汐），影响角色能力。",
            "灵石": "修仙界的通用货币。可用于购买法宝丹药，通过采集、交易或掠夺获取。",
            "宗门": "修士的庇护所。加入宗门可习得独门功法、获同门庇护；散修自由但资源匮乏。",
            "战斗": "弱肉强食。境界压制极大，高境界者对低境界者有绝对优势。若对方死亡，胜者可掠夺败者财物。",
            "动作": "你有一系列可以执行的动作。要注意动作的效果、限制条件、区域和时间。",
            "装备与丹药": "通过兵器、辅助装备、丹药等装备，可以获得额外的属性加成，获得或小或大的增益。拥有好的装备或者服用好的丹药，能获得很大好处。",
        }
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