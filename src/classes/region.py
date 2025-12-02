from dataclasses import dataclass, field
from typing import Union, TypeVar, Type, Optional
from enum import Enum
from abc import ABC, abstractmethod

from src.utils.df import game_configs, get_str, get_int, get_list_int
from src.utils.config import CONFIG
from src.classes.essence import EssenceType, Essence
from src.classes.animal import Animal, animals_by_id
from src.classes.plant import Plant, plants_by_id
from src.classes.sect import sects_by_name


def get_tiles_from_shape(shape: 'Shape', north_west_cor: str, south_east_cor: str) -> list[tuple[int, int]]:
    """
    根据形状和两个角点坐标，计算出对应的所有坐标点
    """
    if not north_west_cor or not south_east_cor:
        return []
        
    nw_coords = tuple(map(int, north_west_cor.split(',')))
    se_coords = tuple(map(int, south_east_cor.split(',')))
    
    min_x, min_y = nw_coords
    max_x, max_y = se_coords
    
    coordinates = []
    
    if shape == Shape.SQUARE or shape == Shape.RECTANGLE:
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                coordinates.append((x, y))
                
    elif shape == Shape.MEANDERING:
        distance_x = max_x - min_x
        distance_y = max_y - min_y
        total_distance = max(distance_x, distance_y)
        
        if total_distance < 10: width = 1
        elif total_distance < 30: width = 2
        else: width = 3
        
        path_points = []
        if distance_x >= distance_y:
            for x in range(min_x, max_x + 1):
                progress = (x - min_x) / max(distance_x, 1)
                base_y = min_y + int(progress * distance_y)
                import math
                wave_amplitude = min(3, distance_y // 4) if distance_y > 0 else 0
                wave_y = int(wave_amplitude * math.sin(progress * math.pi * 2))
                y = max(min_y, min(max_y, base_y + wave_y))
                path_points.append((x, y))
        else:
            for y in range(min_y, max_y + 1):
                progress = (y - min_y) / max(distance_y, 1)
                base_x = min_x + int(progress * distance_x)
                import math
                wave_amplitude = min(3, distance_x // 4) if distance_x > 0 else 0
                wave_x = int(wave_amplitude * math.sin(progress * math.pi * 2))
                x = max(min_x, min(max_x, base_x + wave_x))
                path_points.append((x, y))
        
        for px, py in path_points:
            for dx in range(-width//2, width//2 + 1):
                for dy in range(-width//2, width//2 + 1):
                    nx, ny = px + dx, py + dy
                    if min_x <= nx <= max_x and min_y <= ny <= max_y:
                        coordinates.append((nx, ny))
    
    return sorted(list(set(coordinates)))


@dataclass
class Region(ABC):
    """
    区域抽象基类
    """
    id: int
    name: str
    desc: str
    
    # 可选/默认值，因为现在主要通过外部传入 cors 初始化
    shape: 'Shape' = field(default=None) 
    north_west_cor: str = ""
    south_east_cor: str = ""
    
    # 核心坐标数据
    cors: list[tuple[int, int]] = field(default_factory=list)
    
    # 计算字段
    center_loc: tuple[int, int] = field(init=False)
    area: int = field(init=False)

    def __post_init__(self):
        """初始化计算字段"""
        if self.shape is None:
            self.shape = Shape.SQUARE # 默认值

        # 如果 cors 为空且提供了旧版坐标字符串，尝试计算 (兼容性)
        if not self.cors and self.north_west_cor and self.south_east_cor:
             self.cors = get_tiles_from_shape(self.shape, self.north_west_cor, self.south_east_cor)
        
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
            if self.north_west_cor and self.south_east_cor:
                nw = list(map(int, self.north_west_cor.split(',')))
                se = list(map(int, self.south_east_cor.split(',')))
                self.center_loc = ((nw[0]+se[0])//2, (nw[1]+se[1])//2)
            else:
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

    def get_hover_info(self) -> list[str]:
        return [
            f"区域: {self.name}",
            f"描述: {self.desc}",
        ]

    def get_info(self) -> str:
        return self.name

    def get_detailed_info(self) -> str:
        return f"{self.name} - {self.desc}"

    def get_structured_info(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "desc": self.desc,
            "type": self.get_region_type(),
            "type_name": "区域" 
        }


class Shape(Enum):
    SQUARE = "square"
    RECTANGLE = "rectangle"
    MEANDERING = "meandering"

    @classmethod
    def from_str(cls, shape_str: str) -> 'Shape':
        if not shape_str: return cls.SQUARE
        for shape in cls:
            if shape.value == shape_str:
                return shape
        return cls.SQUARE


@dataclass
class NormalRegion(Region):
    """普通区域"""
    animal_ids: list[int] = field(default_factory=list)
    plant_ids: list[int] = field(default_factory=list)
    
    animals: list[Animal] = field(init=False, default_factory=list)
    plants: list[Plant] = field(init=False, default_factory=list)
    
    def __post_init__(self):
        super().__post_init__()
        for animal_id in self.animal_ids:
            if animal_id in animals_by_id:
                self.animals.append(animals_by_id[animal_id])
        for plant_id in self.plant_ids:
            if plant_id in plants_by_id:
                self.plants.append(plants_by_id[plant_id])
    
    def get_region_type(self) -> str:
        return "normal"
    
    def get_species_info(self) -> str:
        info_parts = []
        if self.animals:
            info_parts.extend([a.get_info() for a in self.animals])
        if self.plants:
            info_parts.extend([p.get_info() for p in self.plants])
        return "; ".join(info_parts) if info_parts else "暂无特色物种"

    def _get_species_brief(self) -> str:
        briefs: list[str] = []
        if self.animals:
            briefs.extend([f"{a.name}（{a.realm.value}）" for a in self.animals])
        if self.plants:
            briefs.extend([f"{p.name}（{p.realm.value}）" for p in self.plants])
        return "、".join(briefs)

    def __str__(self) -> str:
        species_info = self.get_species_info()
        return f"普通区域：{self.name} - {self.desc} | 物种分布：{species_info}"

    def get_info(self) -> str:
        brief = self._get_species_brief()
        return f"{self.name}（{brief}）" if brief else self.name

    def get_detailed_info(self) -> str:
        brief = self._get_species_brief()
        name_with_brief = f"{self.name}（{brief}）" if brief else self.name
        species_info = self.get_species_info()
        if not species_info or species_info == "暂无特色物种":
            return f"{name_with_brief} - {self.desc}"
        return f"{name_with_brief} - {self.desc} | 物种分布：{species_info}"

    def get_hover_info(self) -> list[str]:
        lines = super().get_hover_info()
        species_info = self.get_species_info()
        if species_info and species_info != "暂无特色物种":
            lines.append("物种分布:")
            for species in species_info.split("; "):
                lines.append(f"  {species}")
        else:
            lines.append("物种分布: 暂无特色物种")
        return lines

    @property
    def is_huntable(self) -> bool:
        return len(self.animals) > 0

    @property
    def is_harvestable(self) -> bool:
        return len(self.plants) > 0

    def get_structured_info(self) -> dict:
        info = super().get_structured_info()
        info["type_name"] = "普通区域"
        info["animals"] = [a.get_structured_info() for a in self.animals]
        info["plants"] = [p.get_structured_info() for p in self.plants]
        return info


@dataclass
class CultivateRegion(Region):
    """修炼区域"""
    essence_type: EssenceType = EssenceType.GOLD # 默认值避免 dataclass 继承错误
    essence_density: int = 0
    essence: Essence = field(init=False)

    def __post_init__(self):
        super().__post_init__()
        essence_density_dict = {essence_type: 0 for essence_type in EssenceType}
        essence_density_dict[self.essence_type] = self.essence_density
        self.essence = Essence(essence_density_dict)

    def get_region_type(self) -> str:
        return "cultivate"

    def __str__(self) -> str:
        return f"修炼区域：{self.name}（{self.essence_type}行灵气：{self.essence_density}）- {self.desc}"

    def get_info(self) -> str:
        return f"{self.name}（{self.essence_type}行灵气：{self.essence_density}）"

    def get_detailed_info(self) -> str:
        return f"{self.name}（{self.essence_type}行灵气：{self.essence_density}）- {self.desc}"

    def get_hover_info(self) -> list[str]:
        lines = super().get_hover_info()
        stars = "★" * self.essence_density + "☆" * (10 - self.essence_density)
        lines.append(f"主要灵气: {self.essence_type} {stars}")
        return lines

    def get_structured_info(self) -> dict:
        info = super().get_structured_info()
        info["type_name"] = "修炼区域"
        info["essence"] = {
            "type": str(self.essence_type),
            "density": self.essence_density
        }
        return info


@dataclass
class CityRegion(Region):
    """城市区域"""
    def get_region_type(self) -> str:
        return "city"

    def __str__(self) -> str:
        return f"城市区域：{self.name} - {self.desc}"

    def get_info(self) -> str:
        return self.name

    def get_detailed_info(self) -> str:
        return f"{self.name} - {self.desc}"

    def get_structured_info(self) -> dict:
        info = super().get_structured_info()
        info["type_name"] = "城市区域"
        return info


def _normalize_region_name(name: str) -> str:
    s = str(name).strip()
    brackets = [("(", ")"), ("（", "）"), ("[", "]"), ("【", "】"), ("「", "」"), ("『", "』"), ("<", ">"), ("《", "》")]
    for left, right in brackets:
        while True:
            start = s.find(left)
            end = s.rfind(right)
            if start != -1 and end != -1 and end > start:
                s = (s[:start] + s[end + 1:]).strip()
            else:
                break
    return s


def resolve_region(world, region: Union[Region, str]) -> Region:
    """
    解析字符串或 Region 为当前 world.map 中的 Region 实例
    """
    from typing import Dict

    if isinstance(region, str):
        region_name = region
        by_name: Dict[str, Region] = getattr(world.map, "region_names", {})

        # 1) 精确匹配
        r = by_name.get(region_name)
        if r is not None:
            return r

        # 2) 归一化后再精确匹配
        normalized = _normalize_region_name(region_name)
        if normalized and normalized != region_name:
            r2 = by_name.get(normalized)
            if r2 is not None:
                return r2

        # 3) 唯一包含匹配
        candidates = [name for name in by_name.keys() if name and (name in region_name or (normalized and name in normalized))]
        if len(candidates) == 1:
            return by_name[candidates[0]]

        # 4) 兜底：若传入为宗门名，则解析为其总部区域
        sect = sects_by_name.get(region_name) or (sects_by_name.get(normalized) if normalized and normalized != region_name else None)
        if sect is not None:
            sect_regions = getattr(world.map, "sect_regions", {}) or {}
            matched = [r for r in sect_regions.values() if getattr(r, "sect_name", None) == sect.name]
            if len(matched) == 1:
                return matched[0]

        if candidates:
            sample = ", ".join(candidates[:5])
            raise ValueError(f"区域名不唯一: {region_name}，候选: {sample}")
        raise ValueError(f"未知区域名: {region_name}")

    if isinstance(region, Region):
        by_id = getattr(world.map, "regions", None)
        if isinstance(by_id, dict) and region.id in by_id:
            return by_id[region.id]
        return region

    raise TypeError(f"不支持的region类型: {type(region).__name__}")
