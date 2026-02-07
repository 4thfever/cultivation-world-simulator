"""
Avatar 物品与装备管理 Mixin
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Any, Union

if TYPE_CHECKING:
    from src.classes.core.avatar.core import Avatar
    from src.classes.material import Material
    from src.classes.items.weapon import Weapon
    from src.classes.items.auxiliary import Auxiliary
    from src.classes.items.elixir import Elixir


class InventoryMixin:
    """物品与装备管理相关方法"""
    
    def add_material(self: "Avatar", material: "Material", quantity: int = 1) -> None:
        """
        添加物品到背包
        
        Args:
            material: 要添加的物品
            quantity: 添加数量，默认为1
        """
        if quantity <= 0:
            return
            
        if material in self.materials:
            self.materials[material] += quantity
        else:
            self.materials[material] = quantity
    
    def remove_material(self: "Avatar", material: "Material", quantity: int = 1) -> bool:
        """
        从背包移除材料
        
        Args:
            material: 要移除的材料
            quantity: 移除数量，默认为1
            
        Returns:
            bool: 是否成功移除（如果材料不足则返回False）
        """
        if quantity <= 0:
            return True
            
        if material not in self.materials:
            return False
            
        if self.materials[material] < quantity:
            return False
            
        self.materials[material] -= quantity
        
        # 如果数量为0，从字典中移除该物品
        if self.materials[material] == 0:
            del self.materials[material]
            
        return True
    
    def get_material_quantity(self: "Avatar", material: "Material") -> int:
        """
        获取指定材料的数量
        
        Args:
            material: 要查询的材料
            
        Returns:
            int: 材料数量，如果没有该材料则返回0
        """
        return self.materials.get(material, 0)

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

    # ==================== 出售接口 ====================
    
    def sell_material(self: "Avatar", material: "Material", quantity: int = 1) -> int:
        """
        出售材料物品，返回获得的灵石数量。
        应用 extra_item_sell_price_multiplier 效果。
        """
        from src.classes.prices import prices
        
        if quantity <= 0 or self.get_material_quantity(material) < quantity:
            return 0
        
        self.remove_material(material, quantity)
        
        # 使用统一的卖出价格接口（包含所有加成逻辑）
        unit_price = prices.get_selling_price(material, self)
        total = unit_price * quantity
        
        self.magic_stone = self.magic_stone + total
        return total

    def sell_weapon(self: "Avatar", weapon: "Weapon") -> int:
        """
        出售兵器，返回获得的灵石数量。
        注意：这是辅助方法，不会自动卸下当前装备。
        """
        from src.classes.prices import prices
        
        # 记录流转
        self.world.circulation.add_weapon(weapon)

        # 使用统一的卖出价格接口
        total = prices.get_selling_price(weapon, self)
        self.magic_stone = self.magic_stone + total
        return total

    def sell_auxiliary(self: "Avatar", auxiliary: "Auxiliary") -> int:
        """
        出售辅助装备，返回获得的灵石数量。
        注意：这是辅助方法，不会自动卸下当前装备。
        """
        from src.classes.prices import prices
        
        # 记录流转
        self.world.circulation.add_auxiliary(auxiliary)

        # 使用统一的卖出价格接口
        total = prices.get_selling_price(auxiliary, self)
        self.magic_stone = self.magic_stone + total
        return total

    def sell_elixir(self: "Avatar", elixir: "Elixir") -> int:
        """
        出售丹药，返回获得的灵石数量。
        """
        from src.classes.prices import prices
        
        # 记录流转
        self.world.circulation.add_elixir(elixir)
        
        # 使用统一的卖出价格接口
        total = prices.get_selling_price(elixir, self)
        self.magic_stone = self.magic_stone + total
        return total

    # ==================== 购买接口 ====================

    def can_buy_item(self: "Avatar", obj: Any) -> tuple[bool, str]:
        """
        检查是否可以购买指定物品。
        涵盖价格检查、境界限制、耐药性等。
        """
        from src.classes.items.elixir import Elixir
        from src.classes.prices import prices
        from src.systems.cultivation import Realm
        
        # 1. 检查价格
        price = prices.get_buying_price(obj, self)
        if self.magic_stone < price:
            return False, f"灵石不足 (需要 {price})"

        # 2. 丹药特殊检查
        if isinstance(obj, Elixir):
            # 境界限制
            if obj.realm > self.cultivation_progress.realm:
                # 使用 str() 来触发 Realm 的 __str__ 方法进行 i18n 翻译。
                return False, f"境界不足，无法承受药力 ({str(obj.realm)})"

            # 耐药性/生效中检查
            for consumed in self.elixirs:
                if consumed.elixir.id == obj.id:
                    if not consumed.is_completely_expired(int(self.world.month_stamp)):
                        return False, "药效尚存，无法重复服用"
                
        return True, ""

    def buy_item(self: "Avatar", obj: Any) -> dict:
        """
        执行购买逻辑。
        包括扣款、获得物品（服用/入包/装备）、以旧换新。
        返回交易报告 dict。
        """
        from src.classes.items.elixir import Elixir
        from src.classes.items.weapon import Weapon
        from src.classes.items.auxiliary import Auxiliary
        from src.classes.material import Material
        from src.classes.prices import prices
        
        report = {
            "success": True,
            "cost": 0,
            "action_type": "store", # store, consume, equip
            "sold_item_name": None,
            "sold_item_refund": 0
        }
        
        # 1. 扣款
        price = prices.get_buying_price(obj, self)
        self.magic_stone -= price
        report["cost"] = price
        
        # 2. 交付
        if isinstance(obj, Elixir):
            # 购买即服用
            self.consume_elixir(obj)
            report["action_type"] = "consume"
            
        elif isinstance(obj, Material):
            # 放入背包
            self.add_material(obj)
            report["action_type"] = "store"
            
        elif isinstance(obj, (Weapon, Auxiliary)):
            # 装备需要深拷贝
            new_equip = obj.instantiate()
            
            # 尝试卖出旧装备并换上新装备
            sold_name, refund = self._equip_and_trade_in(new_equip)
            
            report["action_type"] = "equip"
            if sold_name:
                report["sold_item_name"] = sold_name
                report["sold_item_refund"] = refund
            
        return report

    def _equip_and_trade_in(self: "Avatar", new_equip: Union["Weapon", "Auxiliary"]) -> tuple[str | None, int]:
        """
        内部方法：装备新物品，并尝试卖出旧物品（如果有）。
        返回: (旧物品名称, 卖出金额)
        """
        from src.classes.items.weapon import Weapon
        from src.classes.items.auxiliary import Auxiliary
        
        sold_name = None
        refund = 0
        
        if isinstance(new_equip, Weapon):
            # 检查是否有旧兵器
            if self.weapon:
                sold_name = self.weapon.name
                # sell_weapon 会把旧兵器加到 circulation 并加钱给 avatar
                # 注意：sell_weapon 不会 clear self.weapon，也不会 deepcopy（因为是直接把引用给 circulation）
                # 这是正确的，旧对象给系统，新对象上身
                refund = self.sell_weapon(self.weapon)
                
            # 换上新兵器 (覆盖 self.weapon)
            self.change_weapon(new_equip)
            
        elif isinstance(new_equip, Auxiliary):
            # 检查是否有旧法宝
            if self.auxiliary:
                sold_name = self.auxiliary.name
                refund = self.sell_auxiliary(self.auxiliary)
                
            # 换上新法宝
            self.change_auxiliary(new_equip)
            
        return sold_name, refund
