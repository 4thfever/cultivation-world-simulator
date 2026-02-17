from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from src.classes.environment.map import Map
from src.systems.time import Year, Month, MonthStamp
from src.sim.managers.avatar_manager import AvatarManager
from src.sim.managers.mortal_manager import MortalManager
from src.sim.managers.event_manager import EventManager
from src.classes.circulation import CirculationManager
from src.classes.gathering.gathering import GatheringManager
from src.classes.history import History
from src.utils.df import game_configs
from src.classes.language import language_manager, LanguageType
from src.i18n import t

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar
    from src.classes.celestial_phenomenon import CelestialPhenomenon


@dataclass
class World():
    map: Map
    month_stamp: MonthStamp
    avatar_manager: AvatarManager = field(default_factory=AvatarManager)
    # 凡人管理器
    mortal_manager: MortalManager = field(default_factory=MortalManager)
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
    # 世界开始年份
    start_year: int = 0
    OCCUPY_CANDIDATES_KEY: str = "Occupy Candidates"

    @staticmethod
    def _describe_major_realm_gap(gap: int) -> str:
        if gap > 0:
            realm_unit = "major realm" if gap == 1 else "major realms"
            return f"owner higher by {gap} {realm_unit}"
        if gap < 0:
            up = -gap
            realm_unit = "major realm" if up == 1 else "major realms"
            return f"you higher by {up} {realm_unit}"
        return "same major realm"

    def _build_occupy_candidates_for_avatar(self, avatar: "Avatar") -> list[dict]:
        from src.classes.environment.region import CultivateRegion
        from src.systems.cultivation import REALM_RANK

        avatar_realm = avatar.cultivation_progress.realm
        avatar_realm_rank = REALM_RANK.get(avatar_realm, 0)
        avatar_realm_text = str(avatar_realm)
        candidates: list[dict] = []

        for region in self.map.regions.values():
            if not isinstance(region, CultivateRegion):
                continue

            host = region.host_avatar
            if host is None:
                candidates.append(
                    {
                        "region_name": region.name,
                        "owner_name": "None",
                        "your_realm": avatar_realm_text,
                        "owner_realm": "None",
                        "major_realm_gap": None,
                        "major_realm_gap_desc": "no owner",
                        "risk_reminder": "If owner rejects, battle likely; losing may cause severe injury/death and major losses.",
                    }
                )
                continue

            owner_realm = host.cultivation_progress.realm
            owner_rank = REALM_RANK.get(owner_realm, 0)
            major_gap = owner_rank - avatar_realm_rank
            candidates.append(
                {
                    "region_name": region.name,
                    "owner_name": host.name,
                    "your_realm": avatar_realm_text,
                    "owner_realm": str(owner_realm),
                    "major_realm_gap": major_gap,
                    "major_realm_gap_desc": self._describe_major_realm_gap(major_gap),
                    "risk_reminder": "If owner rejects, battle likely; losing may cause severe injury/death and major losses.",
                }
            )

        return candidates

    def get_info(self, detailed: bool = False, avatar: Optional["Avatar"] = None) -> dict:
        """
        返回世界信息（dict），其中包含地图信息（dict）。
        如果指定了 avatar，将传给 map.get_info 用于过滤区域和计算距离。
        """
        static_info = self.static_info
        map_info = self.map.get_info(detailed=detailed, avatar=avatar)
        world_info = {**map_info, **static_info}

        if self.current_phenomenon:
            # 使用翻译 Key
            key = t("Current World Phenomenon")
            # 格式化内容，注意这里我们假设 name 和 desc 已经是当前语言的（它们是对象属性，加载时确定）
            # 但如果需要在 Prompt 中有特定的格式（如中文用【】，英文不用），也可以引入 key
            # 为了简单起见，我们把格式也放入翻译
            # "phenomenon_format": "【{name}】{desc}" (ZH) vs "{name}: {desc}" (EN)
            value = t("phenomenon_format", name=self.current_phenomenon.name, desc=self.current_phenomenon.desc)
            world_info[key] = value

        if avatar is not None:
            world_info[self.OCCUPY_CANDIDATES_KEY] = self._build_occupy_candidates_for_avatar(avatar)

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
            t_val = row.get("title")
            d_val = row.get("desc")
            if t_val and d_val:
                desc[t_val] = d_val
        
        if self.history.text:
            key = t("History")
            desc[key] = self.history.text
        return desc

    @classmethod
    def create_with_db(
        cls,
        map: "Map",
        month_stamp: MonthStamp,
        events_db_path: Path,
        start_year: int = 0,
    ) -> "World":
        """
        工厂方法：创建使用 SQLite 持久化事件的 World 实例。

        Args:
            map: 地图对象。
            month_stamp: 时间戳。
            events_db_path: 事件数据库文件路径。
            start_year: 世界开始年份。

        Returns:
            配置好的 World 实例。
        """
        event_manager = EventManager.create_with_db(events_db_path)
        return cls(
            map=map,
            month_stamp=month_stamp,
            event_manager=event_manager,
            start_year=start_year,
        )
