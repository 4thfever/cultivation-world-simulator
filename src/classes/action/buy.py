from __future__ import annotations

from typing import TYPE_CHECKING, Tuple, Any

from src.classes.action import InstantAction
from src.classes.event import Event
from src.classes.region import CityRegion
from src.classes.elixir import elixirs_by_name, Elixir
from src.classes.item import items_by_name, Item
from src.classes.prices import prices
from src.classes.normalize import normalize_item_name

if TYPE_CHECKING:
    from src.classes.avatar import Avatar


class BuyItem(InstantAction):
    """
    在城镇购买物品。
    
    如果是丹药：购买后强制立即服用。
    如果是其他物品：购买后放入背包。
    """

    ACTION_NAME = "购买物品"
    EMOJI = "💸"
    DESC = "在城镇购买物品（丹药购买后将立即服用）"
    DOABLES_REQUIREMENTS = "在城镇且金钱足够"
    PARAMS = {"item_name": "str"}

    def _resolve_obj(self, item_name: str) -> Tuple[Any, str, str]:
        """
        解析物品名称，返回 (对象, 类型, 显示名称)。
        类型字符串: "elixir", "item", "unknown"
        """
        normalized_name = normalize_item_name(item_name)
        
        # 1. 尝试作为丹药查找
        if normalized_name in elixirs_by_name:
            # 这里的 elixirs_by_name 返回的是 list，我们取第一个作为购买对象
            # TODO: 如果未来有同名不同级的丹药，这里可能需要更精确的逻辑
            elixir = elixirs_by_name[normalized_name][0]
            return elixir, "elixir", elixir.name

        # 2. 尝试作为普通物品查找
        item = items_by_name.get(normalized_name)
        if item:
            return item, "item", item.name

        return None, "unknown", normalized_name

    def can_start(self, item_name: str | None = None) -> tuple[bool, str]:
        region = self.avatar.tile.region
        if not isinstance(region, CityRegion):
            return False, "仅能在城市区域执行"
            
        if item_name is None:
            # 用于动作空间检查
            # 理论上只要有钱就可以买东西，这里简单判定金钱>0
            ok = self.avatar.magic_stone > 0
            return (ok, "" if ok else "身无分文")

        obj, obj_type, display_name = self._resolve_obj(item_name)
        if obj_type == "unknown":
            return False, f"未知物品: {item_name}"

        # 检查价格
        price = prices.get_buying_price(obj, self.avatar)
        if self.avatar.magic_stone < price:
            return False, f"灵石不足 (需要 {price})"

        # 丹药特殊限制
        if obj_type == "elixir":
            elixir: Elixir = obj
            
            # 境界限制
            if elixir.realm > self.avatar.cultivation_progress.realm:
                return False, f"境界不足，无法承受药力 ({elixir.realm.value})"
                
            # 耐药性/生效中检查
            for consumed in self.avatar.elixirs:
                if consumed.elixir.id == elixir.id:
                    if not consumed.is_completely_expired(int(self.world.month_stamp)):
                        return False, "药效尚存，无法重复服用"
                        
        return True, ""

    def _execute(self, item_name: str) -> None:
        obj, obj_type, display_name = self._resolve_obj(item_name)
        if obj_type == "unknown":
            return
            
        price = prices.get_buying_price(obj, self.avatar)
        self.avatar.magic_stone -= price
        
        # 交付
        if obj_type == "elixir":
            self.avatar.consume_elixir(obj)
        elif obj_type == "item":
            self.avatar.add_item(obj)

    def start(self, item_name: str) -> Event:
        obj, obj_type, display_name = self._resolve_obj(item_name)
        
        action_desc = "购买并服用了" if obj_type == "elixir" else "购买了"
        price = prices.get_buying_price(obj, self.avatar) if obj else 0
        
        return Event(
            self.world.month_stamp, 
            f"{self.avatar.name} 在城镇花费 {price} 灵石{action_desc} {display_name}", 
            related_avatars=[self.avatar.id]
        )

    async def finish(self, item_name: str) -> list[Event]:
        return []

