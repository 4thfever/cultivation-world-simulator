import pytest
import copy
from unittest.mock import MagicMock, patch

from src.classes.prices import prices, Prices
from src.classes.cultivation import Realm
from src.classes.item import items_by_id
from src.classes.weapon import weapons_by_id, Weapon, get_random_weapon_by_realm
from src.classes.auxiliary import auxiliaries_by_id, Auxiliary, get_random_auxiliary_by_realm


class TestPrices:
    """价格系统测试"""
    
    def test_item_prices_by_realm(self):
        """测试材料价格按境界递增"""
        assert prices.ITEM_PRICES[Realm.Qi_Refinement] < prices.ITEM_PRICES[Realm.Foundation_Establishment]
        assert prices.ITEM_PRICES[Realm.Foundation_Establishment] < prices.ITEM_PRICES[Realm.Core_Formation]
        assert prices.ITEM_PRICES[Realm.Core_Formation] < prices.ITEM_PRICES[Realm.Nascent_Soul]

    def test_weapon_prices_by_realm(self):
        """测试兵器价格按境界递增"""
        assert prices.WEAPON_PRICES[Realm.Qi_Refinement] < prices.WEAPON_PRICES[Realm.Foundation_Establishment]
        assert prices.WEAPON_PRICES[Realm.Foundation_Establishment] < prices.WEAPON_PRICES[Realm.Core_Formation]
        assert prices.WEAPON_PRICES[Realm.Core_Formation] < prices.WEAPON_PRICES[Realm.Nascent_Soul]

    def test_auxiliary_prices_by_realm(self):
        """测试辅助装备价格按境界递增"""
        assert prices.AUXILIARY_PRICES[Realm.Qi_Refinement] < prices.AUXILIARY_PRICES[Realm.Foundation_Establishment]
        assert prices.AUXILIARY_PRICES[Realm.Foundation_Establishment] < prices.AUXILIARY_PRICES[Realm.Core_Formation]
        assert prices.AUXILIARY_PRICES[Realm.Core_Formation] < prices.AUXILIARY_PRICES[Realm.Nascent_Soul]

    def test_get_price_for_item(self):
        """测试 get_price 对 Item 类型的分发"""
        if not items_by_id:
            pytest.skip("No items available in config")
        
        item = next(iter(items_by_id.values()))
        price = prices.get_price(item)
        expected = prices.get_item_price(item)
        assert price == expected
        assert price == prices.ITEM_PRICES[item.realm]

    def test_get_price_for_weapon(self):
        """测试 get_price 对 Weapon 类型的分发"""
        if not weapons_by_id:
            pytest.skip("No weapons available in config")
        
        weapon = next(iter(weapons_by_id.values()))
        price = prices.get_price(weapon)
        expected = prices.get_weapon_price(weapon)
        assert price == expected
        assert price == prices.WEAPON_PRICES[weapon.realm]

    def test_get_price_for_auxiliary(self):
        """测试 get_price 对 Auxiliary 类型的分发"""
        if not auxiliaries_by_id:
            pytest.skip("No auxiliaries available in config")
        
        aux = next(iter(auxiliaries_by_id.values()))
        price = prices.get_price(aux)
        expected = prices.get_auxiliary_price(aux)
        assert price == expected
        assert price == prices.AUXILIARY_PRICES[aux.realm]

    def test_weapon_more_expensive_than_item(self):
        """测试同境界下兵器比材料贵"""
        for realm in Realm:
            if realm in prices.ITEM_PRICES and realm in prices.WEAPON_PRICES:
                assert prices.WEAPON_PRICES[realm] >= prices.ITEM_PRICES[realm]


class TestAvatarSell:
    """Avatar 出售接口测试"""

    def test_sell_item_basic(self, dummy_avatar):
        """测试基础材料出售"""
        if not items_by_id:
            pytest.skip("No items available in config")
        
        item = next(iter(items_by_id.values()))
        dummy_avatar.items = {}  # 清空背包
        dummy_avatar.magic_stone.value = 0
        
        # 添加物品
        dummy_avatar.add_item(item, 5)
        assert dummy_avatar.get_item_quantity(item) == 5
        
        # 出售3个
        gained = dummy_avatar.sell_item(item, 3)
        
        expected_price = prices.get_item_price(item) * 3
        assert gained == expected_price
        assert dummy_avatar.magic_stone.value == expected_price
        assert dummy_avatar.get_item_quantity(item) == 2

    def test_sell_item_insufficient(self, dummy_avatar):
        """测试出售物品数量不足"""
        if not items_by_id:
            pytest.skip("No items available in config")
        
        item = next(iter(items_by_id.values()))
        dummy_avatar.items = {}
        dummy_avatar.magic_stone.value = 100
        
        dummy_avatar.add_item(item, 2)
        
        # 尝试出售5个（只有2个）
        gained = dummy_avatar.sell_item(item, 5)
        
        assert gained == 0
        assert dummy_avatar.magic_stone.value == 100  # 没有变化
        assert dummy_avatar.get_item_quantity(item) == 2  # 物品未减少

    def test_sell_weapon(self, dummy_avatar):
        """测试出售兵器"""
        weapon = get_random_weapon_by_realm(Realm.Foundation_Establishment)
        if not weapon:
            pytest.skip("No Foundation Establishment weapons available")
        
        dummy_avatar.magic_stone.value = 0
        
        gained = dummy_avatar.sell_weapon(weapon)
        
        expected = prices.get_weapon_price(weapon)
        assert gained == expected
        assert dummy_avatar.magic_stone.value == expected

    def test_sell_auxiliary(self, dummy_avatar):
        """测试出售辅助装备"""
        aux = get_random_auxiliary_by_realm(Realm.Core_Formation)
        if not aux:
            pytest.skip("No Core Formation auxiliaries available")
        
        dummy_avatar.magic_stone.value = 0
        
        gained = dummy_avatar.sell_auxiliary(aux)
        
        expected = prices.get_auxiliary_price(aux)
        assert gained == expected
        assert dummy_avatar.magic_stone.value == expected

    def test_sell_with_price_multiplier(self, dummy_avatar):
        """测试出售价格倍率效果"""
        if not items_by_id:
            pytest.skip("No items available in config")
        
        item = next(iter(items_by_id.values()))
        dummy_avatar.items = {}
        dummy_avatar.magic_stone.value = 0
        dummy_avatar.add_item(item, 1)
        
        base_price = prices.get_item_price(item)
        
        # 设置 20% 加成 - patch 内部方法
        with patch.object(dummy_avatar, '_get_sell_multiplier', return_value=1.2):
            gained = dummy_avatar.sell_item(item, 1)
        
        expected = int(base_price * 1.2)
        assert gained == expected
        assert dummy_avatar.magic_stone.value == expected

    def test_sell_weapon_with_multiplier(self, dummy_avatar):
        """测试出售兵器时价格倍率生效"""
        weapon = get_random_weapon_by_realm(Realm.Qi_Refinement)
        if not weapon:
            pytest.skip("No Qi Refinement weapons available")
        
        dummy_avatar.magic_stone.value = 0
        base_price = prices.get_weapon_price(weapon)
        
        # 设置 50% 加成 - patch 内部方法
        with patch.object(dummy_avatar, '_get_sell_multiplier', return_value=1.5):
            gained = dummy_avatar.sell_weapon(weapon)
        
        expected = int(base_price * 1.5)
        assert gained == expected

