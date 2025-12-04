from dataclasses import dataclass, field
from typing import Optional

from src.utils.df import game_configs, get_str, get_int, get_list_int
from src.utils.config import CONFIG
from src.classes.item import Item, items_by_id
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
    item_ids: list[int] = field(default_factory=list)  # 该植物对应的物品IDs
    
    # 这些字段将在__post_init__中设置
    items: list[Item] = field(init=False, default_factory=list)  # 该植物对应的物品实例
    
    def __post_init__(self):
        """初始化物品实例"""
        for item_id in self.item_ids:
            if item_id in items_by_id:
                self.items.append(items_by_id[item_id])

    def __hash__(self) -> int:
        return hash(self.id)

    def __str__(self) -> str:
        return self.name
    
    def get_info(self) -> str:
        """
        获取植物的详细信息，包括名字、描述、境界和材料
        """
        info_parts = [f"【{self.name}】({self.realm.value})", self.desc]
        
        if self.items:
            item_names = [item.name for item in self.items]
            info_parts.append(f"可获得材料：{', '.join(item_names)}")
        
        return " - ".join(info_parts)

    def get_structured_info(self) -> dict:
        items_info = [item.get_structured_info() for item in self.items]
        return {
            "id": str(self.id),
            "name": self.name,
            "desc": self.desc,
            "grade": self.realm.value,
            "drops": items_info,
            "type": "plant"
        }

def _load_plants() -> tuple[dict[int, Plant], dict[str, Plant]]:
    """从配表加载plant数据"""
    plants_by_id: dict[int, Plant] = {}
    plants_by_name: dict[str, Plant] = {}
    
    plant_df = game_configs["plant"]
    for row in plant_df:
        item_ids_list = get_list_int(row, "item_ids")
            
        plant = Plant(
            id=get_int(row, "id"),
            name=get_str(row, "name"),
            desc=get_str(row, "desc"),
            realm=Realm.from_id(get_int(row, "stage_id")),
            item_ids=item_ids_list
        )
        plants_by_id[plant.id] = plant
        plants_by_name[plant.name] = plant
    
    return plants_by_id, plants_by_name

# 从配表加载plant数据
plants_by_id, plants_by_name = _load_plants()
