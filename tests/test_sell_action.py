import pytest
from unittest.mock import patch
from src.classes.action.sell import Sell
from src.classes.environment.region import CityRegion
from tests.conftest import create_test_material # Explicit import if needed

def test_sell_material_success(avatar_in_city, mock_item_data):
    """测试出售普通材料成功"""
    materials_mock = mock_item_data["materials"]
    weapons_mock = mock_item_data["weapons"]
    auxiliaries_mock = mock_item_data["auxiliaries"]
    test_material = mock_item_data["obj_material"]
    
    # 给角色添加材料
    avatar_in_city.add_material(test_material, quantity=5)
    
    with patch("src.utils.resolution.materials_by_name", materials_mock), \
         patch("src.utils.resolution.weapons_by_name", weapons_mock), \
         patch("src.utils.resolution.auxiliaries_by_name", auxiliaries_mock):
        
        action = Sell(avatar_in_city, avatar_in_city.world)
        
        # 1. 检查是否可出售
        can_start, reason = action.can_start("铁矿石")
        assert can_start is True
        
        # 2. 执行出售
        # 练气期材料基础价格 10，卖出倍率默认为 1.0 -> 单价 10
        # 卖出全部 5 个 -> 总价 50
        initial_money = avatar_in_city.magic_stone
        expected_income = 50
        
        action._execute("铁矿石")
        
        # 3. 验证结果
        assert avatar_in_city.magic_stone == initial_money + expected_income
        assert avatar_in_city.get_material_quantity(test_material) == 0

def test_sell_weapon_success(avatar_in_city, mock_item_data):
    """测试出售当前兵器成功"""
    materials_mock = mock_item_data["materials"]
    weapons_mock = mock_item_data["weapons"]
    auxiliaries_mock = mock_item_data["auxiliaries"]
    test_weapon = mock_item_data["obj_weapon"]
    
    # 装备兵器
    avatar_in_city.weapon = test_weapon
    
    with patch("src.utils.resolution.materials_by_name", materials_mock), \
         patch("src.utils.resolution.weapons_by_name", weapons_mock), \
         patch("src.utils.resolution.auxiliaries_by_name", auxiliaries_mock):
        
        action = Sell(avatar_in_city, avatar_in_city.world)
        
        # 1. 检查是否可出售
        can_start, reason = action.can_start("青云剑")
        assert can_start is True
        
        # 2. 执行出售
        # 练气期兵器基础价格 150 (refer to src/classes/prices.py)
        # 卖出加成默认为 0.0 -> 单价 150
        expected_income = 150 
        
        initial_money = avatar_in_city.magic_stone
        action._execute("青云剑")
        
        # 3. 验证结果
        assert avatar_in_city.magic_stone == initial_money + expected_income
        assert avatar_in_city.weapon is None

def test_sell_auxiliary_success(avatar_in_city, mock_item_data):
    """测试出售当前法宝成功"""
    materials_mock = mock_item_data["materials"]
    weapons_mock = mock_item_data["weapons"]
    auxiliaries_mock = mock_item_data["auxiliaries"]
    test_auxiliary = mock_item_data["obj_auxiliary"]
    
    # 装备法宝
    avatar_in_city.auxiliary = test_auxiliary
    
    with patch("src.utils.resolution.materials_by_name", materials_mock), \
         patch("src.utils.resolution.weapons_by_name", weapons_mock), \
         patch("src.utils.resolution.auxiliaries_by_name", auxiliaries_mock):
        
        action = Sell(avatar_in_city, avatar_in_city.world)
        
        can_start, reason = action.can_start("聚灵珠")
        assert can_start is True
        
        # 练气期辅助装备基础价格 150
        expected_income = 150
        
        action._execute("聚灵珠")
        
        assert avatar_in_city.magic_stone == 1000 + expected_income
        assert avatar_in_city.auxiliary is None

def test_sell_fail_not_in_city(dummy_avatar, mock_item_data):
    """测试不在城市无法出售"""
    materials_mock = mock_item_data["materials"]
    weapons_mock = mock_item_data["weapons"]
    auxiliaries_mock = mock_item_data["auxiliaries"]
    test_material = mock_item_data["obj_material"]
    
    # 确保不在城市
    assert not isinstance(dummy_avatar.tile.region, CityRegion)
    dummy_avatar.add_material(test_material, 1)
    
    with patch("src.utils.resolution.materials_by_name", materials_mock), \
         patch("src.utils.resolution.weapons_by_name", weapons_mock), \
         patch("src.utils.resolution.auxiliaries_by_name", auxiliaries_mock):
        
        action = Sell(dummy_avatar, dummy_avatar.world)
        can_start, reason = action.can_start("铁矿石")
        
        assert can_start is False
        assert "仅能在城市" in reason

def test_sell_fail_no_item(avatar_in_city, mock_item_data):
    """测试未持有该材料"""
    materials_mock = mock_item_data["materials"]
    weapons_mock = mock_item_data["weapons"]
    auxiliaries_mock = mock_item_data["auxiliaries"]
    
    # 背包为空，无装备 (fixture default)
    
    with patch("src.utils.resolution.materials_by_name", materials_mock), \
         patch("src.utils.resolution.weapons_by_name", weapons_mock), \
         patch("src.utils.resolution.auxiliaries_by_name", auxiliaries_mock):
        
        action = Sell(avatar_in_city, avatar_in_city.world)
        can_start, reason = action.can_start("铁矿石")
        
        assert can_start is False
        assert "未持有材料" in reason

def test_sell_fail_unknown_name(avatar_in_city, mock_item_data):
    """测试未知物品名称"""
    materials_mock = mock_item_data["materials"]
    weapons_mock = mock_item_data["weapons"]
    auxiliaries_mock = mock_item_data["auxiliaries"]
    
    with patch("src.utils.resolution.materials_by_name", materials_mock), \
         patch("src.utils.resolution.weapons_by_name", weapons_mock), \
         patch("src.utils.resolution.auxiliaries_by_name", auxiliaries_mock):
        
        action = Sell(avatar_in_city, avatar_in_city.world)
        can_start, reason = action.can_start("不存在的神器")
        
        assert can_start is False
        assert "未持有物品/装备" in reason

def test_sell_priority(avatar_in_city, mock_item_data):
    """测试优先级：同名时优先卖身上装备（根据 resolution 优先级）"""
    materials_mock = mock_item_data["materials"]
    weapons_mock = mock_item_data["weapons"]
    auxiliaries_mock = mock_item_data["auxiliaries"]
    test_weapon = mock_item_data["obj_weapon"]
    
    # 构造一个同名的材料
    # 需要从 conftest 导入
    from src.systems.cultivation import Realm
    fake_sword_material = create_test_material("青云剑", Realm.Qi_Refinement)
    
    # 修改 mock，让 "青云剑" 在 materials 里也能找到
    materials_mock["青云剑"] = fake_sword_material
    
    # 角色同时拥有该材料和该兵器
    avatar_in_city.add_material(fake_sword_material, 1)
    avatar_in_city.weapon = test_weapon # name也是 "青云剑"
    
    with patch("src.utils.resolution.materials_by_name", materials_mock), \
         patch("src.utils.resolution.weapons_by_name", weapons_mock), \
         patch("src.utils.resolution.auxiliaries_by_name", auxiliaries_mock):
        
        action = Sell(avatar_in_city, avatar_in_city.world)
        
        # 执行出售
        action._execute("青云剑")
        
        # 断言：兵器没了，材料还在。
        assert avatar_in_city.weapon is None
        assert avatar_in_city.get_material_quantity(fake_sword_material) == 1
