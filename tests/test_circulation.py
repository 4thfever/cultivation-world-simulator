import pytest
import copy
from unittest.mock import MagicMock, patch
from src.classes.core.world import World
from src.classes.circulation import CirculationManager
from src.classes.items.weapon import Weapon, WeaponType
from src.classes.items.auxiliary import Auxiliary
from src.systems.cultivation import Realm
from src.classes.core.avatar import Avatar, Gender
from src.classes.age import Age
from src.systems.time import Month, Year, create_month_stamp
from src.utils.id_generator import get_avatar_id
from src.sim.save.save_game import save_game
from src.sim.load.load_game import load_game
from src.sim.simulator import Simulator
from src.classes.environment.map import Map
from src.classes.environment.tile import TileType

# --- Helper Objects ---

def create_mock_weapon(w_id=1, name="MockSword"):
    w = MagicMock(spec=Weapon)
    w.id = w_id
    w.name = name
    w.realm = Realm.Qi_Refinement
    w.special_data = {"test_val": 123}
    # Mock to_save_dict behavior manually or rely on CirculationManager using id/special_data
    return w

def create_mock_auxiliary(a_id=1, name="MockRing"):
    a = MagicMock(spec=Auxiliary)
    a.id = a_id
    a.name = name
    a.realm = Realm.Qi_Refinement
    a.special_data = {"souls": 5}
    return a

def create_test_map():
    m = Map(width=10, height=10)
    for x in range(10):
        for y in range(10):
            m.create_tile(x, y, TileType.PLAIN)
    return m

@pytest.fixture
def temp_save_dir(tmp_path):
    d = tmp_path / "saves"
    d.mkdir()
    return d

@pytest.fixture
def empty_world():
    game_map = create_test_map()
    return World(map=game_map, month_stamp=create_month_stamp(Year(1), Month.JANUARY))

# --- Tests ---

def test_circulation_manager_basic():
    """Test basic adding of items to CirculationManager"""
    cm = CirculationManager()
    
    # Test adding Weapon
    w = create_mock_weapon(1, "Sword")
    # CirculationManager uses instantiate, so we need to ensure the mock supports it
    # MagicMock is hard to deepcopy properly in some contexts, let's use a simple object structure or patch copy.deepcopy
    # But for robustness, let's try to make a real-ish object or a class that looks like Weapon
    
    # Let's define a simple dummy class for testing to avoid importing all Weapon dependencies
    class DummyItem:
        def __init__(self, id, name, special_data=None):
            self.id = id
            self.name = name
            self.special_data = special_data or {}
        def instantiate(self):
            import copy
            return copy.deepcopy(self)
    
    w1 = DummyItem(1, "Sword", {"kills": 10})
    cm.add_weapon(w1)
    
    assert len(cm.sold_weapons) == 1
    assert cm.sold_weapons[0].name == "Sword"
    # Ensure it's a copy
    assert cm.sold_weapons[0] is not w1 
    assert cm.sold_weapons[0].special_data["kills"] == 10
    
    # Test adding Auxiliary
    a1 = DummyItem(2, "Ring", {"mana": 50})
    cm.add_auxiliary(a1)
    
    assert len(cm.sold_auxiliaries) == 1
    assert cm.sold_auxiliaries[0].name == "Ring"

def test_circulation_serialization():
    """Test to_save_dict and load_from_dict"""
    cm = CirculationManager()
    
    # Prepare data using real-ish mocks that can be looked up by ID
    # We need to patch weapons_by_id and auxiliaries_by_id during load
    
    class DummyItem:
        def __init__(self, id, name):
            self.id = id
            self.name = name
            self.special_data = {}
        def instantiate(self):
            import copy
            return copy.deepcopy(self)

    w1 = DummyItem(101, "RareSword")
    w1.special_data = {"stat": 1}
    
    a1 = DummyItem(202, "RareRing")
    a1.special_data = {"stat": 2}
    
    cm.add_weapon(w1)
    cm.add_auxiliary(a1)
    
    saved_data = cm.to_save_dict()
    
    # Verify saved structure
    assert "weapons" in saved_data
    assert "auxiliaries" in saved_data
    assert len(saved_data["weapons"]) == 1
    assert saved_data["weapons"][0]["id"] == 101
    assert saved_data["weapons"][0]["special_data"] == {"stat": 1}
    
    # Test Loading
    new_cm = CirculationManager()
    
    # We need to mock the global dictionaries used in load_from_dict
    mock_weapons_db = {101: DummyItem(101, "RareSword_Proto")} # Proto doesn't have special_data usually
    mock_aux_db = {202: DummyItem(202, "RareRing_Proto")}
    
    with patch("src.classes.items.weapon.weapons_by_id", mock_weapons_db), \
         patch("src.classes.items.auxiliary.auxiliaries_by_id", mock_aux_db):
        
        new_cm.load_from_dict(saved_data)
        
        assert len(new_cm.sold_weapons) == 1
        assert new_cm.sold_weapons[0].id == 101
        assert new_cm.sold_weapons[0].name == "RareSword_Proto" # Should come from prototype
        assert new_cm.sold_weapons[0].special_data == {"stat": 1} # Should be restored from save
        
        assert len(new_cm.sold_auxiliaries) == 1
        assert new_cm.sold_auxiliaries[0].id == 202

