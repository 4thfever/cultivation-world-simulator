import pytest
from src.classes.items.item import Item
from src.classes.items.registry import ItemRegistry
from src.classes.items.weapon import Weapon
from src.classes.items.auxiliary import Auxiliary
from src.classes.items.elixir import Elixir
from src.classes.items.store import StoreMixin
from src.systems.cultivation import Realm
from src.classes.weapon_type import WeaponType
from src.classes.items.elixir import ElixirType

# Mock concrete implementations for testing
class MockItem(Item):
    def __init__(self, id, name):
        self.id = id
        self.name = name

# --- Test Item Registry ---

def test_registry_registration():
    """Test that items can be registered and retrieved."""
    # Clear registry for test isolation (though usually not exposed, we access _items_by_id)
    original_registry = ItemRegistry._items_by_id.copy()
    ItemRegistry._items_by_id.clear()
    
    try:
        item1 = MockItem(1001, "TestItem1")
        item2 = MockItem(1002, "TestItem2")
        
        ItemRegistry.register(item1.id, item1)
        ItemRegistry.register(item2.id, item2)
        
        assert ItemRegistry.get(1001) == item1
        assert ItemRegistry.get(1002) == item2
        assert ItemRegistry.get(9999) is None
        
        all_items = ItemRegistry.get_all()
        assert len(all_items) == 2
        assert 1001 in all_items
        assert 1002 in all_items
        
    finally:
        # Restore registry
        ItemRegistry._items_by_id = original_registry

def test_registry_overwrite():
    """Test that registering an ID again overwrites the previous item."""
    original_registry = ItemRegistry._items_by_id.copy()
    ItemRegistry._items_by_id.clear()
    
    try:
        item1 = MockItem(1001, "ItemV1")
        item2 = MockItem(1001, "ItemV2")
        
        ItemRegistry.register(1001, item1)
        assert ItemRegistry.get(1001).name == "ItemV1"
        
        ItemRegistry.register(1001, item2)
        assert ItemRegistry.get(1001).name == "ItemV2"
        
    finally:
        ItemRegistry._items_by_id = original_registry

# --- Test Store Mixin with Item IDs ---

class MockShop(StoreMixin):
    def __init__(self):
        self.name = "TestShop"

def test_store_init_with_ids(mock_item_data):
    """Test initializing a store with item IDs."""
    original_registry = ItemRegistry._items_by_id.copy()
    ItemRegistry._items_by_id.clear()
    
    try:
        # Setup registry
        weapon = mock_item_data["obj_weapon"] # ID 201
        elixir = mock_item_data["obj_elixir"] # ID 1
        
        ItemRegistry.register(weapon.id, weapon)
        ItemRegistry.register(elixir.id, elixir)
        
        # Init shop
        shop = MockShop()
        shop.init_store([weapon.id, elixir.id])
        
        assert len(shop.store_items) == 2
        assert any(i.name == weapon.name for i in shop.store_items)
        assert any(i.name == elixir.name for i in shop.store_items)
        
        # Test store info
        info = shop.get_store_info()
        assert "出售：" in info
        assert weapon.name in info
        assert elixir.name in info
        
    finally:
        ItemRegistry._items_by_id = original_registry

def test_store_init_mixed_ids_and_names(mock_item_data):
    """Test backward compatibility: store init with both IDs and names."""
    original_registry = ItemRegistry._items_by_id.copy()
    ItemRegistry._items_by_id.clear()
    
    from src.classes.items.weapon import weapons_by_name
    original_weapons_by_name = weapons_by_name.copy()
    
    try:
        # We need `resolve_query` to work for names, which relies on 
        # weapons_by_name etc. populated in conftest or manually here.
        # Since we are mocking, we might need to patch resolve_query or ensure global dicts are populated.
        # For simplicity, we assume `resolve_query` logic works if global dicts are set.
        # But `mock_item_data` objects are fresh and NOT in global dicts by default unless we put them there.
        
        weapon = mock_item_data["obj_weapon"]
        weapon_id = weapon.id
        
        # Register weapon by ID
        ItemRegistry.register(weapon_id, weapon)
        
        # Prepare an item for Name lookup (not in Registry)
        # We need to mock `src.utils.resolution.resolve_query` or make `resolve_query` find it.
        # Ideally, `StoreMixin` uses `resolve_query` for strings.
        
        weapons_by_name[weapon.name] = weapon
        
        shop = MockShop()
        # Init with ID for weapon, and Name for weapon (redundant but testing logic)
        shop.init_store([weapon_id, weapon.name])
        
        # Should contain two instances of the same weapon (one found by ID, one by Name)
        assert len(shop.store_items) == 2
        assert shop.store_items[0] == weapon
        assert shop.store_items[1] == weapon
        
    finally:
        ItemRegistry._items_by_id = original_registry
        weapons_by_name.clear()
        weapons_by_name.update(original_weapons_by_name)

# --- Test Item Instantiation ---

def test_item_instantiation():
    """Test the Item.instantiate() method."""
    original = MockItem(1, "Original")
    original.some_attr = [1, 2, 3]
    
    clone = original.instantiate()
    
    assert clone is not original
    assert clone.id == original.id
    assert clone.name == original.name
    assert clone.some_attr == original.some_attr
    assert clone.some_attr is not original.some_attr # Deep copy check

