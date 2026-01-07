import copy
from typing import TypeVar, Any

T = TypeVar("T", bound="Item")

class Item:
    """所有物品的基类"""
    
    def instantiate(self: T) -> T:
        """
        创建该物品的一个新实例。
        默认行为是深拷贝，适用于有独立状态的物品（如装备）。
        子类如果是只读对象（如材料），可以重写此方法返回 self 以优化性能。
        """
        return copy.deepcopy(self)

