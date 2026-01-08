from dataclasses import dataclass

from src.classes.item import Item
from src.utils.df import game_configs, get_str, get_int
from src.classes.cultivation import Realm

@dataclass
class Material(Item):
    """
    材料
    """
    id: int
    name: str
    desc: str
    realm: Realm

    def instantiate(self) -> "Material":
        return self

    def __hash__(self) -> int:
        return hash(self.id)

    def __str__(self) -> str:
        return self.name

    def get_info(self) -> str:
        return f"{self.name} -（{self.realm.value}）"

    def get_detailed_info(self) -> str:
        return f"{self.name} - {self.desc}（{self.realm.value}）"

    def get_structured_info(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "desc": self.desc,
            "grade": self.realm.value,
            "effect_desc": "" # 材料暂时没有效果字段
        }

def _load_materials() -> tuple[dict[int, Material], dict[str, Material]]:
    """从配表加载 material 数据"""
    materials_by_id: dict[int, Material] = {}
    materials_by_name: dict[str, Material] = {}
    
    if "material" in game_configs:
        material_df = game_configs["material"]
        for row in material_df:
            material = Material(
                id=get_int(row, "id"),
                name=get_str(row, "name"),
                desc=get_str(row, "desc"),
                realm=Realm.from_id(get_int(row, "stage_id"))
            )
            materials_by_id[material.id] = material
            materials_by_name[material.name] = material
    
    return materials_by_id, materials_by_name

# 从配表加载 material 数据
materials_by_id, materials_by_name = _load_materials()
