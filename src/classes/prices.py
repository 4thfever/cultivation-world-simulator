from src.classes.cultivation import Realm
from src.classes.item import Item

class Prices:
    """
    价格体系。
    刚开始我只准备做一个比较简单的价格体系，之后可能复杂化。
    目前是所有的城镇都可以出售材料，同时这些材料的价格是固定的，并且全局公开。
    价格只和对应的realm绑定。
    """
    def __init__(self):
        self.realm_to_prices = {
            Realm.Qi_Refinement: 10,
            Realm.Foundation_Establishment: 50,
            Realm.Core_Formation: 100,
            Realm.Nascent_Soul: 200,
        }

    def get_price(self, item: Item) -> int:
        return self.realm_to_prices[item.realm]

# 预先创建全局价格实例，供全局使用
prices = Prices()