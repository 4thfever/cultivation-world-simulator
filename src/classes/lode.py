from dataclasses import dataclass, field
from typing import Optional

from src.utils.df import game_configs, get_str, get_int, get_list_int
from src.classes.material import Material, materials_by_id
from src.classes.cultivation import Realm

@dataclass
class Lode:
    """
    矿脉
    """
    id: int
    name: str
    desc: str
    realm: Realm
    material_ids: list[int] = field(default_factory=list)  # 该矿脉对应的物品IDs
    
    # 这些字段将在__post_init__中设置
    materials: list[Material] = field(init=False, default_factory=list)  # 该矿脉对应的物品实例
    
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
        获取矿脉的详细信息
        """
        info_parts = [f"【{self.name}】({self.realm.value})", self.desc]
        
        if self.materials:
            material_names = [material.name for material in self.materials]
            info_parts.append(f"可获得矿石：{', '.join(material_names)}")
        
        return " - ".join(info_parts)

    def get_structured_info(self) -> dict:
        materials_info = [material.get_structured_info() for material in self.materials]
        return {
            "id": str(self.id),
            "name": self.name,
            "desc": self.desc,
            "grade": self.realm.value,
            "drops": materials_info,
            "type": "lode"
        }

def _load_lodes() -> tuple[dict[int, Lode], dict[str, Lode]]:
    """从配表加载lode数据"""
    lodes_by_id: dict[int, Lode] = {}
    lodes_by_name: dict[str, Lode] = {}
    
    # 检查配置是否存在，避免初始化错误
    if "lode" not in game_configs:
        return {}, {}
    
    lode_df = game_configs["lode"]
    for row in lode_df:
        material_ids_list = get_list_int(row, "material_ids")
            
        lode = Lode(
            id=get_int(row, "id"),
            name=get_str(row, "name"),
            desc=get_str(row, "desc"),
            realm=Realm.from_id(get_int(row, "stage_id")),
            material_ids=material_ids_list
        )
        lodes_by_id[lode.id] = lode
        lodes_by_name[lode.name] = lode
    
    return lodes_by_id, lodes_by_name

# 从配表加载lode数据
lodes_by_id, lodes_by_name = _load_lodes()

# 导出所有属于矿石的物品ID，供铸造逻辑判断
ORE_MATERIAL_IDS = {material_id for lode in lodes_by_id.values() for material_id in lode.material_ids}
