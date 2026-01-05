from __future__ import annotations

from typing import Tuple, Any

from src.classes.action import InstantAction
from src.classes.event import Event
from src.classes.region import CityRegion
from src.classes.item import items_by_name
from src.classes.normalize import normalize_goods_name


class Sell(InstantAction):
    """
    在城镇出售指定名称的物品/装备。
    如果是材料：一次性卖出持有的全部数量。
    如果是装备：卖出当前装备的（如果是当前装备）。
    收益通过 avatar.sell_item() / sell_weapon() / sell_auxiliary() 结算。
    """

    ACTION_NAME = "出售"
    EMOJI = "💰"
    DESC = "在城镇出售持有的某类物品的全部，或当前装备"
    DOABLES_REQUIREMENTS = "在城镇且持有可出售物品/装备"
    PARAMS = {"target_name": "str"}

    def _resolve_obj(self, target_name: str) -> Tuple[Any, str, str]:
        """
        解析出售对象
        返回: (对象, 类型, 显示名称)
        类型: "item", "weapon", "auxiliary", "none"
        """
        normalized_name = normalize_goods_name(target_name)
        
        # 1. 检查背包材料
        item = items_by_name.get(normalized_name)
        if item and self.avatar.get_item_quantity(item) > 0:
            return item, "item", item.name

        # 2. 检查当前兵器
        if self.avatar.weapon and normalize_goods_name(self.avatar.weapon.name) == normalized_name:
            return self.avatar.weapon, "weapon", self.avatar.weapon.name

        # 3. 检查当前辅助装备
        if self.avatar.auxiliary and normalize_goods_name(self.avatar.auxiliary.name) == normalized_name:
            return self.avatar.auxiliary, "auxiliary", self.avatar.auxiliary.name

        return None, "none", normalized_name

    def _execute(self, target_name: str) -> None:
        region = self.avatar.tile.region
        if not isinstance(region, CityRegion):
            return

        obj, obj_type, _ = self._resolve_obj(target_name)
        
        if obj_type == "item":
            quantity = self.avatar.get_item_quantity(obj)
            self.avatar.sell_item(obj, quantity)
        elif obj_type == "weapon":
            self.avatar.sell_weapon(obj)
            self.avatar.change_weapon(None) # 卖出后卸下
        elif obj_type == "auxiliary":
            self.avatar.sell_auxiliary(obj)
            self.avatar.change_auxiliary(None) # 卖出后卸下

    def can_start(self, target_name: str | None = None) -> tuple[bool, str]:
        region = self.avatar.tile.region
        if not isinstance(region, CityRegion):
            return False, "仅能在城市区域执行"
            
        if target_name is None:
            # 用于动作空间：只要有任何可卖东西即可
            has_items = bool(self.avatar.items)
            has_weapon = self.avatar.weapon is not None
            has_auxiliary = self.avatar.auxiliary is not None
            ok = has_items or has_weapon or has_auxiliary
            return (ok, "" if ok else "背包为空且无装备，无可出售物品")
        
        obj, obj_type, _ = self._resolve_obj(target_name)
        if obj_type == "none":
            return False, f"未持有物品/装备: {target_name}"
            
        return True, ""

    def start(self, target_name: str) -> Event:
        obj, obj_type, display_name = self._resolve_obj(target_name)
        return Event(
            self.world.month_stamp, 
            f"{self.avatar.name} 在城镇出售了 {display_name}", 
            related_avatars=[self.avatar.id]
        )

    async def finish(self, target_name: str) -> list[Event]:
        return []
