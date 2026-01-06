from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Tuple, Any

from src.classes.action import InstantAction
from src.classes.event import Event
from src.classes.region import CityRegion
from src.classes.elixir import Elixir, get_elixirs_by_realm
from src.classes.prices import prices
from src.classes.cultivation import Realm
from src.utils.resolution import resolve_goods_by_name

if TYPE_CHECKING:
    from src.classes.avatar import Avatar


class Buy(InstantAction):
    """
    在城镇购买物品。
    
    如果是丹药：购买后强制立即服用。
    如果是其他物品：购买后放入背包。
    如果是装备（兵器/法宝）：购买后直接装备（替换原有装备）。
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
            
        obj, obj_type, display_name = resolve_goods_by_name(target_name)
        if obj_type == "unknown":
            return False, f"未知物品: {target_name}"

        # 检查价格
        price = prices.get_buying_price(obj, self.avatar)
        if self.avatar.magic_stone < price:
            return False, f"灵石不足 (需要 {price})"

        # 丹药特殊限制
        if obj_type == "elixir":
            elixir: Elixir = obj
            
            # 必须是练气期丹药
            if elixir.realm != Realm.Qi_Refinement:
                return False, "当前仅开放练气期丹药购买"

            # 境界限制
            if elixir.realm > self.avatar.cultivation_progress.realm:
                return False, f"境界不足，无法承受药力 ({elixir.realm.value})"
                
            # 耐药性/生效中检查
            for consumed in self.avatar.elixirs:
                if consumed.elixir.id == elixir.id:
                    if not consumed.is_completely_expired(int(self.world.month_stamp)):
                        return False, "药效尚存，无法重复服用"
                        
        return True, ""

    def _execute(self, target_name: str) -> None:
        obj, obj_type, display_name = resolve_goods_by_name(target_name)
        if obj_type == "unknown":
            return
            
        price = prices.get_buying_price(obj, self.avatar)
        self.avatar.magic_stone -= price
        
        # 交付
        if obj_type == "elixir":
            self.avatar.consume_elixir(obj)
        # TODO: 购买新装备，如果换下了旧装备，应该自动卖出
        # 但是我现在还没有购买的能力，所以这个逻辑之后做。
        elif obj_type == "item":
            self.avatar.add_item(obj)
        elif obj_type == "weapon":
            # 购买装备需要深拷贝，因为装备有独立状态
            new_weapon = copy.deepcopy(obj)
            self.avatar.change_weapon(new_weapon)
        elif obj_type == "auxiliary":
            # 购买装备需要深拷贝
            new_auxiliary = copy.deepcopy(obj)
            self.avatar.change_auxiliary(new_auxiliary)

    def start(self, target_name: str) -> Event:
        obj, obj_type, display_name = resolve_goods_by_name(target_name)
        
        if obj_type == "elixir":
            action_desc = "购买并服用了"
        elif obj_type in ["weapon", "auxiliary"]:
            action_desc = "购买并装备了"
        else:
            action_desc = "购买了"
            
        price = prices.get_buying_price(obj, self.avatar) if obj else 0
        
        return Event(
            self.world.month_stamp, 
            f"{self.avatar.name} 在城镇花费 {price} 灵石{action_desc} {display_name}", 
            related_avatars=[self.avatar.id]
        )

    async def finish(self, target_name: str) -> list[Event]:
        return []
