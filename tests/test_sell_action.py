import pytest
from unittest.mock import patch, MagicMock
from src.classes.action.sell import Sell
from src.classes.region import CityRegion
from src.classes.item import Item
from src.classes.weapon import Weapon
from src.classes.auxiliary import Auxiliary
from src.classes.cultivation import Realm
from src.classes.tile import Tile, TileType
from src.classes.weapon_type import WeaponType

# 创建测试用的对象 helper
def create_test_item(name, realm, item_id=101):
    return Item(
        id=item_id,
        name=name,
        desc="测试物品",
        realm=realm
    )

def create_test_weapon(name, realm, weapon_id=201):
    return Weapon(
        id=weapon_id,
        name=name,
        weapon_type=WeaponType.SWORD,
        realm=realm,
        desc="测试兵器",
        effects={},
        effect_desc=""
    )

def create_test_auxiliary(name, realm, aux_id=301):
    return Auxiliary(
        id=aux_id,
        name=name,
        realm=realm,
        desc="测试法宝",
        effects={},
        effect_desc=""
    )

@pytest.fixture
def avatar_in_city(dummy_avatar):
    """
    修改 dummy_avatar，使其位于城市中，并给予初始状态
    """
    city_region = CityRegion(id=1, name="TestCity", desc="测试城市")
    tile = Tile(0, 0, TileType.CITY)
    tile.region = city_region
    
    dummy_avatar.tile = tile
    dummy_avatar.magic_stone = 0
    dummy_avatar.items = {}
    dummy_avatar.weapon = None
    dummy_avatar.auxiliary = None
    
    return dummy_avatar

@pytest.fixture
def mock_sell_objects():
    """
    Mock items_by_name 并提供测试对象
    """
    test_item = create_test_item("铁矿石", Realm.Qi_Refinement)
    test_weapon = create_test_weapon("青云剑", Realm.Qi_Refinement)
    test_auxiliary = create_test_auxiliary("聚灵珠", Realm.Qi_Refinement)

    items_mock = {
        "铁矿石": test_item
    }
    
    return items_mock, test_item, test_weapon, test_auxiliary

def test_sell_item_success(avatar_in_city, mock_sell_objects):
    """测试出售普通物品成功"""
    items_mock, test_item, _, _ = mock_sell_objects
    
    # 给角色添加物品
    avatar_in_city.add_item(test_item, quantity=5)
    
    with patch("src.classes.action.sell.items_by_name", items_mock):
        action = Sell(avatar_in_city, avatar_in_city.world)
        
        # 1. 检查是否可出售
        can_start, reason = action.can_start("铁矿石")
        assert can_start is True
        
        # 2. 执行出售
        # 练气期物品基础价格 10，卖出倍率默认为 1.0 -> 单价 10
        # 卖出全部 5 个 -> 总价 50
        initial_money = avatar_in_city.magic_stone
        expected_income = 50
        
        action._execute("铁矿石")
        
        # 3. 验证结果
        assert avatar_in_city.magic_stone == initial_money + expected_income
        assert avatar_in_city.get_item_quantity(test_item) == 0

def test_sell_weapon_success(avatar_in_city, mock_sell_objects):
    """测试出售当前兵器成功"""
    items_mock, _, test_weapon, _ = mock_sell_objects
    
    # 装备兵器
    avatar_in_city.weapon = test_weapon
    
    with patch("src.classes.action.sell.items_by_name", items_mock):
        action = Sell(avatar_in_city, avatar_in_city.world)
        
        # 1. 检查是否可出售
        can_start, reason = action.can_start("青云剑")
        assert can_start is True
        
        # 2. 执行出售
        # 练气期兵器基础价格 100，卖出倍率 1.0 -> 100
        # 注意：Prices.WEAPON_PRICES[Realm.Qi_Refinement] 实际值需确认，假设是 default 100 或 mock
        # 根据 prices.py: WEAPON_PRICES = {Realm.Qi_Refinement: 10...} 
        # 等等，prices.py 里 Qi_Refinement 兵器是 10 吗？
        # 让我们 check prices.py 的内容:
        # Realm.Qi_Refinement: 10 (ITEM_PRICES)
        # Realm.Qi_Refinement: 10 (WEAPON_PRICES)
        # Realm.Qi_Refinement: 10 (AUXILIARY_PRICES)
        # 看来练气期都是 10。
        
        expected_income = 10 
        
        action._execute("青云剑")
        
        # 3. 验证结果
        assert avatar_in_city.magic_stone == expected_income
        assert avatar_in_city.weapon is None

