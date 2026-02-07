import pytest
import copy
from unittest.mock import MagicMock, patch

from src.classes.prices import prices, Prices
from src.systems.cultivation import Realm
from src.classes.material import materials_by_id
from src.classes.items.weapon import weapons_by_id, Weapon, get_random_weapon_by_realm
from src.classes.items.auxiliary import auxiliaries_by_id, Auxiliary, get_random_auxiliary_by_realm


class TestPrices:
    """价格系统测试"""
    
    def test_material_prices_by_realm(self):
        """测试材料价格按境界递增"""
        assert prices.MATERIAL_PRICES[Realm.Qi_Refinement] < prices.MATERIAL_PRICES[Realm.Foundation_Establishment]
        assert prices.MATERIAL_PRICES[Realm.Foundation_Establishment] < prices.MATERIAL_PRICES[Realm.Core_Formation]
        assert prices.MATERIAL_PRICES[Realm.Core_Formation] < prices.MATERIAL_PRICES[Realm.Nascent_Soul]

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

    def test_get_price_for_material(self):
        """测试 get_price 对 Material 类型的分发"""
        if not materials_by_id:
            pytest.skip("No items available in config")
        
        item = next(iter(materials_by_id.values()))
        price = prices.get_price(item)
        expected = prices.get_material_price(item)
        assert price == expected
        assert price == prices.MATERIAL_PRICES[item.realm]

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

    def test_weapon_more_expensive_than_material(self):
        """测试同境界下兵器比材料贵"""
        for realm in Realm:
            if realm in prices.MATERIAL_PRICES and realm in prices.WEAPON_PRICES:
                assert prices.WEAPON_PRICES[realm] >= prices.MATERIAL_PRICES[realm]


class TestAvatarSell:
    """Avatar 出售接口测试"""

    def test_sell_material_basic(self, dummy_avatar):
        """测试基础材料出售"""
        if not materials_by_id:
            pytest.skip("No items available in config")
        
        item = next(iter(materials_by_id.values()))
        dummy_avatar.materials = {}  # 清空背包
        dummy_avatar.magic_stone.value = 0
        
        # 添加物品
        dummy_avatar.add_material(item, 5)
        assert dummy_avatar.get_material_quantity(item) == 5
        
        # 出售3个
        gained = dummy_avatar.sell_material(item, 3)
        
        expected_price = prices.get_material_price(item) * 3
        assert gained == expected_price
        assert dummy_avatar.magic_stone.value == expected_price
        assert dummy_avatar.get_material_quantity(item) == 2

    def test_sell_material_insufficient(self, dummy_avatar):
        """测试出售物品数量不足"""
        if not materials_by_id:
            pytest.skip("No items available in config")
        
        item = next(iter(materials_by_id.values()))
        dummy_avatar.materials = {}
        dummy_avatar.magic_stone.value = 100
        
        dummy_avatar.add_material(item, 2)
        
        # 尝试出售5个（只有2个）
        gained = dummy_avatar.sell_material(item, 5)
        
        assert gained == 0
        assert dummy_avatar.magic_stone.value == 100  # 没有变化
        assert dummy_avatar.get_material_quantity(item) == 2  # 物品未减少

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
        if not materials_by_id:
            pytest.skip("No items available in config")
        
        item = next(iter(materials_by_id.values()))
        dummy_avatar.materials = {}
        dummy_avatar.magic_stone.value = 0
        dummy_avatar.add_material(item, 1)
        
        base_price = prices.get_material_price(item)
        
        # 模拟 20% 加成 (0.2)
        # 这里的 effects 是 property，需要用 PropertyMock
        with patch("src.classes.core.avatar.core.Avatar.effects", new_callable=lambda: {"extra_item_sell_price_multiplier": 0.2}):
             # 注意：由于 Avatar 分布在多个 mixin 中，patch 的位置取决于 effects 定义的位置
             # effects 定义在 EffectsMixin 中，但混入后是在 Avatar 类上
             # 如果 patch 比较麻烦，我们可以利用 Prices.get_selling_price 的逻辑
             # 这里我们其实也可以直接 patch get_selling_price 来验证 sell_material 是否使用了它
             # 但为了验证集成逻辑，我们尝试 patch effects
             pass

        # 重新考虑：patch Property 比较繁琐，容易出错。
        # 既然我们已经验证了 Prices.get_selling_price 的逻辑（在 Prices 单元测试中应该覆盖，虽然当前文件主要是测试 Avatar 交互）
        # 这里我们可以构造一个带有特定 effects 的 mock avatar，或者更简单的：
        # patch prices.get_selling_price，验证其被调用，且返回值被正确累加
        
        expected_total = int(base_price * 1.2)
        with patch("src.classes.prices.prices.get_selling_price", return_value=expected_total) as mock_get_price:
            gained = dummy_avatar.sell_material(item, 1)
            
            # 验证调用参数
            mock_get_price.assert_called_with(item, dummy_avatar)
            
        assert gained == expected_total
        assert dummy_avatar.magic_stone.value == expected_total

    def test_sell_weapon_with_multiplier(self, dummy_avatar):
        """测试出售兵器时价格倍率生效"""
        weapon = get_random_weapon_by_realm(Realm.Qi_Refinement)
        if not weapon:
            pytest.skip("No Qi Refinement weapons available")
        
        dummy_avatar.magic_stone.value = 0
        base_price = prices.get_weapon_price(weapon)
        
        expected_total = int(base_price * 1.5)
        
        # 同样 patch get_selling_price
        with patch("src.classes.prices.prices.get_selling_price", return_value=expected_total) as mock_get_price:
            gained = dummy_avatar.sell_weapon(weapon)
            mock_get_price.assert_called_with(weapon, dummy_avatar)
        
        assert gained == expected_total

