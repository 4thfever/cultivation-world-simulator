from dataclasses import dataclass, field
from typing import Union, TypeVar, Type, Optional, TYPE_CHECKING
from enum import Enum
from abc import ABC, abstractmethod

from src.utils.df import game_configs, get_str, get_int, get_list_int
from src.utils.config import CONFIG
from src.utils.distance import chebyshev_distance
from src.classes.essence import EssenceType, Essence
from src.classes.animal import Animal, animals_by_id
from src.classes.environment.plant import Plant, plants_by_id
from src.classes.environment.lode import Lode, lodes_by_id
from src.classes.core.sect import sects_by_name
from src.classes.items.store import StoreMixin
from src.i18n import t

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar



@dataclass
class Region(ABC):
    """
    区域抽象基类
    """
    id: int
    name: str
    desc: str
    
    # 核心坐标数据，由 load_map.py 注入
    cors: list[tuple[int, int]] = field(default_factory=list)
    
    # 计算字段
    center_loc: tuple[int, int] = field(init=False)
    area: int = field(init=False)

    def __post_init__(self):
        """初始化计算字段"""
        # 基于坐标点计算面积
        self.area = len(self.cors)
        
        # 计算中心位置
        if self.cors:
            avg_x = sum(coord[0] for coord in self.cors) // len(self.cors)
            avg_y = sum(coord[1] for coord in self.cors) // len(self.cors)
            candidate = (avg_x, avg_y)
            if candidate in self.cors:
                self.center_loc = candidate
            else:
                def _dist2(p: tuple[int, int]) -> int:
                    return (p[0] - avg_x) ** 2 + (p[1] - avg_y) ** 2
                self.center_loc = min(self.cors, key=_dist2)
        else:
            # Fallback
            self.center_loc = (0, 0)

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Region):
            return False
        return self.id == other.id

    @abstractmethod
    def get_region_type(self) -> str:
        pass

    @abstractmethod
    def _get_desc(self) -> str:
        """
        返回紧跟在名字后的描述，通常包含括号，例如 '（金行灵气：5）'
        注意，不需要包含self.desc
        """
        pass

    def _get_distance_desc(self, current_loc: tuple[int, int] = None, step_len: int = 1) -> str:
        if current_loc is None:
            return ""
        dist = chebyshev_distance(current_loc, self.center_loc)
        # 估算到达时间：距离 / 步长 (向上取整)
        months = (dist + step_len - 1) // step_len
        # 避免显示 0 个月
        months = max(1, months)
        return t(" (Distance: {months} months)", months=months)

    def get_info(self, current_loc: tuple[int, int] = None, step_len: int = 1) -> str:
        return f"{self.name}{self._get_distance_desc(current_loc, step_len)}"

    def get_detailed_info(self, current_loc: tuple[int, int] = None, step_len: int = 1) -> str:
        return f"{self.name}{self._get_desc()} - {self.desc}{self._get_distance_desc(current_loc, step_len)}"

    def get_structured_info(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "desc": self.desc,
            "type": self.get_region_type(),
            "type_name": t("Region")
        }


@dataclass(eq=False)
class NormalRegion(Region):
    """普通区域"""
    animal_ids: list[int] = field(default_factory=list)
    plant_ids: list[int] = field(default_factory=list)
    lode_ids: list[int] = field(default_factory=list)
    
    animals: list[Animal] = field(init=False, default_factory=list)
    plants: list[Plant] = field(init=False, default_factory=list)
    lodes: list[Lode] = field(init=False, default_factory=list)
    
    def __post_init__(self):
        super().__post_init__()
        for animal_id in self.animal_ids:
            if animal_id in animals_by_id:
                self.animals.append(animals_by_id[animal_id])
        for plant_id in self.plant_ids:
            if plant_id in plants_by_id:
                self.plants.append(plants_by_id[plant_id])
        for lode_id in self.lode_ids:
            if lode_id in lodes_by_id:
                self.lodes.append(lodes_by_id[lode_id])
    
    def get_region_type(self) -> str:
        return "normal"
    
    def get_species_info(self) -> str:
        info_parts = []
        if self.animals:
            info_parts.extend([a.get_info() for a in self.animals])
        if self.plants:
            info_parts.extend([p.get_info() for p in self.plants])
        if self.lodes:
            info_parts.extend([l.get_info() for l in self.lodes])
        return "; ".join(info_parts) if info_parts else t("No special resources")

    def _get_desc(self) -> str:
        species_info = self.get_species_info()
        return t(" (Resource Distribution: {species_info})", species_info=species_info)

    def __str__(self) -> str:
        species_info = self.get_species_info()
        return t("Normal Region: {name} - {desc} | Resource Distribution: {species_info}",
                 name=self.name, desc=self.desc, species_info=species_info)

    @property
    def is_huntable(self) -> bool:
        return len(self.animals) > 0

    @property
    def is_harvestable(self) -> bool:
        return len(self.plants) > 0

    @property
    def is_mineable(self) -> bool:
        return len(self.lodes) > 0

    def get_structured_info(self) -> dict:
        info = super().get_structured_info()
        info["type_name"] = t("Normal Region")
        
        # Assuming animals and plants are populated in __post_init__
        info["animals"] = [a.get_structured_info() for a in self.animals] if self.animals else []
        info["plants"] = [p.get_structured_info() for p in self.plants] if self.plants else []
        info["lodes"] = [l.get_structured_info() for l in self.lodes] if self.lodes else []
        
        return info


