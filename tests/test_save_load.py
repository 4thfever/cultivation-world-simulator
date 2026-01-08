import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.classes.world import World
from src.classes.map import Map
from src.classes.tile import TileType
from src.classes.calendar import Month, Year, create_month_stamp
from src.classes.avatar import Avatar, Gender
from src.classes.age import Age
from src.classes.cultivation import Realm
from src.sim.simulator import Simulator
from src.sim.save.save_game import save_game
from src.sim.load.load_game import load_game
from src.utils.id_generator import get_avatar_id
from src.utils.config import CONFIG

# Helper to create a simple map (aligned with conftest base_map logic)
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

def test_save_load_cycle(temp_save_dir):
    """
    Test the full save and load cycle with a real World and Simulator instance,
    but without running the LLM or stepping the simulation.
    """
    # 1. Setup World
    # Create a deterministic map for testing
    game_map = create_test_map()
    
    # Set a specific time
    start_year = Year(100)
    start_month = Month.JANUARY
    month_stamp = create_month_stamp(start_year, start_month)
    
    world = World(map=game_map, month_stamp=month_stamp)

    
    # 2. Add an Avatar
    avatar_id = get_avatar_id()
    avatar_name = "TestUser_SaveLoad"
    avatar = Avatar(
        world=world,
        name=avatar_name,
        id=avatar_id,
        birth_month_stamp=create_month_stamp(Year(80), Month.JANUARY),
        age=Age(20, Realm.Qi_Refinement),
        gender=Gender.MALE
    )
    # Set some specific attributes to verify persistence
    # Note: hp.max is recalculated from realm and effects on load, so setting it manually
    # without a supporting effect will result in it being reset.
    # We test hp.cur persistence instead (as long as it's <= max).
    # Default max for Qi_Refinement is 100.
    avatar.hp.cur = 80
    
    # Add to world
    world.avatar_manager.avatars[avatar.id] = avatar
    
    # 3. Setup Simulator
    sim = Simulator(world)
    # Modify a config value on the instance to check if it persists
    test_birth_rate = 0.99 
    sim.birth_rate = test_birth_rate
    
    # 4. Prepare Existed Sects (Empty for this basic test)
    existed_sects = []

    # 5. Save Game
    save_filename = "test_save_cycle.json"
    save_path = temp_save_dir / save_filename
    
    success, saved_name = save_game(world, sim, existed_sects, save_path)
    
    assert success, "Save operation failed"
    assert save_path.exists(), "Save file was not created"
    
    # 6. Load Game
    # We need to patch 'load_cultivation_world_map' because load_game calls it.
    # We want it to return our simple map (or a new equivalent one) instead of loading the real huge map.
    # Note: load_game imports it inside the function, so we patch where it is imported FROM if it was global,
    # but since it's inside, we rely on sys.modules or patch the target module path.
    # The import in load_game.py is: from src.run.load_map import load_cultivation_world_map
    
    with patch('src.run.load_map.load_cultivation_world_map', return_value=create_test_map()):
        # We also need to be careful about 'sects_by_id' if we had sects, but we don't.
        loaded_world, loaded_sim, loaded_sects = load_game(save_path)
    
    # 7. Verification
    
    # Verify World Metadata
    assert loaded_world.month_stamp == world.month_stamp
    assert loaded_world.month_stamp.get_year() == 100
    
    # Verify Avatar
    assert len(loaded_world.avatar_manager.avatars) == 1
    assert avatar_id in loaded_world.avatar_manager.avatars
    
    loaded_avatar = loaded_world.avatar_manager.avatars[avatar_id]
    assert loaded_avatar.name == avatar_name
    assert loaded_avatar.age.age == 20
    assert loaded_avatar.cultivation_progress.realm == Realm.Qi_Refinement
    assert loaded_avatar.gender == Gender.MALE
    # hp.max is reset to 100 based on Realm.Qi_Refinement
    assert loaded_avatar.hp.max == 100
    assert loaded_avatar.hp.cur == 80
    
    # Verify Simulator
    assert loaded_sim.birth_rate == test_birth_rate
    
    # Verify World/Simulator linkage
    assert loaded_sim.world == loaded_world
    assert loaded_avatar.world == loaded_world

def test_save_load_with_relations(temp_save_dir):
    """
    Test saving and loading avatars with relationships.
    """
    game_map = create_test_map()
    world = World(map=game_map, month_stamp=create_month_stamp(Year(1), Month.JANUARY))
    
    # Create two avatars
    av1 = Avatar(world, "Av1", get_avatar_id(), create_month_stamp(Year(1), Month.JANUARY), Age(20, Realm.Qi_Refinement), Gender.MALE)
    av2 = Avatar(world, "Av2", get_avatar_id(), create_month_stamp(Year(1), Month.JANUARY), Age(20, Realm.Qi_Refinement), Gender.FEMALE)
    
    world.avatar_manager.avatars[av1.id] = av1
    world.avatar_manager.avatars[av2.id] = av2
    
    # Add relationship
    from src.classes.relation import Relation
    
    # Manually adding relation for test (usually done via helper methods)
    # relation value is integer
    av1.relations[av2] = Relation.FRIEND
    
    sim = Simulator(world)
    
    save_path = temp_save_dir / "test_relation.json"
    save_game(world, sim, [], save_path)
    
    with patch('src.run.load_map.load_cultivation_world_map', return_value=create_test_map()):
        l_world, _, _ = load_game(save_path)
        
    l_av1 = l_world.avatar_manager.avatars[av1.id]
    l_av2 = l_world.avatar_manager.avatars[av2.id]
    
    assert l_av2 in l_av1.relations
    assert l_av1.relations[l_av2] == Relation.FRIEND
