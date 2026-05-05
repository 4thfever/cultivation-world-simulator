from __future__ import annotations

from typing import TYPE_CHECKING, Tuple, Any

from src.i18n import t
from src.classes.action import InstantAction
from src.classes.action.param_options import ParamOptionSource
from src.classes.event import Event
from src.classes.environment.region import CityRegion
from src.classes.items.elixir import Elixir
from src.classes.prices import prices
from src.classes.items.weapon import Weapon
from src.classes.items.auxiliary import Auxiliary
from src.classes.material import Material
from src.utils.resolution import resolve_query

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar


class Buy(InstantAction):
    """
    在城镇购买物品。
    
    如果是丹药：购买后强制立即服用。
    如果是其他物品：购买后放入背包。
    如果是装备（兵器/法宝）：购买后直接装备（替换原有装备，旧装备折价售出）。
    """
    
    # 多语言 ID
    ACTION_NAME_ID = "buy_action_name"
    DESC_ID = "buy_description"
    REQUIREMENTS_ID = "buy_requirements"
    
    # 不需要翻译的常量
    EMOJI = "💸"
    PARAMS = {"target_name": "str"}
    PARAM_OPTION_SOURCES = {"target_name": ParamOptionSource.CURRENT_CITY_STORE_ITEM_NAME}

    def can_start(self, target_name: str) -> tuple[bool, str]:
        region = self.avatar.tile.region
        if not isinstance(region, CityRegion):
            return False, t("Can only execute in city areas")
            
        res = resolve_query(target_name, expected_types=[Elixir, Weapon, Auxiliary, Material])
        if not res.is_valid:
            return False, t("Unknown item: {name}", name=target_name)

        # 检查商店是否售卖
        # 必须是 StoreMixin (CityRegion 混入了 StoreMixin)
        if hasattr(region, "is_selling"):
            if not region.is_selling(res.obj.name):
                return False, t("{region} does not sell {item}", region=region.name, item=res.obj.name)
        else:
            # 如果不是商店区域（虽然前面已经检查了 CityRegion，但为了安全）
            return False, t("This area has no shop")

        # 核心逻辑委托给 Avatar
        return self.avatar.can_buy_item(res.obj)

    def _execute(self, target_name: str) -> None:
        res = resolve_query(target_name, expected_types=[Elixir, Weapon, Auxiliary, Material])
        if not res.is_valid:
            return
            
        # 真正执行购买 (含扣款、服用/装备/卖旧)
        self.avatar.buy_item(res.obj)

    def start(self, target_name: str) -> Event:
        res = resolve_query(target_name, expected_types=[Elixir, Weapon, Auxiliary, Material])
        obj = res.obj
        display_name = res.name
        
        # 预先获取一些信息用于生成文本 (不修改状态)
        price = prices.get_buying_price(obj, self.avatar)
        
        # 构造描述
        action_desc = t("bought")
        suffix = ""
        
        if isinstance(obj, Elixir):
            action_desc = t("bought and consumed")
        elif isinstance(obj, (Weapon, Auxiliary)):
            action_desc = t("bought and equipped")
            # 预测是否会有卖旧行为，生成对应描述
            if isinstance(obj, Weapon) and self.avatar.weapon:
                suffix = t(" (and sold old {item} at reduced price)", item=self.avatar.weapon.name)
            elif isinstance(obj, Auxiliary) and self.avatar.auxiliary:
                suffix = t(" (and sold old {item} at reduced price)", item=self.avatar.auxiliary.name)

        content = t("{avatar} spent {price} spirit stones in town, {action} {item}{suffix}",
                   avatar=self.avatar.name, price=price, action=action_desc, 
                   item=display_name, suffix=suffix)
        return Event(
            self.world.month_stamp, 
            content, 
            related_avatars=[self.avatar.id]
        )

    async def finish(self, target_name: str) -> list[Event]:
        return []
