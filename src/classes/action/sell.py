from __future__ import annotations

from typing import Tuple, Any

from src.i18n import t
from src.classes.action import InstantAction
from src.classes.action.param_options import ParamOptionSource
from src.classes.event import Event
from src.classes.environment.region import CityRegion
from src.utils.normalize import normalize_goods_name
from src.utils.resolution import resolve_query
from src.classes.material import Material
from src.classes.items.weapon import Weapon
from src.classes.items.auxiliary import Auxiliary


class Sell(InstantAction):
    """
    在城镇出售指定名称的物品/装备。
    如果是材料：一次性卖出持有的全部数量。
    如果是装备：卖出当前装备的（如果是当前装备）。
    收益通过 avatar.sell_material() / sell_weapon() / sell_auxiliary() 结算。
    """
    
    # 多语言 ID
    ACTION_NAME_ID = "sell_action_name"
    DESC_ID = "sell_description"
    REQUIREMENTS_ID = "sell_requirements"
    
    # 不需要翻译的常量
    EMOJI = "💰"
    PARAMS = {"target_name": "str"}
    PARAM_OPTION_SOURCES = {"target_name": ParamOptionSource.SELLABLE_ITEM_NAME}

    def can_start(self, target_name: str) -> tuple[bool, str]:
        region = self.avatar.tile.region
        if not isinstance(region, CityRegion):
            return False, t("Can only execute in city areas")
        
        # 使用通用解析逻辑获取物品原型和类型
        res = resolve_query(target_name, expected_types=[Material, Weapon, Auxiliary])
        if not res.is_valid:
            return False, t("Do not possess item/equipment: {name}", name=target_name)
        
        obj = res.obj
        normalized_name = normalize_goods_name(target_name)
        
        # 1. 如果是材料，检查背包
        if isinstance(obj, Material):
            if self.avatar.get_material_quantity(obj) > 0:
                pass # 检查通过
            else:
                return False, t("Do not possess material: {name}", name=target_name)

        # 2. 如果是兵器，检查当前装备
        elif isinstance(obj, Weapon):
            if self.avatar.weapon and normalize_goods_name(self.avatar.weapon.name) == normalized_name:
                pass # 检查通过
            else:
                return False, t("Do not possess equipment: {name}", name=target_name)

        # 3. 如果是辅助装备，检查当前装备
        elif isinstance(obj, Auxiliary):
            if self.avatar.auxiliary and normalize_goods_name(self.avatar.auxiliary.name) == normalized_name:
                pass # 检查通过
            else:
                return False, t("Do not possess equipment: {name}", name=target_name)
        
        else:
            return False, t("Cannot sell this type: {name}", name=target_name)
            
        return True, ""

    def _execute(self, target_name: str) -> None:
        region = self.avatar.tile.region
        if not isinstance(region, CityRegion):
            return

        res = resolve_query(target_name, expected_types=[Material, Weapon, Auxiliary])
        if not res.is_valid:
            return
            
        obj = res.obj
        normalized_name = normalize_goods_name(target_name)
        
        if isinstance(obj, Material):
            quantity = self.avatar.get_material_quantity(obj)
            self.avatar.sell_material(obj, quantity)
        elif isinstance(obj, Weapon):
            # 需要再确认一次是否是当前装备
             if self.avatar.weapon and normalize_goods_name(self.avatar.weapon.name) == normalized_name:
                self.avatar.sell_weapon(obj)
                self.avatar.change_weapon(None) # 卖出后卸下
        elif isinstance(obj, Auxiliary):
            # 需要再确认一次是否是当前装备
             if self.avatar.auxiliary and normalize_goods_name(self.avatar.auxiliary.name) == normalized_name:
                self.avatar.sell_auxiliary(obj)
                self.avatar.change_auxiliary(None) # 卖出后卸下

    def start(self, target_name: str) -> Event:
        res = resolve_query(target_name)
        display_name = res.name if res.is_valid else target_name
        content = t("{avatar} sold {item} in town",
                   avatar=self.avatar.name, item=display_name)
        return Event(
            self.world.month_stamp, 
            content, 
            related_avatars=[self.avatar.id]
        )

    async def finish(self, target_name: str) -> list[Event]:
        return []
