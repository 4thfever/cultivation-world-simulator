from __future__ import annotations

from typing import TYPE_CHECKING, Tuple, Any

from src.classes.action import InstantAction
from src.classes.event import Event
from src.classes.region import CityRegion
from src.classes.elixir import Elixir, get_elixirs_by_realm
from src.classes.prices import prices
from src.classes.cultivation import Realm
from src.classes.weapon import Weapon
from src.classes.auxiliary import Auxiliary
from src.classes.material import Material
from src.utils.resolution import resolve_query

if TYPE_CHECKING:
    from src.classes.avatar import Avatar


class Buy(InstantAction):
    """
    在城镇购买物品。
    
    如果是丹药：购买后强制立即服用。
    如果是其他物品：购买后放入背包。
    如果是装备（兵器/法宝）：购买后直接装备（替换原有装备，旧装备折价售出）。
    """

    ACTION_NAME = "购买"
    EMOJI = "💸"
    elixir_names_str = ", ".join([e.name for e in get_elixirs_by_realm(Realm.Qi_Refinement)])
    DESC = f"在城镇购买物品/装备（丹药购买后将立即服用）。可选丹药：{elixir_names_str}"
    DOABLES_REQUIREMENTS = "在城镇且金钱足够"
    PARAMS = {"target_name": "str"}

    def can_start(self, target_name: str) -> tuple[bool, str]:
        region = self.avatar.tile.region
        if not isinstance(region, CityRegion):
            return False, "仅能在城市区域执行"
            
        res = resolve_query(target_name, expected_types=[Elixir, Weapon, Auxiliary, Material])
        if not res.is_valid:
            return False, f"未知物品: {target_name}"

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
        action_desc = "购买了"
        suffix = ""
        
        if isinstance(obj, Elixir):
            action_desc = "购买并服用了"
        elif isinstance(obj, (Weapon, Auxiliary)):
            action_desc = "购买并装备了"
            # 预测是否会有卖旧行为，生成对应描述
            if isinstance(obj, Weapon) and self.avatar.weapon:
                suffix = f" (并将原有的{self.avatar.weapon.name}折价售出)"
            elif isinstance(obj, Auxiliary) and self.avatar.auxiliary:
                suffix = f" (并将原有的{self.avatar.auxiliary.name}折价售出)"

        return Event(
            self.world.month_stamp, 
            f"{self.avatar.name} 在城镇花费 {price} 灵石{action_desc} {display_name}{suffix}", 
            related_avatars=[self.avatar.id]
        )

    async def finish(self, target_name: str) -> list[Event]:
        return []