def test_avatar_sell_integration(empty_world):
    """Test that selling an item via Avatar correctly adds it to World.circulation"""
    
    # Setup Avatar
    avatar = Avatar(
        world=empty_world,
        name="Seller",
        id=get_avatar_id(),
        birth_month_stamp=create_month_stamp(Year(1), Month.JANUARY),
        age=Age(20, Realm.Qi_Refinement),
        gender=Gender.MALE
    )
    empty_world.avatar_manager.avatars[avatar.id] = avatar
    
    # Setup Prices mock to avoid complex price calculation dependencies
    with patch("src.classes.prices.prices") as mock_prices:
        mock_prices.get_weapon_price.return_value = 100
        mock_prices.get_auxiliary_price.return_value = 200
        # 这里的 sell_weapon 现在调用 get_selling_price，我们也 mock 它
        # 假设这里没有额外加成，或者我们直接设定最终售价
        mock_prices.get_selling_price.side_effect = lambda obj, seller: \
            100 if getattr(obj, "id", 0) == 999 else \
            (300 if getattr(obj, "id", 0) == 888 else 0)
        # 上面的 side_effect 比较复杂，因为测试里先后卖了 weapon(id=999) 和 aux(id=888)
        # 我们可以简单地根据类型返回，或者分段 mock
        
        # 重新定义 mock 逻辑
        def get_selling_price_mock(obj, seller):
            if hasattr(obj, "id") and obj.id == 999: return 100
            if hasattr(obj, "id") and obj.id == 888: return 200
            return 0
        mock_prices.get_selling_price.side_effect = get_selling_price_mock

        # 1. Test Sell Weapon
        # Create a dummy weapon that acts like the real one
        weapon = MagicMock(spec=Weapon)
        weapon.instantiate.return_value = weapon # Mock instantiate
        weapon.id = 999
        weapon.name = "TestBlade"
        weapon.realm = Realm.Qi_Refinement
        
        # The mixin usually requires self.materials to have the material for sell_material, 
        # but sell_weapon/sell_auxiliary are for equipped items or passed items.
        # Looking at inventory_mixin.py: sell_weapon(self, weapon) just calculates price and adds stones.
        # It calls _get_sell_multiplier()
        
        # Ensure avatar has magic stones initialized
        avatar.magic_stone = 0
        
        # Action
        avatar.sell_weapon(weapon)
        
        # Verify
        assert avatar.magic_stone == 100
        assert len(empty_world.circulation.sold_weapons) == 1
        # Since we use MagicMock, deepcopy might be weird, but let's check basic attr
        assert empty_world.circulation.sold_weapons[0].id == 999
        
        # 2. Test Sell Auxiliary
        aux = MagicMock(spec=Auxiliary)
        aux.instantiate.return_value = aux # Mock instantiate
        aux.id = 888
        aux.name = "TestAmulet"
        
        # Action
        avatar.sell_auxiliary(aux)
        
        # Verify
        assert avatar.magic_stone == 300 # 100 + 200
        assert len(empty_world.circulation.sold_auxiliaries) == 1
        assert empty_world.circulation.sold_auxiliaries[0].id == 888

def test_save_load_circulation(temp_save_dir, empty_world):
    """Test full save/load cycle with circulation data"""
    
    # 1. Populate circulation
    class SimpleItem:
        def __init__(self, id, name):
            self.id = id
            self.name = name
            self.special_data = {}
            self.realm = Realm.Qi_Refinement # needed if deepcopy looks at it or for other checks
        def instantiate(self):
            import copy
            return copy.deepcopy(self)
            
    w1 = SimpleItem(10, "LostSword")
    w1.special_data = {"kills": 99}
    empty_world.circulation.add_weapon(w1)
    
    # 2. Save
    sim = Simulator(empty_world)
    save_path = temp_save_dir / "circulation_test.json"
    
    save_game(empty_world, sim, [], save_path)
    
    # 3. Load
    # We need to mock the DBs to recognize ID 10
    mock_weapons_db = {10: SimpleItem(10, "LostSword_Proto")}
    
    with patch("src.run.load_map.load_cultivation_world_map", return_value=create_test_map()), \
         patch("src.classes.items.weapon.weapons_by_id", mock_weapons_db), \
         patch("src.classes.items.auxiliary.auxiliaries_by_id", {}):
        
        loaded_world, _, _ = load_game(save_path)
        
    # 4. Verify
    assert len(loaded_world.circulation.sold_weapons) == 1
    loaded_w = loaded_world.circulation.sold_weapons[0]
    assert loaded_w.id == 10
    assert loaded_w.name == "LostSword_Proto" # Should be restored from proto name
    assert loaded_w.special_data == {"kills": 99} # Should have restored data

