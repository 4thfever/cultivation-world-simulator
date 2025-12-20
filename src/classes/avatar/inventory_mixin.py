"""
Avatar 物品与装备管理 Mixin
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.classes.avatar.core import Avatar
    from src.classes.item import Item
    from src.classes.weapon import Weapon
    from src.classes.auxiliary import Auxiliary


class InventoryMixin:
    """物品与装备管理相关方法"""
    
    def add_item(self: "Avatar", item: "Item", quantity: int = 1) -> None:
        """
        添加物品到背包
        
        Args:
            item: 要添加的物品
            quantity: 添加数量，默认为1
        """
        if quantity <= 0:
            return
            
        if item in self.items:
            self.items[item] += quantity
        else:
            self.items[item] = quantity
    
    def remove_item(self: "Avatar", item: "Item", quantity: int = 1) -> bool:
        """
        从背包移除物品
        
        Args:
            item: 要移除的物品
            quantity: 移除数量，默认为1
            
        Returns:
            bool: 是否成功移除（如果物品不足则返回False）
        """
        if quantity <= 0:
            return True
            
        if item not in self.items:
            return False
            
        if self.items[item] < quantity:
            return False
            
        self.items[item] -= quantity
        
        # 如果数量为0，从字典中移除该物品
        if self.items[item] == 0:
            del self.items[item]
            
        return True
    
    def get_item_quantity(self: "Avatar", item: "Item") -> int:
        """
        获取指定物品的数量
        
        Args:
            item: 要查询的物品
            
        Returns:
            int: 物品数量，如果没有该物品则返回0
        """
        return self.items.get(item, 0)

    def change_weapon(self: "Avatar", new_weapon: "Weapon") -> None:
        """
        更换兵器，熟练度归零，并重新计算长期效果
        
        Args:
            new_weapon: 新的兵器
        """
        self.weapon = new_weapon
        self.weapon_proficiency = 0.0
        self.recalc_effects()
    
    def change_auxiliary(self: "Avatar", new_auxiliary: Optional["Auxiliary"]) -> None:
        """
        更换辅助装备，并重新计算长期效果
        
        Args:
            new_auxiliary: 新的辅助装备（可为 None 表示卸下）
        """
        self.auxiliary = new_auxiliary
        self.recalc_effects()
    
    def increase_weapon_proficiency(self: "Avatar", amount: float) -> None:
        """
        增加兵器熟练度，上限100
        
        Args:
            amount: 增加的熟练度值
        """
        # 应用extra_weapon_proficiency_gain效果（倍率加成）
        gain_multiplier = 1.0 + self.effects.get("extra_weapon_proficiency_gain", 0.0)
        actual_amount = amount * gain_multiplier
        self.weapon_proficiency = min(100.0, self.weapon_proficiency + actual_amount)