@dataclass(eq=False)
class CultivateRegion(Region):
    """修炼区域（洞府/遗迹）"""
    essence_type: EssenceType = EssenceType.GOLD # 默认值避免 dataclass 继承错误
    essence_density: int = 0
    sub_type: str = "cave"  # "cave" 或 "ruin"
    essence: Essence = field(init=False)
    
    # 洞府主人：默认为空（无主）
    host_avatar: Optional["Avatar"] = field(default=None, init=False)

    def __post_init__(self):
        super().__post_init__()
        essence_density_dict = {essence_type: 0 for essence_type in EssenceType}
        essence_density_dict[self.essence_type] = self.essence_density
        self.essence = Essence(essence_density_dict)

    def get_region_type(self) -> str:
        return "cultivate"

    def _get_owner_desc(self) -> str:
        if self.host_avatar:
             return t(" (Owner: {owner}, {realm})", owner=self.host_avatar.name, realm=str(self.host_avatar.cultivation_progress.realm))
        return ""

    def get_info(self, current_loc: tuple[int, int] = None, step_len: int = 1) -> str:
        return super().get_info(current_loc, step_len) + self._get_owner_desc()

    def get_detailed_info(self, current_loc: tuple[int, int] = None, step_len: int = 1) -> str:
        return super().get_detailed_info(current_loc, step_len) + self._get_owner_desc()

    def _get_desc(self) -> str:
        return t(" ({essence_type} Essence: {essence_density})", essence_type=self.essence_type, essence_density=self.essence_density)

    def __str__(self) -> str:
        return t("Cultivate Region: {name} ({essence_type} Essence: {essence_density}) - {desc}", 
                 name=self.name, essence_type=self.essence_type, essence_density=self.essence_density, desc=self.desc)

    def get_structured_info(self) -> dict:
        info = super().get_structured_info()
        info["type_name"] = t("Cave Dwelling") if self.sub_type == "cave" else t("Ruins")
        info["essence"] = {
            "type": str(self.essence_type),
            "density": self.essence_density
        }
        info["sub_type"] = self.sub_type
        
        if self.host_avatar:
            info["host"] = {
                "id": self.host_avatar.id,
                "name": self.host_avatar.name
            }
        else:
            info["host"] = None
            
        return info


@dataclass(eq=False)
class CityRegion(Region, StoreMixin):
    """城市区域"""
    sell_item_ids: list[int] = field(default_factory=list)
    prosperity: float = 50.0

    def __post_init__(self):
        super().__post_init__()
        self.init_store(self.sell_item_ids)

    def change_prosperity(self, delta: float) -> None:
        """安全修改繁荣度，限制在 0-100 之间"""
        self.prosperity = max(0.0, min(100.0, self.prosperity + delta))

    def get_region_type(self) -> str:
        return "city"

    def _get_desc(self) -> str:
        store_info = self.get_store_info()
        if store_info:
            return t(" ({store_info})", store_info=store_info)
        return ""

    def __str__(self) -> str:
        store_info = self.get_store_info()
        desc_part = t(" | {store_info}", store_info=store_info) if store_info else ""
        return t("City Region: {name} - {desc}{desc_part}", name=self.name, desc=self.desc, desc_part=desc_part)

    def get_structured_info(self) -> dict:
        info = super().get_structured_info()
        info["type_name"] = t("City Region")
        
        store_items_info = []
        if hasattr(self, 'store_items'):
            from src.classes.prices import prices
            for item in self.store_items:
                item_info = item.get_structured_info()
                # Inject price
                item_info["price"] = prices.get_buying_price(item, None)
                store_items_info.append(item_info)
        
        info["store_items"] = store_items_info
        info["prosperity"] = self.prosperity
        return info
