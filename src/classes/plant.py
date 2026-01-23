from dataclasses import dataclass, field
from typing import Optional

from src.utils.df import game_configs, get_str, get_int, get_list_int
from src.utils.config import CONFIG
from src.classes.material import Material, materials_by_id
from src.classes.cultivation import Realm

@dataclass
class Plant:
    """
    植物
    """
    id: int
    name: str
    desc: str
    realm: Realm
    material_ids: list[int] = field(default_factory=list)  # 该植物对应的物品IDs
    
    # 这些字段将在__post_init__中设置
    materials: list[Material] = field(init=False, default_factory=list)  # 该植物对应的物品实例
    
    def __post_init__(self):
        """初始化物品实例"""
        for material_id in self.material_ids:
            if material_id in materials_by_id:
                self.materials.append(materials_by_id[material_id])

    def __hash__(self) -> int:
        return hash(self.id)

    def __str__(self) -> str:
        return self.name
    
    def get_info(self) -> str:
        """
        获取植物的详细信息，包括名字、描述、境界和材料
        """
        from src.i18n import t
        # 使用格式化字符串 msgid
        base_info = t("[{name}] ({realm})", name=t(self.name), realm=str(self.realm))
        info_parts = [base_info, t(self.desc)]
        
        if self.materials:
            material_names = [t(material.name) for material in self.materials]
            materials_str = t("comma_separator").join(material_names)
            info_parts.append(t("Drops: {materials}", materials=materials_str))
        
        return " - ".join(info_parts)

    def get_structured_info(self) -> dict:
        materials_info = [material.get_structured_info() for material in self.materials]
        return {
            "id": str(self.id),
            "name": self.name,
            "desc": self.desc,
            "grade": self.realm.value,
            "drops": materials_info,
            "type": "plant"
        }

def _load_plants() -> tuple[dict[int, Plant], dict[str, Plant]]:
    """从配表加载plant数据"""
    plants_by_id: dict[int, Plant] = {}
    plants_by_name: dict[str, Plant] = {}
    
    plant_df = game_configs["plant"]
    for row in plant_df:
        material_ids_list = get_list_int(row, "material_ids")
            
        plant = Plant(
            id=get_int(row, "id"),
            name=get_str(row, "name"),
            desc=get_str(row, "desc"),
            realm=Realm.from_id(get_int(row, "stage_id")),
            material_ids=material_ids_list
        )
        plants_by_id[plant.id] = plant
        plants_by_name[plant.name] = plant
    
    return plants_by_id, plants_by_name

# 从配表加载plant数据
plants_by_id, plants_by_name = _load_plants()
