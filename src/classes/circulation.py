from __future__ import annotations
from typing import Dict, List, TYPE_CHECKING, Any
import copy

if TYPE_CHECKING:
    from src.classes.items.weapon import Weapon
    from src.classes.items.auxiliary import Auxiliary
    from src.classes.items.elixir import Elixir


class CirculationManager:
    """
    出世物品流通管理器
    记录所有从角色身上流出的贵重物品（出售、死亡掉落且未被夺取等）
    用于后续拍卖会等玩法的物品池
    """
    
    def __init__(self):
        # 存储被卖出的兵器
        self.sold_weapons: List[Weapon] = []
        # 存储被卖出的辅助
        self.sold_auxiliaries: List[Auxiliary] = []
        # 存储被卖出的丹药
        self.sold_elixirs: List[Elixir] = []
        
    @property
    def sold_item_count(self) -> int:
        """记录一共有多少个sold items"""
        return len(self.sold_weapons) + len(self.sold_auxiliaries) + len(self.sold_elixirs)

    def add_weapon(self, weapon: "Weapon") -> None:
        """记录一件流出的兵器"""
        if weapon is None:
            return
        # 使用深拷贝存储，防止外部修改影响记录
        # 注意：这里假设 weapon 对象是可以被 copy 的
        self.sold_weapons.append(weapon.instantiate())
        
    def add_auxiliary(self, auxiliary: "Auxiliary") -> None:
        """记录一件流出的辅助装备"""
        if auxiliary is None:
            return
        self.sold_auxiliaries.append(auxiliary.instantiate())

    def add_elixir(self, elixir: "Elixir") -> None:
        """记录一件流出的丹药"""
        if elixir is None:
            return
        # 尝试实例化，如果失败（如未实现）则拷贝，或者直接存储
        if hasattr(elixir, "instantiate"):
            self.sold_elixirs.append(elixir.instantiate())
        else:
            self.sold_elixirs.append(copy.copy(elixir))

    def add_item(self, item: Any) -> None:
        """
        通用入口：记录一件流出的物品。
        根据物品类型自动分发到对应的存储列表中。
        设计此方法的目的是为了统一所有物品流出逻辑，避免各个业务模块手动判断类型。
        """
        if item is None:
            return
            
        from src.classes.items.weapon import Weapon
        from src.classes.items.auxiliary import Auxiliary
        from src.classes.items.elixir import Elixir
        
        if isinstance(item, Weapon):
            self.add_weapon(item)
        elif isinstance(item, Auxiliary):
            self.add_auxiliary(item)
        elif isinstance(item, Elixir):
            self.add_elixir(item)
        # 未来扩展其他类型...

    def remove_item(self, item: Any) -> None:
        """
        从流通池移除物品
        """
        from src.classes.items.weapon import Weapon
        from src.classes.items.auxiliary import Auxiliary
        from src.classes.items.elixir import Elixir
        
        if isinstance(item, Weapon):
            if item in self.sold_weapons:
                self.sold_weapons.remove(item)
        elif isinstance(item, Auxiliary):
            if item in self.sold_auxiliaries:
                self.sold_auxiliaries.remove(item)
        elif isinstance(item, Elixir):
            if item in self.sold_elixirs:
                self.sold_elixirs.remove(item)
    
    def to_save_dict(self) -> dict:
        """序列化为字典以便存档"""
        return {
            "weapons": [self._item_to_dict(w) for w in self.sold_weapons],
            "auxiliaries": [self._item_to_dict(a) for a in self.sold_auxiliaries],
            "elixirs": [self._item_to_dict(e) for e in self.sold_elixirs]
        }
    
    def load_from_dict(self, data: dict) -> None:
        """从字典恢复数据"""
        from src.classes.items.weapon import weapons_by_id
        from src.classes.items.auxiliary import auxiliaries_by_id
        from src.classes.items.elixir import elixirs_by_id
        
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

        self.sold_elixirs = []
        for e_data in data.get("elixirs", []):
            e_id = e_data.get("id")
            if e_id in elixirs_by_id:
                elixir = copy.copy(elixirs_by_id[e_id])
                elixir.special_data = e_data.get("special_data", {})
                self.sold_elixirs.append(elixir)

    def _item_to_dict(self, item) -> dict:
        """将物品对象转换为简略的存储格式"""
        return {
            "id": item.id,
            "special_data": getattr(item, "special_data", {})
        }

