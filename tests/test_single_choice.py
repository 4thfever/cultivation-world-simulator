import pytest
from unittest.mock import AsyncMock, Mock, patch
from src.classes.single_choice import handle_item_exchange

# Mocks for types
class MockAvatar:
    def __init__(self):
        self.name = "TestAvatar"
        self.weapon = None
        self.auxiliary = None
        self.technique = None
        self.world = Mock()
        self.world.static_info = {}
        self.change_weapon = Mock()
        self.sell_weapon = Mock(return_value=100)
        self.consume_elixir = Mock()
        self.sell_elixir = Mock(return_value=50)
        
    def get_info(self, detailed=False):
        return {"name": self.name}

class MockItem:
    def __init__(self, name, item_type="weapon"):
        self.name = name
        self.item_type = item_type
        # Weapon/Auxiliary/Elixir usually have realm or grade.
        self.realm = Mock()
        self.realm.value = "TestRealm"
        self.realm.__str__ = Mock(return_value="TestRealm")
        
    def get_info(self, detailed=False):
        return f"Info({self.name})"

@pytest.mark.asyncio
async def test_weapon_auto_equip_no_sell_new():
    """测试：自动装备兵器（无旧兵器，不可卖新）"""
    avatar = MockAvatar()
    new_weapon = MockItem("NewSword", "weapon")
    
    # 模拟无旧兵器
    avatar.weapon = None
    
    swapped, msg = await handle_item_exchange(
        avatar, new_weapon, "weapon", "Context", can_sell_new=False
    )
    
    assert swapped is True
    assert "获得了TestRealm兵器『NewSword』并装备" in msg
    avatar.change_weapon.assert_called_once_with(new_weapon)

@pytest.mark.asyncio
async def test_weapon_swap_choice_A():
    """测试：替换兵器，选择 A（装备新，卖旧）"""
    avatar = MockAvatar()
    old_weapon = MockItem("OldSword", "weapon")
    new_weapon = MockItem("NewSword", "weapon")
    avatar.weapon = old_weapon
    
    # Mock decision to return 'A'
    with patch("src.classes.single_choice.make_decision", new_callable=AsyncMock) as mock_decision:
        mock_decision.return_value = "A"
        
        swapped, msg = await handle_item_exchange(
            avatar, new_weapon, "weapon", "Context", can_sell_new=True
        )
        
        # 验证文案包含动词
        # call_args[0][1] is context string, check options description
        call_args = mock_decision.call_args
        options = call_args[0][2] # options list
        opt_a_desc = options[0]["desc"]
        
        # 验证选项文案使用了 "装备" 和 "卖掉"
        assert "装备新兵器『NewSword』" in opt_a_desc
        assert "卖掉旧兵器『OldSword』" in opt_a_desc
        
        assert swapped is True
        assert "换上了TestRealm兵器『NewSword』" in msg
        avatar.sell_weapon.assert_called_once_with(old_weapon)
        avatar.change_weapon.assert_called_once_with(new_weapon)

@pytest.mark.asyncio
async def test_elixir_consume_choice_A():
    """测试：获得丹药，选择 A（服用）"""
    avatar = MockAvatar()
    new_elixir = MockItem("PowerPill", "elixir")
    
    # Mock decision to return 'A'
    with patch("src.classes.single_choice.make_decision", new_callable=AsyncMock) as mock_decision:
        mock_decision.return_value = "A"
        
        swapped, msg = await handle_item_exchange(
            avatar, new_elixir, "elixir", "Context", can_sell_new=True
        )
        
        # 验证选项文案
        options = mock_decision.call_args[0][2]
        opt_a_desc = options[0]["desc"]
        # 验证使用了 "服用"
        assert "服用新丹药『PowerPill』" in opt_a_desc
        
        assert swapped is True
        # 验证结果使用了 "服用了"
        assert "服用了TestRealm丹药『PowerPill』" in msg
        avatar.consume_elixir.assert_called_once_with(new_elixir)

@pytest.mark.asyncio
async def test_elixir_sell_choice_B():
    """测试：获得丹药，选择 B（卖出）"""
    avatar = MockAvatar()
    new_elixir = MockItem("PowerPill", "elixir")
    
    # Mock decision to return 'B'
    with patch("src.classes.single_choice.make_decision", new_callable=AsyncMock) as mock_decision:
        mock_decision.return_value = "B"
        
        swapped, msg = await handle_item_exchange(
            avatar, new_elixir, "elixir", "Context", can_sell_new=True
        )
        
        assert swapped is False
        assert "卖掉了新获得的PowerPill" in msg
        avatar.sell_elixir.assert_called_once_with(new_elixir)
        avatar.consume_elixir.assert_not_called()

