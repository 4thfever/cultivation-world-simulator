from typing import Dict, Type, TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.classes.item import Item

class ItemRegistry:
    """全局物品注册表"""
    
    _items_by_id: Dict[int, "Item"] = {}

    @classmethod
    def register(cls, item_id: int, item: "Item"):
        if item_id in cls._items_by_id:
            # 允许重复注册（覆盖），但在开发环境中最好打印警告
            pass
        cls._items_by_id[item_id] = item

    @classmethod
    def get(cls, item_id: int) -> Optional["Item"]:
        return cls._items_by_id.get(item_id)

    @classmethod
    def get_all(cls) -> Dict[int, "Item"]:
        return cls._items_by_id
