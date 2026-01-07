import pytest
from unittest.mock import patch
from src.classes.action.buy import Buy
from src.classes.region import CityRegion
from src.classes.elixir import ElixirType, ConsumedElixir
from src.classes.cultivation import Realm
from tests.conftest import create_test_weapon # Explicitly import if needed, or rely on conftest being auto-loaded (it is)

def test_buy_item_success(avatar_in_city, mock_item_data):
    """测试购买普通材料成功"""
    elixirs_mock = mock_item_data["elixirs"]
    materials_mock = mock_item_data["materials"]
    test_material = mock_item_data["obj_material"]
    
    with patch("src.utils.resolution.elixirs_by_name", elixirs_mock), \
         patch("src.utils.resolution.materials_by_name", materials_mock):
        
        action = Buy(avatar_in_city, avatar_in_city.world)
        
        # 1. 检查是否可购买
        can_start, reason = action.can_start("铁矿石")
        assert can_start is True
        
        # 2. 执行购买
        initial_money = avatar_in_city.magic_stone
        # 练气期材料基础价格 10，倍率 1.5 -> 15
        expected_price = int(10 * 1.5)
        
        action._execute("铁矿石")
        
        # 3. 验证结果
        assert avatar_in_city.magic_stone == initial_money - expected_price
        assert avatar_in_city.get_material_quantity(test_material) == 1

def test_buy_elixir_success(avatar_in_city, mock_item_data):
    """测试购买并服用丹药成功"""
    elixirs_mock = mock_item_data["elixirs"]
    materials_mock = mock_item_data["materials"]
    test_elixir = mock_item_data["obj_elixir"]
    
    with patch("src.utils.resolution.elixirs_by_name", elixirs_mock), \
         patch("src.utils.resolution.materials_by_name", materials_mock):
        
        action = Buy(avatar_in_city, avatar_in_city.world)
        
        can_start, reason = action.can_start("聚气丹")
        assert can_start is True
        
        initial_money = avatar_in_city.magic_stone
        expected_price = int(test_elixir.price * 1.5)
        
        # 模拟服用丹药的行为
        action._execute("聚气丹")
        
        assert avatar_in_city.magic_stone == initial_money - expected_price
        # 背包里不应该有丹药
        assert len(avatar_in_city.materials) == 0 
        # 已服用列表应该有
        assert len(avatar_in_city.elixirs) == 1
        assert avatar_in_city.elixirs[0].elixir.name == "聚气丹"

def test_buy_fail_not_in_city(dummy_avatar, mock_item_data):
    """测试不在城市无法购买"""
    elixirs_mock = mock_item_data["elixirs"]
    materials_mock = mock_item_data["materials"]
    
    # 确保不在城市 (dummy_avatar 默认在 (0,0) PLAIN)
    assert not isinstance(dummy_avatar.tile.region, CityRegion)
    
    with patch("src.utils.resolution.elixirs_by_name", elixirs_mock), \
         patch("src.utils.resolution.materials_by_name", materials_mock):
        
        action = Buy(dummy_avatar, dummy_avatar.world)
        can_start, reason = action.can_start("铁矿石")
        
        assert can_start is False
        assert "仅能在城市" in reason

def test_buy_fail_no_money(avatar_in_city, mock_item_data):
    """测试没钱无法购买"""
    elixirs_mock = mock_item_data["elixirs"]
    materials_mock = mock_item_data["materials"]
    
    avatar_in_city.magic_stone = 0 # 没钱
    
    with patch("src.utils.resolution.elixirs_by_name", elixirs_mock), \
         patch("src.utils.resolution.materials_by_name", materials_mock):
        
        action = Buy(avatar_in_city, avatar_in_city.world)
        can_start, reason = action.can_start("铁矿石")
        
        assert can_start is False
        assert "灵石不足" in reason

def test_buy_fail_unknown_item(avatar_in_city, mock_item_data):
    """测试未知物品"""
    elixirs_mock = mock_item_data["elixirs"]
    materials_mock = mock_item_data["materials"]
    
    with patch("src.utils.resolution.elixirs_by_name", elixirs_mock), \
         patch("src.utils.resolution.materials_by_name", materials_mock):
        
        action = Buy(avatar_in_city, avatar_in_city.world)
        can_start, reason = action.can_start("不存在的东西")
        
        assert can_start is False
        assert "未知物品" in reason

