from __future__ import annotations

from src.classes.action import InstantAction
from src.classes.event import Event
from src.classes.region import CityRegion
from src.classes.item import items_by_name
from src.classes.prices import prices
from src.classes.normalize import normalize_item_name


class SellItems(InstantAction):
    """
    在城镇出售指定名称的物品，一次性卖出持有的全部数量。
    收益为 item_price * item_num，动作耗时1个月。
    """

    COMMENT = "在城镇出售持有的某类物品的全部"
    DOABLES_REQUIREMENTS = "在城镇且背包非空"
    PARAMS = {"item_name": "str"}

    def _execute(self, item_name: str) -> None:
        region = self.avatar.tile.region
        if not isinstance(region, CityRegion):
            return

        # 规范化物品名称（去除境界等附加信息）
        normalized_name = normalize_item_name(item_name)
        
        # 找到物品
        item = items_by_name.get(normalized_name)
        if item is None:
            return

        # 检查持有数量
        quantity = self.avatar.get_item_quantity(item)
        if quantity <= 0:
            return

        # 计算价格并结算
        price_per = prices.get_price(item)
        base_total_gain = price_per * quantity
        
        # 应用出售价格倍率加成
        price_multiplier_raw = self.avatar.effects.get("extra_item_sell_price_multiplier", 0.0)
        price_multiplier = 1.0 + float(price_multiplier_raw or 0.0)
        total_gain = int(base_total_gain * price_multiplier)

        # 扣除物品并增加灵石
        removed = self.avatar.remove_item(item, quantity)
        if not removed:
            return

        self.avatar.magic_stone = self.avatar.magic_stone + total_gain

    def can_start(self, item_name: str | None = None) -> tuple[bool, str]:
        region = self.avatar.tile.region
        if not isinstance(region, CityRegion):
            return False, "仅能在城市区域执行"
        if item_name is None:
            # 用于动作空间：只要背包非空即可
            ok = bool(self.avatar.items)
            return (ok, "" if ok else "背包为空，无可出售物品")
        
        # 规范化物品名称
        normalized_name = normalize_item_name(item_name)
        item = items_by_name.get(normalized_name)
        if item is None:
            return False, f"未知物品: {item_name}"
        ok = self.avatar.get_item_quantity(item) > 0
        return (ok, "" if ok else "该物品数量为0")

    def start(self, item_name: str) -> Event:
        # 规范化物品名称用于显示（与执行逻辑一致）
        normalized_name = normalize_item_name(item_name)
        # 尝试获取标准物品名（如果存在）
        item = items_by_name.get(normalized_name)
        display_name = item.name if item is not None else normalized_name
        return Event(self.world.month_stamp, f"{self.avatar.name} 在城镇出售 {display_name}", related_avatars=[self.avatar.id])

    # InstantAction 已实现 step 完成

    def finish(self, item_name: str) -> list[Event]:
        return []