def test_sell_auxiliary_success(avatar_in_city, mock_sell_objects):
    """测试出售当前法宝成功"""
    items_mock, _, _, test_auxiliary = mock_sell_objects
    
    # 装备法宝
    avatar_in_city.auxiliary = test_auxiliary
    
    with patch("src.classes.action.sell.items_by_name", items_mock):
        action = Sell(avatar_in_city, avatar_in_city.world)
        
        can_start, reason = action.can_start("聚灵珠")
        assert can_start is True
        
        # 练气期辅助装备也是 10
        expected_income = 10
        
        action._execute("聚灵珠")
        
        assert avatar_in_city.magic_stone == expected_income
        assert avatar_in_city.auxiliary is None

def test_sell_fail_not_in_city(dummy_avatar, mock_sell_objects):
    """测试不在城市无法出售"""
    items_mock, test_item, _, _ = mock_sell_objects
    
    # 确保不在城市
    assert not isinstance(dummy_avatar.tile.region, CityRegion)
    dummy_avatar.add_item(test_item, 1)
    
    with patch("src.classes.action.sell.items_by_name", items_mock):
        action = Sell(dummy_avatar, dummy_avatar.world)
        can_start, reason = action.can_start("铁矿石")
        
        assert can_start is False
        assert "仅能在城市" in reason

def test_sell_fail_no_item(avatar_in_city, mock_sell_objects):
    """测试未持有该物品"""
    items_mock, _, _, _ = mock_sell_objects
    
    # 背包为空，无装备
    
    with patch("src.classes.action.sell.items_by_name", items_mock):
        action = Sell(avatar_in_city, avatar_in_city.world)
        can_start, reason = action.can_start("铁矿石")
        
        assert can_start is False
        assert "未持有物品/装备" in reason

def test_sell_fail_unknown_name(avatar_in_city, mock_sell_objects):
    """测试未知物品名称"""
    items_mock, _, _, _ = mock_sell_objects
    
    with patch("src.classes.action.sell.items_by_name", items_mock):
        action = Sell(avatar_in_city, avatar_in_city.world)
        can_start, reason = action.can_start("不存在的神器")
        
        assert can_start is False
        assert "未持有物品/装备" in reason

def test_sell_priority(avatar_in_city, mock_sell_objects):
    """测试物品优先级：同名时优先卖背包里的材料"""
    items_mock, test_item, test_weapon, _ = mock_sell_objects
    
    # 构造一个同名的兵器和材料（虽然逻辑上不太可能，但测试代码健壮性）
    # 假设 items_mock 里有一个 "青云剑" 的材料
    fake_sword_item = create_test_item("青云剑", Realm.Qi_Refinement)
    items_mock["青云剑"] = fake_sword_item
    
    # 角色同时拥有该材料和该兵器
    avatar_in_city.add_item(fake_sword_item, 1)
    avatar_in_city.weapon = test_weapon # name也是 "青云剑"
    
    with patch("src.classes.action.sell.items_by_name", items_mock):
        action = Sell(avatar_in_city, avatar_in_city.world)
        
        # 执行出售
        action._execute("青云剑")
        
        # 应该优先卖掉了材料
        assert avatar_in_city.get_item_quantity(fake_sword_item) == 0
        assert avatar_in_city.weapon is not None # 兵器还在