def test_buy_elixir_fail_high_level_restricted(avatar_in_city, mock_item_data):
    """测试购买高阶丹药被限制"""
    elixirs_mock = mock_item_data["elixirs"]
    materials_mock = mock_item_data["materials"]
    high_level_elixir = mock_item_data["obj_high_elixir"]
    
    # 给予足够金钱
    avatar_in_city.magic_stone = 10000
    
    # 角色是练气期，尝试买筑基期丹药
    assert avatar_in_city.cultivation_progress.realm == Realm.Qi_Refinement
    assert high_level_elixir.realm == Realm.Foundation_Establishment
    
    with patch("src.utils.resolution.elixirs_by_name", elixirs_mock), \
         patch("src.utils.resolution.materials_by_name", materials_mock):
        
        action = Buy(avatar_in_city, avatar_in_city.world)
        can_start, reason = action.can_start("筑基丹")
        
        assert can_start is False
        assert "当前仅开放练气期丹药购买" in reason

def test_buy_elixir_fail_duplicate_active(avatar_in_city, mock_item_data):
    """测试药效尚存无法重复购买"""
    elixirs_mock = mock_item_data["elixirs"]
    materials_mock = mock_item_data["materials"]
    test_elixir = mock_item_data["obj_elixir"]
    
    # 先服用一个
    consumed = ConsumedElixir(test_elixir, int(avatar_in_city.world.month_stamp))
    
    avatar_in_city.elixirs.append(consumed)
    
    with patch("src.utils.resolution.elixirs_by_name", elixirs_mock), \
         patch("src.utils.resolution.materials_by_name", materials_mock):
        
        action = Buy(avatar_in_city, avatar_in_city.world)
        can_start, reason = action.can_start("聚气丹")
        
        assert can_start is False
        assert "药效尚存" in reason

def test_buy_weapon_trade_in(avatar_in_city, mock_item_data):
    """测试购买新武器时自动卖出旧武器"""
    # 这里需要构造一个旧武器，mock_item_data里只有一套新武器
    from tests.conftest import create_test_weapon
    from src.classes.weapon import Weapon, WeaponType
    
    elixirs_mock = mock_item_data["elixirs"]
    materials_mock = mock_item_data["materials"]
    new_weapon = mock_item_data["obj_weapon"]
    
    # 手动添加武器到 materials_mock (Buy logic looks up weapons in materials too? Or just assumes unique names?)
    # Buy code checks `get_item_by_name` which checks all dicts.
    # In test_buy_action we only mocked elixirs and materials. 
    # Let's ensure '青云剑' is findable. Ideally it should be in weapons_by_name but maybe Buy logic is flexible?
    # Original test put it in materials_mock["青云剑"] = new_weapon. Let's follow that pattern for now or better: mock weapons too.
    
    # Wait, original test: materials_mock["青云剑"] = new_weapon
    # But `src.utils.resolution.get_item_by_name` checks materials, weapons, auxiliaries.
    # Let's do it properly by mocking weapons_by_name as well if possible, or just stick to materials for simplicity if Buy allows.
    # Buy uses `get_item_by_name`.
    
    materials_mock["青云剑"] = new_weapon
    
    # 构造旧武器
    old_weapon = create_test_weapon("铁剑", Realm.Qi_Refinement, weapon_id=199)
    old_weapon.effects = {'atk': 1}
    
    # 装备旧武器
    avatar_in_city.change_weapon(old_weapon)
    assert avatar_in_city.weapon == old_weapon
    
    initial_money = avatar_in_city.magic_stone
    
    # 价格计算
    # 练气期 Weapon Base Price = 10
    # 买入: 10 * 1.5 = 15
    buy_cost = 15
    # 卖出: 10 * 1.0 = 10
    sell_refund = 10
    
    expected_money = initial_money - buy_cost + sell_refund
    
    with patch("src.utils.resolution.elixirs_by_name", elixirs_mock), \
         patch("src.utils.resolution.materials_by_name", materials_mock):
         
        action = Buy(avatar_in_city, avatar_in_city.world)
        
        # 验证 Event 描述
        event = action.start("青云剑")
        assert "青云剑" in event.content
        assert "铁剑" in event.content
        assert "折价售出" in event.content
        
        # 执行购买
        action._execute("青云剑")
        
        assert avatar_in_city.weapon.name == "青云剑"
        assert avatar_in_city.weapon != old_weapon
        assert avatar_in_city.magic_stone == expected_money
