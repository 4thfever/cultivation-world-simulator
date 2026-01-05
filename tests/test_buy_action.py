import pytest
from unittest.mock import patch, MagicMock
from src.classes.action.buy import BuyItem
from src.classes.region import CityRegion, Region
from src.classes.elixir import Elixir, ElixirType, ConsumedElixir
from src.classes.item import Item
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

def create_test_item(name, realm, item_id=101):
    return Item(
        id=item_id,
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
    Mock elixirs_by_name 和 items_by_name
    """
    test_elixir = create_test_elixir("聚气丹", Realm.Qi_Refinement, price=100)
    high_level_elixir = create_test_elixir("筑基丹", Realm.Foundation_Establishment, price=1000, elixir_id=2)
    test_item = create_test_item("铁矿石", Realm.Qi_Refinement)

    # elixirs_by_name 是 Dict[str, List[Elixir]]
    elixirs_mock = {
        "聚气丹": [test_elixir],
        "筑基丹": [high_level_elixir]
    }
    
    # items_by_name 是 Dict[str, Item]
    items_mock = {
        "铁矿石": test_item
    }
    
    return elixirs_mock, items_mock, test_elixir, high_level_elixir, test_item

def test_buy_item_success(avatar_in_city, mock_objects):
    """测试购买普通物品成功"""
    elixirs_mock, items_mock, _, _, test_item = mock_objects
    
    with patch("src.classes.action.buy.elixirs_by_name", elixirs_mock), \
         patch("src.classes.action.buy.items_by_name", items_mock):
        
        action = BuyItem(avatar_in_city, avatar_in_city.world)
        
        # 1. 检查是否可购买
        can_start, reason = action.can_start("铁矿石")
        assert can_start is True
        
        # 2. 执行购买
        initial_money = avatar_in_city.magic_stone
        # 练气期物品基础价格 10，倍率 1.5 -> 15
        expected_price = int(10 * 1.5)
        
        action._execute("铁矿石")
        
        # 3. 验证结果
        assert avatar_in_city.magic_stone == initial_money - expected_price
        assert avatar_in_city.get_item_quantity(test_item) == 1

def test_buy_elixir_success(avatar_in_city, mock_objects):
    """测试购买并服用丹药成功"""
    elixirs_mock, items_mock, test_elixir, _, _ = mock_objects
    
    with patch("src.classes.action.buy.elixirs_by_name", elixirs_mock), \
         patch("src.classes.action.buy.items_by_name", items_mock):
        
        action = BuyItem(avatar_in_city, avatar_in_city.world)
        
        can_start, reason = action.can_start("聚气丹")
        assert can_start is True
        
        initial_money = avatar_in_city.magic_stone
        expected_price = int(test_elixir.price * 1.5)
        
        # 模拟服用丹药的行为（因为 consume_elixir 是 Avatar 的方法，我们可以信赖它，
        # 但为了单元测试的隔离性，或者确认它被调用了，可以验证副作用）
        # 这里直接验证副作用：elixirs 列表增加
        
        action._execute("聚气丹")
        
        assert avatar_in_city.magic_stone == initial_money - expected_price
        # 背包里不应该有丹药
        assert len(avatar_in_city.items) == 0 
        # 已服用列表应该有
        assert len(avatar_in_city.elixirs) == 1
        assert avatar_in_city.elixirs[0].elixir.name == "聚气丹"

def test_buy_fail_not_in_city(dummy_avatar, mock_objects):
    """测试不在城市无法购买"""
    elixirs_mock, items_mock, _, _, _ = mock_objects
    
    # 确保不在城市 (dummy_avatar 默认在 (0,0) PLAIN)
    assert not isinstance(dummy_avatar.tile.region, CityRegion)
    
    with patch("src.classes.action.buy.elixirs_by_name", elixirs_mock), \
         patch("src.classes.action.buy.items_by_name", items_mock):
        
        action = BuyItem(dummy_avatar, dummy_avatar.world)
        can_start, reason = action.can_start("铁矿石")
        
        assert can_start is False
        assert "仅能在城市" in reason

def test_buy_fail_no_money(avatar_in_city, mock_objects):
    """测试没钱无法购买"""
    elixirs_mock, items_mock, _, _, test_item = mock_objects
    
    avatar_in_city.magic_stone = 0 # 没钱
    
    with patch("src.classes.action.buy.elixirs_by_name", elixirs_mock), \
         patch("src.classes.action.buy.items_by_name", items_mock):
        
        action = BuyItem(avatar_in_city, avatar_in_city.world)
        can_start, reason = action.can_start("铁矿石")
        
        assert can_start is False
        assert "灵石不足" in reason

def test_buy_fail_unknown_item(avatar_in_city, mock_objects):
    """测试未知物品"""
    elixirs_mock, items_mock, _, _, _ = mock_objects
    
    with patch("src.classes.action.buy.elixirs_by_name", elixirs_mock), \
         patch("src.classes.action.buy.items_by_name", items_mock):
        
        action = BuyItem(avatar_in_city, avatar_in_city.world)
        can_start, reason = action.can_start("不存在的东西")
        
        assert can_start is False
        assert "未知物品" in reason

def test_buy_elixir_fail_realm_too_low(avatar_in_city, mock_objects):
    """测试境界不足无法购买丹药"""
    elixirs_mock, items_mock, _, high_level_elixir, _ = mock_objects
    
    # 给予足够金钱，避免因为钱不够而先报错
    avatar_in_city.magic_stone = 10000
    
    # 角色是练气期，尝试买筑基期丹药
    assert avatar_in_city.cultivation_progress.realm == Realm.Qi_Refinement
    assert high_level_elixir.realm == Realm.Foundation_Establishment
    
    with patch("src.classes.action.buy.elixirs_by_name", elixirs_mock), \
         patch("src.classes.action.buy.items_by_name", items_mock):
        
        action = BuyItem(avatar_in_city, avatar_in_city.world)
        can_start, reason = action.can_start("筑基丹")
        
        assert can_start is False
        assert "境界不足" in reason

def test_buy_elixir_fail_duplicate_active(avatar_in_city, mock_objects):
    """测试药效尚存无法重复购买"""
    elixirs_mock, items_mock, test_elixir, _, _ = mock_objects
    
    # 先服用一个
    consumed = ConsumedElixir(test_elixir, int(avatar_in_city.world.month_stamp))
    # 假设它是持久效果或未过期
    # ConsumedElixir 计算过期时间依赖 effects，我们在 create_test_elixir 里如果不给 duration_month，默认是 inf 或者是 0 (Action里的逻辑是看 is_completely_expired)
    # 这里的 mock elixir 默认 effects 是 {"max_hp": 10}，没有 duration_month，所以是永久效果？
    # 查阅 ConsumedElixir._get_max_duration: 如果没有 duration_month, return inf (永久)。
    # 所以这应该是永久生效的。
    
    avatar_in_city.elixirs.append(consumed)
    
    with patch("src.classes.action.buy.elixirs_by_name", elixirs_mock), \
         patch("src.classes.action.buy.items_by_name", items_mock):
        
        action = BuyItem(avatar_in_city, avatar_in_city.world)
        can_start, reason = action.can_start("聚气丹")
        
        assert can_start is False
        assert "药效尚存" in reason


