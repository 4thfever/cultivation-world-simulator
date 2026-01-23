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
        from src.i18n import t
        return t("{name} ({realm})", name=t(self.name), realm=str(self.realm))

    def get_detailed_info(self) -> str:
        from src.i18n import t
        return t("{name}: {desc} ({realm})", name=t(self.name), desc=t(self.desc), realm=str(self.realm))

    def get_structured_info(self) -> dict:
        from src.classes.language import language_manager
        grade_display = self.realm.value
        if str(language_manager) == "en-US":
             # 英文状态下，使用翻译后的境界名称 (例如 "Qi Refinement" 而不是 "QI_REFINEMENT")
            grade_display = str(self.realm)

        return {
            "id": str(self.id),
            "name": self.name,
            "desc": self.desc,
            "grade": grade_display,
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

def reload():
    """重新加载数据"""
    new_id, new_name = _load_materials()
    materials_by_id.clear()
    materials_by_id.update(new_id)
    materials_by_name.clear()
    materials_by_name.update(new_name)
