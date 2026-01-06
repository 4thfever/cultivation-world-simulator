from __future__ import annotations

from typing import Tuple, Any

from src.classes.action import InstantAction
from src.classes.event import Event
from src.classes.region import CityRegion
from src.classes.normalize import normalize_goods_name
from src.utils.resolution import resolve_goods_by_name


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

    def can_start(self, target_name: str) -> tuple[bool, str]:
        region = self.avatar.tile.region
        if not isinstance(region, CityRegion):
            return False, "仅能在城市区域执行"
        
        # 使用通用解析逻辑获取物品原型和类型
        obj, obj_type, _ = resolve_goods_by_name(target_name)
        normalized_name = normalize_goods_name(target_name)
        
        # 1. 如果是物品，检查背包
        if obj_type == "item":
            if self.avatar.get_item_quantity(obj) > 0:
                pass # 检查通过
            else:
                 return False, f"未持有物品: {target_name}"

        # 2. 如果是兵器，检查当前装备
        elif obj_type == "weapon":
            if self.avatar.weapon and normalize_goods_name(self.avatar.weapon.name) == normalized_name:
                pass # 检查通过
            else:
                return False, f"未持有装备: {target_name}"

        # 3. 如果是辅助装备，检查当前装备
        elif obj_type == "auxiliary":
            if self.avatar.auxiliary and normalize_goods_name(self.avatar.auxiliary.name) == normalized_name:
                pass # 检查通过
            else:
                return False, f"未持有装备: {target_name}"
        
        else:
            return False, f"未持有物品/装备: {target_name}"
            
        return True, ""

    def _execute(self, target_name: str) -> None:
        region = self.avatar.tile.region
        if not isinstance(region, CityRegion):
            return

        # 使用通用解析逻辑获取物品原型和类型
        obj, obj_type, _ = resolve_goods_by_name(target_name)
        normalized_name = normalize_goods_name(target_name)
        
        if obj_type == "item":
            quantity = self.avatar.get_item_quantity(obj)
            self.avatar.sell_item(obj, quantity)
        elif obj_type == "weapon":
            # 需要再确认一次是否是当前装备
             if self.avatar.weapon and normalize_goods_name(self.avatar.weapon.name) == normalized_name:
                self.avatar.sell_weapon(obj)
                self.avatar.change_weapon(None) # 卖出后卸下
        elif obj_type == "auxiliary":
            # 需要再确认一次是否是当前装备
             if self.avatar.auxiliary and normalize_goods_name(self.avatar.auxiliary.name) == normalized_name:
                self.avatar.sell_auxiliary(obj)
                self.avatar.change_auxiliary(None) # 卖出后卸下

    def start(self, target_name: str) -> Event:
        obj, obj_type, display_name = resolve_goods_by_name(target_name)
        return Event(
            self.world.month_stamp, 
            f"{self.avatar.name} 在城镇出售了 {display_name}", 
            related_avatars=[self.avatar.id]
        )

    async def finish(self, target_name: str) -> list[Event]:
        return []
