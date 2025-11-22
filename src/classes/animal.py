from dataclasses import dataclass, field
from typing import Optional

from src.utils.df import game_configs, get_str, get_int, get_list_int
from src.utils.config import CONFIG
from src.classes.item import Item, items_by_id
from src.classes.cultivation import Realm

@dataclass
class Animal:
    """
    动物
    """
    id: int
    name: str
    desc: str
    realm: Realm
    item_ids: list[int] = field(default_factory=list)  # 该动物对应的物品IDs
    
    # 这些字段将在__post_init__中设置
    items: list[Item] = field(init=False, default_factory=list)  # 该动物对应的物品实例
    
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
        获取动物的详细信息，包括名字、描述、境界和材料
        """
        info_parts = [f"【{self.name}】({self.realm.value})", self.desc]
        
        if self.items:
            item_names = [item.name for item in self.items]
            info_parts.append(f"可获得材料：{', '.join(item_names)}")
        
        return " - ".join(info_parts)

    def get_structured_info(self) -> dict:
        items_info = [item.get_structured_info() for item in self.items]
        return {
            "name": self.name,
            "desc": self.desc,
            "grade": self.realm.value,
            "drops": items_info,
            "type": "animal"
        }

def _load_animals() -> tuple[dict[int, Animal], dict[str, Animal]]:
    """从配表加载animal数据"""
    animals_by_id: dict[int, Animal] = {}
    animals_by_name: dict[str, Animal] = {}
    
    animal_df = game_configs["animal"]
    for row in animal_df:
        item_ids_list = get_list_int(row, "item_ids")
            
        animal = Animal(
            id=get_int(row, "id"),
            name=get_str(row, "name"),
            desc=get_str(row, "desc"),
            realm=Realm.from_id(get_int(row, "stage_id")),
            item_ids=item_ids_list
        )
        animals_by_id[animal.id] = animal
        animals_by_name[animal.name] = animal
    
    return animals_by_id, animals_by_name

# 从配表加载animal数据
animals_by_id, animals_by_name = _load_animals()
