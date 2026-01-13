import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from src.classes.gathering.auction import Auction
from src.classes.item import Item
from src.classes.weapon import Weapon
from src.classes.auxiliary import Auxiliary
from src.classes.prices import prices
from src.utils.config import CONFIG

# Monkeypatch hash for Weapon/Auxiliary/Item to make them usable as dict keys in tests
# Dataclasses are unhashable by default if they are mutable
def _item_hash(self):
    return hash(self.id)

Weapon.__hash__ = _item_hash
Auxiliary.__hash__ = _item_hash

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

