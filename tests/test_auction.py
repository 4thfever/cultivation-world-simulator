import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from src.classes.gathering.auction import Auction
from src.classes.items.item import Item
from src.classes.items.weapon import Weapon
from src.classes.items.auxiliary import Auxiliary
from src.classes.prices import prices
from src.utils.config import CONFIG

# Monkeypatch removed as Weapon/Auxiliary now have __hash__ implemented

@pytest.mark.asyncio
async def test_auction_is_start(base_world, mock_item_data):
    auction = Auction()
    weapon = mock_item_data["obj_weapon"]
    
    # 初始状态，sold_item_count 为 0
    # 清空 circulation
    base_world.circulation.sold_weapons = []
    base_world.circulation.sold_auxiliaries = []
    base_world.circulation.sold_elixirs = []
    
    # 设置阈值
    CONFIG.game.gathering.auction_trigger_count = 5
    
    assert auction.is_start(base_world) is False
    
    # 增加物品数量达到阈值
    for _ in range(5):
        base_world.circulation.add_weapon(weapon)
        
    assert auction.is_start(base_world) is True

def test_calculate_bid(dummy_avatar, mock_item_data):
    auction = Auction()
    item = mock_item_data["obj_weapon"]
    base_price = prices.get_price(item)
    
    # Case 1: 需求低 (<=1) -> 出价 0
    assert auction._calculate_bid(item, 1, 1000) == 0
    
    # Case 2: 需求 2 (捡漏 0.8)
    expected_price = int(base_price * 0.8)
    assert auction._calculate_bid(item, 2, 100000) == expected_price
    
    # Case 3: 余额不足 -> 出价 = 余额
    avatar_money = 10
    bid = auction._calculate_bid(item, 3, avatar_money) # need 3 is 1.5x, definitely > 10
    assert bid == avatar_money
    
    # Case 4: 需求 5 (梭哈) -> 出价 = 余额
    assert auction._calculate_bid(item, 5, 5000) == 5000

def test_resolve_auctions_basic(dummy_avatar, mock_item_data):
    """测试基本的竞价结算逻辑（单物品）"""
    auction = Auction()
    item = mock_item_data["obj_weapon"]
    
    avatar1 = dummy_avatar
    avatar1.magic_stone = 1000
    avatar1.name = "A1"
    
    # 创建第二个角色
    avatar2 = MagicMock()
    avatar2.magic_stone = 1000
    avatar2.name = "A2"
    avatar2.__hash__ = MagicMock(return_value=123) # Make it hashable for dict keys
    
    # 模拟需求字典
    needs = {
        item: {
            avatar1: 4, # High need
            avatar2: 2  # Low need
        }
    }
    
    # Mock prices
    with patch("src.classes.prices.prices.get_price", return_value=100):
        deal_results, unsold, willing = auction.resolve_auctions(needs)
        
    # 验证结果
    assert item in deal_results
    winner, price = deal_results[item]
    
    # A1 出价: 100 * 3.0 = 300
    # A2 出价: 100 * 0.8 = 80
    # 成交价应为第二高价(80) + 1 = 81
    assert winner == avatar1
    assert price == 81
    assert not unsold

def test_resolve_auctions_asset_protection(dummy_avatar, mock_item_data):
    """测试资产穿透保护：同一个角色竞拍多个物品"""
    auction = Auction()
    item1 = mock_item_data["obj_weapon"] # 贵
    item2 = mock_item_data["obj_material"] # 便宜
    
    avatar = dummy_avatar
    avatar.magic_stone = 100  # 总共只有 100
    
    needs = {
        item1: {avatar: 5}, # 梭哈 item1
        item2: {avatar: 5}  # 梭哈 item2
    }
    
    # Mock prices: item1=80, item2=50
    # item1 应该先结算（价值高），因为是梭哈(need=5)，出价100。
    # 如果只有一人竞拍，成交价 = max(1, 100 * 0.6) = 60。
    # 剩余余额 = 100 - 60 = 40。
    # item2 结算时，余额只有 40，虽然 need=5，但出价只能是 40。
    # item2 成交价 = max(1, 40 * 0.6) = 24。
    
    def get_price_side_effect(item):
        if item == item1: return 80
        return 50
        
    with patch("src.classes.prices.prices.get_price", side_effect=get_price_side_effect):
        deal_results, unsold, willing = auction.resolve_auctions(needs)
    
    # 验证 item1
    assert item1 in deal_results
    winner1, price1 = deal_results[item1]
    assert winner1 == avatar
    assert price1 == 60 # 100 * 0.6
    
    # 验证 item2
    assert item2 in deal_results
    winner2, price2 = deal_results[item2]
    assert winner2 == avatar
    # 此时余额只剩 40，出价 40，成交价 40 * 0.6 = 24
    assert price2 == 24
    
    # 总花费 84 <= 100，保护成功
    assert price1 + price2 <= 100

