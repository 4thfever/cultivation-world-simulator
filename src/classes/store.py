from collections import defaultdict
from typing import Any, List

from src.utils.resolution import resolve_query
from src.classes.elixir import Elixir
from src.classes.weapon import Weapon
from src.classes.auxiliary import Auxiliary
from src.classes.prices import prices

class StoreMixin:
    """
    商店功能混入类
    赋予区域售卖物品的能力
    """
    
    def init_store(self, item_names: list[str]):
        """
        初始化商店物品
        :param item_names: 物品名称列表
        """
        self.store_items = []
        if not item_names:
            return

        for name in item_names:
            # 期望类型：丹药、武器、辅助
            res = resolve_query(name, expected_types=[Elixir, Weapon, Auxiliary])
            if res.is_valid and res.obj:
                self.store_items.append(res.obj)
    
    def get_store_info(self) -> str:
        """
        获取商店信息描述
        例如：交易：练气剑、练气刀（100灵石）；练气破境丹（50灵石）
        """
        # 如果没有初始化或者没有物品
        if not hasattr(self, 'store_items') or not self.store_items:
            return ""
            
        # 按价格分组
        items_by_price = defaultdict(list)
        for item in self.store_items:
            # 获取该物品的标准购买价格（作为标价，买家为 None）
            price = prices.get_buying_price(item, None)
            items_by_price[price].append(item.name)
            
        if not items_by_price:
            return ""

        # 格式化输出
        parts = []
        # 按价格从低到高排序
        for price in sorted(items_by_price.keys()):
            names = items_by_price[price]
            # 去重并保持顺序 (Python 3.7+ dict key insertion order)
            unique_names = list(dict.fromkeys(names))
            names_str = "、".join(unique_names)
            parts.append(f"{names_str}（{price}灵石）")
            
        return "交易：" + "；".join(parts)

    def is_selling(self, item_name: str) -> bool:
        """
        检查商店是否出售该物品
        """
        if not hasattr(self, 'store_items'):
            return False
        
        # 简单的名字匹配 (Assuming item.name is what we look for)
        # 如果需要更严格的匹配（如 normalized name），需要在这里处理，
        # 但通常 resolve_query 解析出的 obj.name 是标准名。
        return any(item.name == item_name for item in self.store_items)
