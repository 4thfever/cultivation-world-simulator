from dataclasses import dataclass

from src.utils.df import game_configs, get_str, get_int
from src.classes.cultivation import Realm

@dataclass
class Item:
    """
    物品
    """
    id: int
    name: str
    desc: str
    realm: Realm

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
            "name": self.name,
            "desc": self.desc,
            "grade": self.realm.value,
            "effect_desc": "" # 物品暂时没有效果字段
        }

def _load_items() -> tuple[dict[int, Item], dict[str, Item]]:
    """从配表加载item数据"""
    items_by_id: dict[int, Item] = {}
    items_by_name: dict[str, Item] = {}
    
    item_df = game_configs["item"]
    for row in item_df:
        item = Item(
            id=get_int(row, "id"),
            name=get_str(row, "name"),
            desc=get_str(row, "desc"),
            realm=Realm.from_id(get_int(row, "stage_id"))
        )
        items_by_id[item.id] = item
        items_by_name[item.name] = item
    
    return items_by_id, items_by_name

# 从配表加载item数据
items_by_id, items_by_name = _load_items()