def test_resolve_auctions_unsold(mock_item_data):
    """测试流拍"""
    auction = Auction()
    item = mock_item_data["obj_weapon"]
    
    # 空需求或者需求都很低导致不出价
    needs = {
        item: {}
    }
    
    with patch("src.classes.prices.prices.get_price", return_value=100):
        deal_results, unsold, willing = auction.resolve_auctions(needs)
        
    assert item not in deal_results
    assert item in unsold

@pytest.mark.asyncio
async def test_execute_flow(base_world, dummy_avatar, mock_item_data):
    """测试完整的 execute 流程，包括物品交易和销毁"""
    auction = Auction()
    item_sold = mock_item_data["obj_weapon"]
    item_unsold = mock_item_data["obj_auxiliary"] # 使用 Auxiliary 代替 Material
    
    # 设置环境
    # 将物品加入 circulation 以便测试移除逻辑
    base_world.circulation.sold_weapons = [item_sold]
    base_world.circulation.sold_auxiliaries = [item_unsold]
    
    # 设置 Avatar
    dummy_avatar.magic_stone = 1000
    dummy_avatar.weapon = None # 确保没有武器
    dummy_avatar.auxiliary = None 
    
    # 确保 avatar 在 avatar_manager 中
    base_world.avatar_manager.avatars[dummy_avatar.id] = dummy_avatar
    
    # Mock methods
    # 1. get_related_avatars
    auction.get_related_avatars = MagicMock(return_value=[dummy_avatar.id])
    
    # 2. get_needs (Async) -> 让 item_sold 有人买，item_unsold 没人买
    async def mock_get_needs(*args, **kwargs):
        return {
            item_sold: {dummy_avatar: 4}, # High need
            item_unsold: {dummy_avatar: 1} # No need
        }
    auction.get_needs = mock_get_needs
    
    # 3. Mock StoryTeller to avoid LLM
    with patch("src.classes.story_teller.StoryTeller.tell_gathering_story", new_callable=AsyncMock) as mock_story:
        mock_story.return_value = "拍卖会故事..."
        
        # 4. Mock prices
        with patch("src.classes.prices.prices.get_price", return_value=100):
            events = await auction.execute(base_world)
            
    # 验证结果
    
    # 1. 物品去向
    # item_sold 应该被 dummy_avatar 装备
    assert dummy_avatar.weapon == item_sold
    # item_sold 应该不在 circulation 中
    assert item_sold not in base_world.circulation.sold_weapons
    
    # item_unsold 应该被销毁 (不在 circulation 中，也不在 avatar 背包/装备 中)
    assert item_unsold not in base_world.circulation.sold_auxiliaries
    assert dummy_avatar.auxiliary != item_unsold
    
    # 2. 资金扣除
    # Base price 100, Need 4 (3.0x) -> Bid 300
    # Single bidder -> Deal 300 * 0.6 = 180
    # Balance 1000 - 180 = 820
    assert dummy_avatar.magic_stone == 820
    
    # 3. 事件生成
    assert len(events) > 0
    # 应该包含 story event
    assert any(e.content == "拍卖会故事..." for e in events)

def test_items_are_hashable():
    """测试物品类是否可哈希（用作字典键）"""
    from src.classes.items.weapon import Weapon
    from src.classes.weapon_type import WeaponType
    from src.classes.items.auxiliary import Auxiliary
    from src.classes.items.elixir import Elixir, ElixirType
    from src.systems.cultivation import Realm

    # Weapon
    w = Weapon(
        id=1, 
        name="TestSword", 
        weapon_type=WeaponType.SWORD, 
        realm=Realm.Qi_Refinement, 
        desc="Test",
        special_data={"a": 1} # mutable field
    )
    s = set()
    s.add(w)
    assert w in s
    d = {w: 1}
    assert d[w] == 1

    # Auxiliary
    a = Auxiliary(
        id=2, 
        name="TestAux", 
        realm=Realm.Qi_Refinement, 
        desc="Test",
        special_data={"b": 2} # mutable field
    )
    s = set()
    s.add(a)
    assert a in s
    
    # Elixir
    e = Elixir(
        id=3,
        name="TestElixir",
        realm=Realm.Qi_Refinement,
        type=ElixirType.Heal,
        desc="Test",
        price=100
    )
    s = set()
    s.add(e)
    assert e in s

def test_resolve_auctions_tie_breaking(dummy_avatar, mock_item_data):
    """测试出价相同时的判定（稳定性）"""
    auction = Auction()
    item = mock_item_data["obj_weapon"]
    
    # 两个角色，需求相同，资金充足 -> 理论上出价相同
    avatar1 = dummy_avatar
    avatar1.magic_stone = 1000
    avatar1.name = "A1"
    
    avatar2 = MagicMock()
    avatar2.magic_stone = 1000
    avatar2.name = "A2"
    avatar2.__hash__ = MagicMock(return_value=12345) 
    
    # 手动构建 needs 字典，控制 key 的顺序
    # 情况1: A1 在前
    needs1 = {
        item: {avatar1: 5, avatar2: 5}
    }
    
    with patch("src.classes.prices.prices.get_price", return_value=100):
        deal_results1, _, _ = auction.resolve_auctions(needs1)
        
    winner1, _ = deal_results1[item]
    # 如果是稳定排序，且 bid 相等，应该保持顺序，winner 是 A1
    assert winner1 == avatar1
    
    # 情况2: A2 在前
    needs2 = {
        item: {avatar2: 5, avatar1: 5}
    }
    with patch("src.classes.prices.prices.get_price", return_value=100):
        deal_results2, _, _ = auction.resolve_auctions(needs2)
    
    winner2, _ = deal_results2[item]
    # winner 应该是 A2
    assert winner2 == avatar2

