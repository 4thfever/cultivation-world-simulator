from dataclasses import dataclass, field
from typing import Union, TypeVar, Type, Optional
from enum import Enum
from abc import ABC, abstractmethod

from src.utils.df import game_configs
from src.utils.config import CONFIG
from src.classes.essence import EssenceType, Essence
from src.classes.animal import Animal, animals_by_id
from src.classes.plant import Plant, plants_by_id


def get_tiles_from_shape(shape: 'Shape', north_west_cor: str, south_east_cor: str) -> list[tuple[int, int]]:
    """
    根据形状和两个角点坐标，计算出对应的所有坐标点
    
    Args:
        shape: 区域形状
        north_west_cor: 西北角坐标，格式: "x,y"
        south_east_cor: 东南角坐标，格式: "x,y"
    
    Returns:
        所有坐标点的列表
    """
    nw_coords = tuple(map(int, north_west_cor.split(',')))
    se_coords = tuple(map(int, south_east_cor.split(',')))
    
    min_x, min_y = nw_coords
    max_x, max_y = se_coords
    
    coordinates = []
    
    if shape == Shape.SQUARE or shape == Shape.RECTANGLE:
        # 正方形和长方形：填充整个矩形区域
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                coordinates.append((x, y))
                
    elif shape == Shape.MEANDERING:
        # 蜿蜒形状（如河流）：创建一条从西北到东南的蜿蜒路径
        # 计算河流的宽度（根据距离动态调整）
        distance_x = max_x - min_x
        distance_y = max_y - min_y
        total_distance = max(distance_x, distance_y)
        
        # 河流宽度：距离越长，河流越宽
        if total_distance < 10:
            width = 1
        elif total_distance < 30:
            width = 2
        else:
            width = 3
        
        # 生成中心路径点
        path_points = []
        if distance_x >= distance_y:
            # 主要沿X轴方向流动
            for x in range(min_x, max_x + 1):
                # 计算对应的y坐标，添加一些蜿蜒效果
                progress = (x - min_x) / max(distance_x, 1)
                base_y = min_y + int(progress * distance_y)
                
                # 添加蜿蜒效果：使用简单的正弦波
                import math
                wave_amplitude = min(3, distance_y // 4) if distance_y > 0 else 0
                wave_y = int(wave_amplitude * math.sin(progress * math.pi * 2))
                y = max(min_y, min(max_y, base_y + wave_y))
                
                path_points.append((x, y))
        else:
            # 主要沿Y轴方向流动
            for y in range(min_y, max_y + 1):
                progress = (y - min_y) / max(distance_y, 1)
                base_x = min_x + int(progress * distance_x)
                
                # 添加蜿蜒效果
                import math
                wave_amplitude = min(3, distance_x // 4) if distance_x > 0 else 0
                wave_x = int(wave_amplitude * math.sin(progress * math.pi * 2))
                x = max(min_x, min(max_x, base_x + wave_x))
                
                path_points.append((x, y))
        
        # 为每个路径点添加宽度
        for px, py in path_points:
            for dx in range(-width//2, width//2 + 1):
                for dy in range(-width//2, width//2 + 1):
                    nx, ny = px + dx, py + dy
                    # 确保在边界内
                    if min_x <= nx <= max_x and min_y <= ny <= max_y:
                        coordinates.append((nx, ny))
    
    # 去重并排序
    return sorted(list(set(coordinates)))


@dataclass
class Region(ABC):
    """
    区域抽象基类
    理想中，一些地块应当在一起组成一个区域。
    比如，某山；某湖、江、海；某森林；某平原；某城市；
    一些分布，比如物产，按照Region来分布。
    再比如，灵气，应当也是按照region分布的。
    默认，一个region内部的属性，是共通的。
    同时，NPC应当对Region有观测和认知。
    """
    id: int
    name: str
    desc: str
    shape: 'Shape'
    north_west_cor: str  # 西北角坐标，格式: "x,y"
    south_east_cor: str  # 东南角坐标，格式: "x,y"
    
    # 这些字段将在__post_init__中设置
    cors: list[tuple[int, int]] = field(init=False)  # 存储所有坐标点
    center_loc: tuple[int, int] = field(init=False)
    area: int = field(init=False)

    def __post_init__(self):
        """初始化计算字段"""
        # 先计算所有坐标点
        self.cors = get_tiles_from_shape(self.shape, self.north_west_cor, self.south_east_cor)
        
        # 基于坐标点计算面积
        self.area = len(self.cors)
        
        # 计算中心位置：选取落在区域格点集合中的、最接近几何中心的点
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
            # 如果没有坐标点，使用边界框中心作为fallback
            nw_coords = tuple(map(int, self.north_west_cor.split(',')))
            se_coords = tuple(map(int, self.south_east_cor.split(',')))
            self.center_loc = (
                (nw_coords[0] + se_coords[0]) // 2,
                (nw_coords[1] + se_coords[1]) // 2
            )

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Region):
            return False
        return self.id == other.id

    @abstractmethod
    def get_region_type(self) -> str:
        """返回区域类型的字符串表示"""
        pass

    def get_hover_info(self) -> list[str]:
        """
        返回用于前端悬浮提示的多行信息（基础信息）。
        子类可扩展更多领域信息。
        """
        return [
            f"区域: {self.name}",
            f"描述: {self.desc}",
        ]

    def get_info(self) -> str:
        # 简版：仅返回名称
        return self.name

    def get_detailed_info(self) -> str:
        # 基类暂无更多结构化信息，详细版返回名称+描述
        return f"{self.name} - {self.desc}"


class Shape(Enum):
    """
    区域形状类型
    """
    SQUARE = "square"           # 正方形
    RECTANGLE = "rectangle"     # 长方形
    MEANDERING = "meandering"   # 蜿蜒的（如河流）

    @classmethod
    def from_str(cls, shape_str: str) -> 'Shape':
        """
        从字符串创建Shape实例
        
        Args:
            shape_str: 形状的字符串表示，如 "square", "rectangle", "meandering"
            
        Returns:
            对应的Shape枚举值
            
        Raises:
            ValueError: 如果字符串不匹配任何已知的形状类型
        """
        for shape in cls:
            if shape.value == shape_str:
                return shape
        raise ValueError(f"Unknown shape type: {shape_str}")


@dataclass
class NormalRegion(Region):
    """
    普通区域 - 平原、大河之类的，没有灵气或灵气很低
    包含该区域分布的动植物物种信息
    """
    animal_ids: list[int] = field(default_factory=list)  # 该区域分布的动物物种IDs
    plant_ids: list[int] = field(default_factory=list)   # 该区域分布的植物物种IDs
    
    # 这些字段将在__post_init__中设置
    animals: list[Animal] = field(init=False, default_factory=list)  # 该区域的动物实例
    plants: list[Plant] = field(init=False, default_factory=list)    # 该区域的植物实例
    
    def __post_init__(self):
        """初始化动植物实例"""
        # 先调用父类的__post_init__
        super().__post_init__()
        
        # 加载动物实例
        for animal_id in self.animal_ids:
            if animal_id in animals_by_id:
                self.animals.append(animals_by_id[animal_id])
        
        # 加载植物实例
        for plant_id in self.plant_ids:
            if plant_id in plants_by_id:
                self.plants.append(plants_by_id[plant_id])
    
    def get_region_type(self) -> str:
        return "normal"
    
    def get_species_info(self) -> str:
        """获取该区域动植物物种的描述信息"""
        info_parts = []
        if self.animals:
            animal_infos = [animal.get_info() for animal in self.animals]
            info_parts.extend(animal_infos)
        
        if self.plants:
            plant_infos = [plant.get_info() for plant in self.plants]
            info_parts.extend(plant_infos)
        
        return "; ".join(info_parts) if info_parts else "暂无特色物种"

    def __str__(self) -> str:
        species_info = self.get_species_info()
        return f"普通区域：{self.name} - {self.desc} | 物种分布：{species_info}"

    def get_info(self) -> str:
        return self.name

    def get_detailed_info(self) -> str:
        species_info = self.get_species_info()
        if not species_info or species_info == "暂无特色物种":
            return f"{self.name} - {self.desc}"
        return f"{self.name} - {self.desc} | 物种分布：{species_info}"

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
        # 如果该区域有动物，则可以狩猎
        return len(self.animals) > 0

    @property
    def is_harvestable(self) -> bool:
        # 如果该区域有植物，则可以采集
        return len(self.plants) > 0


@dataclass
class CultivateRegion(Region):
    """
    修炼区域 - 有灵气的区域，可以修炼
    """
    essence_type: EssenceType  # 最高灵气类型
    essence_density: int       # 最高灵气密度
    essence: Essence = field(init=False)  # 灵气对象，根据 essence_type 和 essence_density 生成

    def __post_init__(self):
        # 先调用父类的 __post_init__
        super().__post_init__()
        
        # 创建灵气对象，主要灵气类型设置为指定密度，其他类型设置为0
        essence_density_dict = {essence_type: 0 for essence_type in EssenceType}
        essence_density_dict[self.essence_type] = self.essence_density
        self.essence = Essence(essence_density_dict)

    def get_region_type(self) -> str:
        return "cultivate"

    def __str__(self) -> str:
        return f"修炼区域：{self.name}（{self.essence_type}行灵气：{self.essence_density}）- {self.desc}"

    def get_info(self) -> str:
        return self.name

    def get_detailed_info(self) -> str:
        return f"{self.name}（{self.essence_type}行灵气：{self.essence_density}）- {self.desc}"

    def get_hover_info(self) -> list[str]:
        lines = super().get_hover_info()
        stars = "★" * self.essence_density + "☆" * (10 - self.essence_density)
        lines.append(f"主要灵气: {self.essence_type} {stars}")
        return lines


@dataclass
class CityRegion(Region):
    """
    城市区域 - 不能修炼，但会有特殊操作
    """

    def get_region_type(self) -> str:
        return "city"

    def __str__(self) -> str:
        return f"城市区域：{self.name} - {self.desc}"

    def get_hover_info(self) -> list[str]:
        # 城市区域暂时仅展示基础信息
        return super().get_hover_info()

    def get_info(self) -> str:
        return self.name

    def get_detailed_info(self) -> str:
        return f"{self.name} - {self.desc}"


T = TypeVar('T', NormalRegion, CultivateRegion, CityRegion)

def _load_regions(region_type: Type[T], config_name: str) -> tuple[dict[int, T], dict[str, T]]:
    """
    通用的区域加载函数
    
    Args:
        region_type: 区域类型 (NormalRegion, CultivateRegion, CityRegion)
        config_name: 配置文件名 ("normal_region", "cultivate_region", "city_region")
    
    Returns:
        (按ID索引的字典, 按名称索引的字典)
    """
    regions_by_id: dict[int, T] = {}
    regions_by_name: dict[str, T] = {}
    
    region_df = game_configs[config_name]
    for _, row in region_df.iterrows():
        # 构建基础参数
        base_params = {
            "id": int(row["id"]),
            "name": str(row["name"]),
            "desc": str(row["desc"]),
            "shape": Shape.from_str(str(row["shape"])),
            "north_west_cor": str(row["north-west-cor"]),
            "south_east_cor": str(row["south-east-cor"])
        }
        
        # 如果是修炼区域，添加额外参数
        if region_type == CultivateRegion:
            base_params["essence_type"] = EssenceType.from_str(str(row["root_type"]))
            base_params["essence_density"] = int(row["root_density"])
        
        # 如果是普通区域，添加动植物ID参数
        elif region_type == NormalRegion:
            # 处理动物IDs
            animal_ids_list = []
            animal_ids = row.get("animal_ids")
            if animal_ids is not None and str(animal_ids).strip() and str(animal_ids) != 'nan':
                for animal_id_str in str(animal_ids).split(CONFIG.df.ids_separator):
                    animal_ids_list.append(int(float(animal_id_str.strip())))
            base_params["animal_ids"] = animal_ids_list
                
            # 处理植物IDs
            plant_ids_list = []
            plant_ids = row.get("plant_ids")
            if plant_ids is not None and str(plant_ids).strip() and str(plant_ids) != 'nan':
                for plant_id_str in str(plant_ids).split(CONFIG.df.ids_separator):
                    plant_ids_list.append(int(float(plant_id_str.strip())))
            base_params["plant_ids"] = plant_ids_list
        
        region = region_type(**base_params)
        regions_by_id[region.id] = region
        regions_by_name[region.name] = region
    
    return regions_by_id, regions_by_name


def load_all_regions() -> tuple[
    dict[int, Union[NormalRegion, CultivateRegion, CityRegion]], 
    dict[str, Union[NormalRegion, CultivateRegion, CityRegion]]
]:
    """
    统一加载所有类型的区域数据
    返回: (按ID索引的字典, 按名称索引的字典)
    """
    all_regions_by_id: dict[int, Union[NormalRegion, CultivateRegion, CityRegion]] = {}
    all_regions_by_name: dict[str, Union[NormalRegion, CultivateRegion, CityRegion]] = {}
    
    # 加载普通区域
    normal_by_id, normal_by_name = _load_regions(NormalRegion, "normal_region")
    all_regions_by_id.update(normal_by_id)
    all_regions_by_name.update(normal_by_name)
    
    # 加载修炼区域
    cultivate_by_id, cultivate_by_name = _load_regions(CultivateRegion, "cultivate_region")
    all_regions_by_id.update(cultivate_by_id)
    all_regions_by_name.update(cultivate_by_name)
    
    # 加载城市区域
    city_by_id, city_by_name = _load_regions(CityRegion, "city_region")
    all_regions_by_id.update(city_by_id)
    all_regions_by_name.update(city_by_name)
    
    return all_regions_by_id, all_regions_by_name


# 从配表加载所有区域数据
regions_by_id, regions_by_name = load_all_regions()

# 分别加载各类型区域数据
normal_regions_by_id, normal_regions_by_name = _load_regions(NormalRegion, "normal_region")
cultivate_regions_by_id, cultivate_regions_by_name = _load_regions(CultivateRegion, "cultivate_region")
city_regions_by_id, city_regions_by_name = _load_regions(CityRegion, "city_region")
