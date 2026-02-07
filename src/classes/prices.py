"""
统一价格系统
============

所有物品/装备的价格通过这个模块获取。
价格只和对应的 realm 绑定，全局统一。

价格设计参考（以练气期年收入约 20-30 灵石为基准）：
- 材料(Material): 采集物等消耗品
- 兵器(Weapon): 稀有装备，价值较高
- 辅助装备(Auxiliary): 法宝等，价值次于兵器
"""
from __future__ import annotations

from typing import Union, TYPE_CHECKING

from src.systems.cultivation import Realm

if TYPE_CHECKING:
    from src.classes.material import Material
    from src.classes.items.weapon import Weapon
    from src.classes.items.auxiliary import Auxiliary
    from src.classes.core.avatar import Avatar

# 类型别名
Sellable = Union["Material", "Weapon", "Auxiliary"]


class Prices:
    """
    价格体系。
    所有城镇可交易物品/装备的价格在此统一管理。
    """
    
    # 全局购买倍率（玩家从系统购买时的溢价）
    GLOBAL_BUY_MULTIPLIER = 1.5
    
    # 材料价格表（采集物等）
    MATERIAL_PRICES = {
        Realm.Qi_Refinement: 10,
        Realm.Foundation_Establishment: 30,
        Realm.Core_Formation: 50,
        Realm.Nascent_Soul: 70,
    }
    
    # 兵器价格表（稀有，价值高）
    WEAPON_PRICES = {
        Realm.Qi_Refinement: 150,
        Realm.Foundation_Establishment: 300,
        Realm.Core_Formation: 1000,
        Realm.Nascent_Soul: 2000,
    }
    
    # 辅助装备价格表
    AUXILIARY_PRICES = {
        Realm.Qi_Refinement: 150,
        Realm.Foundation_Establishment: 250,
        Realm.Core_Formation: 800,
        Realm.Nascent_Soul: 1600,
    }
    
    def get_material_price(self, material: "Material") -> int:
        """获取材料基础价格"""
        return self.MATERIAL_PRICES.get(material.realm, 10)
    
    def get_weapon_price(self, weapon: "Weapon") -> int:
        """获取兵器基础价格"""
        return self.WEAPON_PRICES.get(weapon.realm, 100)
    
    def get_auxiliary_price(self, auxiliary: "Auxiliary") -> int:
        """获取辅助装备基础价格"""
        return self.AUXILIARY_PRICES.get(auxiliary.realm, 80)
    
    def get_price(self, obj: Sellable) -> int:
        """
        统一基础价格查询接口。
        根据对象类型自动分发到对应的价格查询方法。
        注意：这是物品的【基准价值】，通常等于玩家【卖出给系统】的基础价格。
        """
        from src.classes.material import Material
        from src.classes.items.weapon import Weapon
        from src.classes.items.auxiliary import Auxiliary
        from src.classes.items.elixir import Elixir
        
        if isinstance(obj, Material):
            return self.get_material_price(obj)
        elif isinstance(obj, Weapon):
            return self.get_weapon_price(obj)
        elif isinstance(obj, Auxiliary):
            return self.get_auxiliary_price(obj)
        elif isinstance(obj, Elixir):
            return obj.price
        return 0

    def get_buying_price(self, obj: Sellable, buyer: "Avatar" = None) -> int:
        """
        获取玩家购买价格（从系统商店购买）。
        
        计算公式：
            基础价格 * max(1.0, GLOBAL_BUY_MULTIPLIER - 折扣)
            
        Args:
            obj: 交易物品
            buyer: 买家（用于计算折扣）
        """
        base_price = self.get_price(obj)
        
        # 默认倍率 1.5
        multiplier = self.GLOBAL_BUY_MULTIPLIER
        
        if buyer is not None:
            # 获取折扣 (倍率减免)
            # 例如 0.1 表示倍率 -0.1
            reduction = float(buyer.effects.get("shop_buy_price_reduction", 0.0))
            multiplier -= reduction
            
        # 保证倍率不低于 1.0 (原价)
        final_multiplier = max(1.0, multiplier)
        
        return int(base_price * final_multiplier)

    def get_selling_price(self, obj: Sellable, seller: "Avatar" = None) -> int:
        """
        获取玩家卖出价格（卖给系统商店）。
        
        计算公式：
            基础价格 * (1.0 + 卖出加成)
            
        Args:
            obj: 交易物品
            seller: 卖家（用于计算加成）
        """
        base_price = self.get_price(obj)
        
        multiplier = 1.0
        
        if seller is not None:
            # 获取卖出加成
            # 例如 0.2 表示价格 +20%
            bonus = float(seller.effects.get("extra_item_sell_price_multiplier", 0.0))
            multiplier += bonus
            
        return int(base_price * multiplier)


# 全局单例
prices = Prices()
