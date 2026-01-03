from __future__ import annotations
from typing import Dict, List, TYPE_CHECKING
import copy

if TYPE_CHECKING:
    from src.classes.weapon import Weapon
    from src.classes.auxiliary import Auxiliary


class CirculationManager:
    """
    出世物品流通管理器
    记录所有从角色身上流出的贵重物品（出售、死亡掉落且未被夺取等）
    用于后续拍卖会等玩法的物品池
    """
    
    def __init__(self):
        # 存储被卖出的法宝
        self.sold_weapons: List[Weapon] = []
        # 存储被卖出的宝物
        self.sold_auxiliaries: List[Auxiliary] = []
        
    def add_weapon(self, weapon: "Weapon") -> None:
        """记录一件流出的兵器"""
        if weapon is None:
            return
        # 使用深拷贝存储，防止外部修改影响记录
        # 注意：这里假设 weapon 对象是可以被 copy 的
        self.sold_weapons.append(copy.deepcopy(weapon))
        
    def add_auxiliary(self, auxiliary: "Auxiliary") -> None:
        """记录一件流出的辅助装备"""
        if auxiliary is None:
            return
        self.sold_auxiliaries.append(copy.deepcopy(auxiliary))
        
    def to_save_dict(self) -> dict:
        """序列化为字典以便存档"""
        return {
            "weapons": [self._item_to_dict(w) for w in self.sold_weapons],
            "auxiliaries": [self._item_to_dict(a) for a in self.sold_auxiliaries]
        }
    
    def load_from_dict(self, data: dict) -> None:
        """从字典恢复数据"""
        from src.classes.weapon import weapons_by_id
        from src.classes.auxiliary import auxiliaries_by_id
        
        self.sold_weapons = []
        for w_data in data.get("weapons", []):
            w_id = w_data.get("id")
            if w_id in weapons_by_id:
                weapon = copy.copy(weapons_by_id[w_id])
                weapon.special_data = w_data.get("special_data", {})
                self.sold_weapons.append(weapon)
                
        self.sold_auxiliaries = []
        for a_data in data.get("auxiliaries", []):
            a_id = a_data.get("id")
            if a_id in auxiliaries_by_id:
                auxiliary = copy.copy(auxiliaries_by_id[a_id])
                auxiliary.special_data = a_data.get("special_data", {})
                self.sold_auxiliaries.append(auxiliary)

    def _item_to_dict(self, item) -> dict:
        """将物品对象转换为简略的存储格式"""
        return {
            "id": item.id,
            "special_data": getattr(item, "special_data", {})
        }