def test_resolve_auctions_no_refund_consideration(dummy_avatar, mock_item_data):
    """测试拍卖结算时不考虑后续装备出售的退款（防止透支）"""
    auction = Auction()
    item1 = mock_item_data["obj_weapon"] # 贵, 先结算
    item2 = mock_item_data["obj_elixir"] # 便宜, 后结算
    
    avatar = dummy_avatar
    avatar.magic_stone = 100 
    
    # 假设 avatar 身上有装备，卖出可得 50
    old_weapon = MagicMock()
    avatar.weapon = old_weapon
    # 但 resolve_auctions 只看 snapshot，不看装备退款
    
    needs = {
        item1: {avatar: 5}, # 梭哈 item1, cost 100
        item2: {avatar: 5}  # 梭哈 item2
    }
    
    # Mock prices: item1=80, item2=50
    # item1 price 80, need 5 -> bid 100 (balance). Deal: 100*0.6 = 60.
    # item2 price 50. Remaining balance 100-60=40.
    # need 5 -> bid 40 (balance). Deal: 40*0.6 = 24.
    # If refund (50) was considered, balance would be 40+50=90.
    # Bid 90 -> Deal 54.
    
    def get_price_side_effect(item):
        if item == item1: return 80
        return 50
        
    with patch("src.classes.prices.prices.get_price", side_effect=get_price_side_effect):
        deal_results, _, _ = auction.resolve_auctions(needs)
        
    # item1 应该成交，消耗 60 (100 * 0.6)
    assert deal_results[item1][0] == avatar
    assert deal_results[item1][1] == 60
    
    # item2 应该成交，消耗 24 (40 * 0.6)
    # 证明使用了 40 的余额，而不是 90 (如果包含退款)
    assert item2 in deal_results
    assert deal_results[item2][1] == 24
    
    # 总消耗 84 <= 100
    assert deal_results[item1][1] + deal_results[item2][1] <= 100

@pytest.mark.asyncio
async def test_execute_item_types(base_world, dummy_avatar, mock_item_data):
    """测试不同类型物品的执行逻辑 (Elixir)"""
    auction = Auction()
    elixir = mock_item_data["obj_elixir"]
    
    dummy_avatar.magic_stone = 1000
    base_world.circulation.sold_elixirs = [elixir]
    
    # Register avatar
    base_world.avatar_manager.avatars[dummy_avatar.id] = dummy_avatar
    
    # Mock resolve_auctions
    auction.resolve_auctions = MagicMock(return_value=(
        {elixir: (dummy_avatar, 100)}, 
        [], 
        {}
    ))
    
    # Mock dependencies
    auction.get_related_avatars = MagicMock(return_value=[dummy_avatar.id])
    auction.get_needs = AsyncMock(return_value={}) # ignored by mocked resolve
    auction._generate_deal_events = MagicMock(return_value=[])
    auction._generate_rivalry_events = MagicMock(return_value=[])
    auction._generate_story = AsyncMock(return_value=[])
    
    # Mock circulation remove
    base_world.circulation.remove_item = MagicMock()
    
    # Mock consume_elixir
    dummy_avatar.consume_elixir = MagicMock()
    
    # Ensure items are "in" circulation logic (count > 0)
    # Circulation.sold_item_count is a property, depends on lists.
    # We set sold_elixirs above, so it should be > 0.
    
    await auction.execute(base_world)
    
    # Verify consume_elixir called
    dummy_avatar.consume_elixir.assert_called_once_with(elixir)
    
    # Verify remove_item called
    base_world.circulation.remove_item.assert_called_once_with(elixir)

@pytest.mark.asyncio
async def test_get_needs_parsing(base_world, dummy_avatar, mock_item_data):
    """测试 get_needs 的 LLM 结果解析逻辑"""
    auction = Auction()
    item = mock_item_data["obj_weapon"]
    # Mock circulation
    base_world.circulation.sold_weapons = [item]
    
    # Mock LLM response
    mock_response = {
        dummy_avatar.name: {
            str(item.id): 5  # High need
        }
    }
    
    with patch("src.classes.gathering.auction.call_llm_with_template", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = mock_response
        
        needs = await auction.get_needs(base_world, [dummy_avatar])
        
    assert item in needs
    assert needs[item][dummy_avatar] == 5
    
    # Test filtering of low needs (<=1)
    mock_response_low = {
        dummy_avatar.name: {
            str(item.id): 1 
        }
    }
    with patch("src.classes.gathering.auction.call_llm_with_template", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = mock_response_low
        needs = await auction.get_needs(base_world, [dummy_avatar])
        
    # Should be empty because score 1 is filtered
    assert item not in needs or not needs.get(item)
