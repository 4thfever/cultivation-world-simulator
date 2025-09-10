from dataclasses import dataclass

from src.utils.df import game_configs

@dataclass
class Item:
    """
    物品
    """
    id: int
    name: str
    desc: str
    grade: int

    def __hash__(self) -> int:
        return hash(self.id)

    def __str__(self) -> str:
        return self.name

def _load_items() -> tuple[dict[int, Item], dict[str, Item]]:
    """从配表加载item数据"""
    items_by_id: dict[int, Item] = {}
    items_by_name: dict[str, Item] = {}
    
    item_df = game_configs["item"]
    for _, row in item_df.iterrows():
        item = Item(
            id=int(row["id"]),
            name=str(row["name"]),
            desc=str(row["desc"]),
            grade=int(row["grade"])
        )
        items_by_id[item.id] = item
        items_by_name[item.name] = item
    
    return items_by_id, items_by_name

# 从配表加载item数据
items_by_id, items_by_name = _load_items()



