import pytest
from unittest.mock import patch, MagicMock
from src.classes.action.buy import Buy
from src.classes.region import CityRegion, Region
from src.classes.elixir import Elixir, ElixirType, ConsumedElixir
from src.classes.material import Material
from src.classes.weapon import Weapon
from src.classes.weapon_type import WeaponType
from src.classes.cultivation import Realm
from src.classes.tile import Tile, TileType

# 创建一些测试用的对象
def create_test_elixir(name, realm, price=100, elixir_id=1, effects=None):
    if effects is None:
        effects = {"max_hp": 10}
    return Elixir(
        id=elixir_id,
        name=name,
        realm=realm,
        type=ElixirType.Breakthrough,
        desc="测试丹药",
        price=price,
        effects=effects
    )

def create_test_material(name, realm, material_id=101):
    return Material(
        id=material_id,
        name=name,
        desc="测试物品",
        realm=realm
    )

@pytest.fixture
def avatar_in_city(dummy_avatar):
    """
    修改 dummy_avatar，使其位于城市中，并给予初始资金
    """
    # 模拟 Tile 和 Region
    # Region init: id, name, desc, cors (default=[])
    city_region = CityRegion(id=1, name="TestCity", desc="测试城市")
    tile = Tile(0, 0, TileType.CITY)
    tile.region = city_region
    
    dummy_avatar.tile = tile
    dummy_avatar.magic_stone = 1000  # 初始资金
    dummy_avatar.cultivation_progress.realm = Realm.Qi_Refinement # 练气期
    dummy_avatar.elixirs = [] # 清空已服用丹药
    
    return dummy_avatar

@pytest.fixture
def mock_objects():
    """
    Mock elixirs_by_name 和 materials_by_name
    """
    test_elixir = create_test_elixir("聚气丹", Realm.Qi_Refinement, price=100)
    high_level_elixir = create_test_elixir("筑基丹", Realm.Foundation_Establishment, price=1000, elixir_id=2)
    test_material = create_test_material("铁矿石", Realm.Qi_Refinement)

    # elixirs_by_name 是 Dict[str, List[Elixir]]
    elixirs_mock = {
        "聚气丹": [test_elixir],
        "筑基丹": [high_level_elixir]
    }
    
    # materials_by_name 是 Dict[str, Material]
    materials_mock = {
        "铁矿石": test_material
    }
    
    return elixirs_mock, materials_mock, test_elixir, high_level_elixir, test_material

def test_buy_item_success(avatar_in_city, mock_objects):
    """测试购买普通材料成功"""
    elixirs_mock, materials_mock, _, _, test_material = mock_objects
    
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

def test_buy_elixir_success(avatar_in_city, mock_objects):
    """测试购买并服用丹药成功"""
    elixirs_mock, materials_mock, test_elixir, _, _ = mock_objects
    
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

def test_buy_fail_not_in_city(dummy_avatar, mock_objects):
    """测试不在城市无法购买"""
    elixirs_mock, materials_mock, _, _, _ = mock_objects
    
    # 确保不在城市 (dummy_avatar 默认在 (0,0) PLAIN)
    assert not isinstance(dummy_avatar.tile.region, CityRegion)
    
    with patch("src.utils.resolution.elixirs_by_name", elixirs_mock), \
         patch("src.utils.resolution.materials_by_name", materials_mock):
        
        action = Buy(dummy_avatar, dummy_avatar.world)
        can_start, reason = action.can_start("铁矿石")
        
        assert can_start is False
        assert "仅能在城市" in reason

def test_buy_fail_no_money(avatar_in_city, mock_objects):
    """测试没钱无法购买"""
    elixirs_mock, materials_mock, _, _, test_material = mock_objects
    
    avatar_in_city.magic_stone = 0 # 没钱
    
    with patch("src.utils.resolution.elixirs_by_name", elixirs_mock), \
         patch("src.utils.resolution.materials_by_name", materials_mock):
        
        action = Buy(avatar_in_city, avatar_in_city.world)
        can_start, reason = action.can_start("铁矿石")
        
        assert can_start is False
        assert "灵石不足" in reason

def test_buy_fail_unknown_item(avatar_in_city, mock_objects):
    """测试未知物品"""
    elixirs_mock, materials_mock, _, _, _ = mock_objects
    
    with patch("src.utils.resolution.elixirs_by_name", elixirs_mock), \
         patch("src.utils.resolution.materials_by_name", materials_mock):
        
        action = Buy(avatar_in_city, avatar_in_city.world)
        can_start, reason = action.can_start("不存在的东西")
        
        assert can_start is False
        assert "未知物品" in reason

def test_buy_elixir_fail_high_level_restricted(avatar_in_city, mock_objects):
    """测试购买高阶丹药被限制"""
    elixirs_mock, materials_mock, _, high_level_elixir, _ = mock_objects
    
    # 给予足够金钱，避免因为钱不够而先报错
    avatar_in_city.magic_stone = 10000
    
    # 角色是练气期，尝试买筑基期丹药
    assert avatar_in_city.cultivation_progress.realm == Realm.Qi_Refinement
    assert high_level_elixir.realm == Realm.Foundation_Establishment
    
    with patch("src.utils.resolution.elixirs_by_name", elixirs_mock), \
         patch("src.utils.resolution.materials_by_name", materials_mock):
        
        action = Buy(avatar_in_city, avatar_in_city.world)
        can_start, reason = action.can_start("筑基丹")
        
        assert can_start is False
        # 当前版本限制仅开放练气期丹药
        assert "当前仅开放练气期丹药购买" in reason

def test_buy_elixir_fail_duplicate_active(avatar_in_city, mock_objects):
    """测试药效尚存无法重复购买"""
    elixirs_mock, materials_mock, test_elixir, _, _ = mock_objects
    
    # 先服用一个
    consumed = ConsumedElixir(test_elixir, int(avatar_in_city.world.month_stamp))
    
    avatar_in_city.elixirs.append(consumed)
    
    with patch("src.utils.resolution.elixirs_by_name", elixirs_mock), \
         patch("src.utils.resolution.materials_by_name", materials_mock):
        
        action = Buy(avatar_in_city, avatar_in_city.world)
        can_start, reason = action.can_start("聚气丹")
        
        assert can_start is False
        assert "药效尚存" in reason

def test_buy_weapon_trade_in(avatar_in_city, mock_objects):
    """测试购买新武器时自动卖出旧武器"""
    elixirs_mock, materials_mock, _, _, _ = mock_objects
    
    # 构造旧武器和新武器
    old_weapon = Weapon(id=201, name="铁剑", weapon_type=WeaponType.SWORD, realm=Realm.Qi_Refinement, desc="...", effects={'atk': 1})
    new_weapon = Weapon(id=202, name="青云剑", weapon_type=WeaponType.SWORD, realm=Realm.Qi_Refinement, desc="...", effects={'atk': 10})
    
    # 装备旧武器
    avatar_in_city.change_weapon(old_weapon)
    assert avatar_in_city.weapon == old_weapon
    
    materials_mock["青云剑"] = new_weapon
    
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
        assert avatar_in_city.weapon != old_weapon # 应该是新对象
        assert avatar_in_city.magic_stone == expected_money
