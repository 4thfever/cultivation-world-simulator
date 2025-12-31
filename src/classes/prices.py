"""
统一价格系统
============

所有物品/装备的价格通过这个模块获取。
价格只和对应的 realm 绑定，全局统一。

价格设计参考（以练气期年收入约 20-30 灵石为基准）：
- 材料(Item): 采集物等消耗品
- 兵器(Weapon): 稀有装备，价值较高
- 辅助装备(Auxiliary): 法宝等，价值次于兵器
"""
from __future__ import annotations

from typing import Union, TYPE_CHECKING

from src.classes.cultivation import Realm

if TYPE_CHECKING:
    from src.classes.item import Item
    from src.classes.weapon import Weapon
    from src.classes.auxiliary import Auxiliary

# 类型别名
Sellable = Union["Item", "Weapon", "Auxiliary"]


class Prices:
    """
    价格体系。
    所有城镇可交易物品/装备的价格在此统一管理。
    """
    
    # 材料价格表（采集物等）
    ITEM_PRICES = {
        Realm.Qi_Refinement: 10,
        Realm.Foundation_Establishment: 30,
        Realm.Core_Formation: 60,
        Realm.Nascent_Soul: 100,
    }
    
    # 兵器价格表（稀有，价值高）
    WEAPON_PRICES = {
        Realm.Qi_Refinement: 10,
        Realm.Foundation_Establishment: 300,
        Realm.Core_Formation: 1000,
        Realm.Nascent_Soul: 2000,
    }
    
    # 辅助装备价格表
    AUXILIARY_PRICES = {
        Realm.Qi_Refinement: 10,
        Realm.Foundation_Establishment: 250,
        Realm.Core_Formation: 800,
        Realm.Nascent_Soul: 1600,
    }
    
    def get_item_price(self, item: "Item") -> int:
        """获取材料价格"""
        return self.ITEM_PRICES.get(item.realm, 10)
    
    def get_weapon_price(self, weapon: "Weapon") -> int:
        """获取兵器价格"""
        return self.WEAPON_PRICES.get(weapon.realm, 100)
    
    def get_auxiliary_price(self, auxiliary: "Auxiliary") -> int:
        """获取辅助装备价格"""
        return self.AUXILIARY_PRICES.get(auxiliary.realm, 80)
    
    def get_price(self, obj: Sellable) -> int:
        """
        统一价格查询接口。
        根据对象类型自动分发到对应的价格查询方法。
        """
        from src.classes.item import Item
        from src.classes.weapon import Weapon
        from src.classes.auxiliary import Auxiliary
        
        if isinstance(obj, Item):
            return self.get_item_price(obj)
        elif isinstance(obj, Weapon):
            return self.get_weapon_price(obj)
        elif isinstance(obj, Auxiliary):
            return self.get_auxiliary_price(obj)
        return 0


# 全局单例
prices = Prices()
