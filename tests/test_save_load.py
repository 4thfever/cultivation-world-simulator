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
from src.classes.event import Event
from src.classes.event_storage import EventStorage
from src.sim.simulator import Simulator
from src.sim.save.save_game import save_game
from src.sim.load.load_game import load_game, get_events_db_path
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
    sim.awakening_rate = test_birth_rate
    
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
    assert loaded_sim.awakening_rate == test_birth_rate
    
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


# =============================================================================
# SQLite Event Storage Tests
# =============================================================================

def make_event(
    year: int,
    month: int,
    content: str,
    avatar_ids: list[str] | None = None,
    is_major: bool = False,
    is_story: bool = False,
) -> Event:
    """Helper to create an Event."""
    month_stamp = create_month_stamp(Year(year), Month(month))
    return Event(
        month_stamp=month_stamp,
        content=content,
        related_avatars=avatar_ids,
        is_major=is_major,
        is_story=is_story,
    )


class TestGetEventsDbPath:
    """Tests for get_events_db_path utility function."""

    def test_json_to_db_path(self, tmp_path):
        """Test converting .json path to _events.db path."""
        save_path = tmp_path / "save_20260105_1423.json"
        db_path = get_events_db_path(save_path)

        assert db_path.name == "save_20260105_1423_events.db"
        assert db_path.parent == save_path.parent

    def test_nested_path(self, tmp_path):
        """Test with nested directory structure."""
        nested = tmp_path / "saves" / "slot1"
        nested.mkdir(parents=True)
        save_path = nested / "game.json"
        db_path = get_events_db_path(save_path)

        assert db_path == nested / "game_events.db"


class TestSaveLoadWithSQLiteEvents:
    """Tests for save/load cycle with SQLite event storage."""

    def test_save_creates_events_db_metadata(self, temp_save_dir):
        """Test that save_game records events_db info in meta."""
        game_map = create_test_map()
        month_stamp = create_month_stamp(Year(100), Month.JANUARY)
        events_db_path = temp_save_dir / "test_meta_events.db"

        world = World.create_with_db(
            map=game_map,
            month_stamp=month_stamp,
            events_db_path=events_db_path,
        )

        # Add some events.
        world.event_manager.add_event(make_event(100, 1, "Event 1"))
        world.event_manager.add_event(make_event(100, 2, "Event 2"))

        sim = Simulator(world)
        save_path = temp_save_dir / "test_meta.json"
        success, _ = save_game(world, sim, [], save_path)

        assert success

        # Check meta contains events_db info.
        with open(save_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        meta = data["meta"]
        assert "events_db" in meta
        assert "event_count" in meta
        assert meta["event_count"] == 2

        world.event_manager.close()

    def test_load_uses_sqlite_events(self, temp_save_dir):
        """Test that load_game connects to the correct SQLite database."""
        game_map = create_test_map()
        month_stamp = create_month_stamp(Year(100), Month.JANUARY)

        save_path = temp_save_dir / "test_sqlite.json"
        events_db_path = get_events_db_path(save_path)

        # Create world with SQLite storage.
        world = World.create_with_db(
            map=game_map,
            month_stamp=month_stamp,
            events_db_path=events_db_path,
        )

        # Add avatar and events.
        avatar_id = get_avatar_id()
        avatar = Avatar(
            world=world,
            name="TestAvatar",
            id=avatar_id,
            birth_month_stamp=create_month_stamp(Year(80), Month.JANUARY),
            age=Age(20, Realm.Qi_Refinement),
            gender=Gender.MALE,
        )
        world.avatar_manager.avatars[avatar.id] = avatar

        # Add events - some related to avatar, some not.
        world.event_manager.add_event(make_event(100, 1, "Avatar event 1", [avatar_id]))
        world.event_manager.add_event(make_event(100, 2, "World event"))
        world.event_manager.add_event(make_event(100, 3, "Avatar event 2", [avatar_id], is_major=True))

        original_count = world.event_manager.count()
        assert original_count == 3

        # Save.
        sim = Simulator(world)
        success, _ = save_game(world, sim, [], save_path)
        assert success

        # Verify DB file exists.
        assert events_db_path.exists()

        # Close original world.
        world.event_manager.close()

        # Load.
        with patch('src.run.load_map.load_cultivation_world_map', return_value=create_test_map()):
            loaded_world, _, _ = load_game(save_path)

        # Verify events are loaded from SQLite.
        assert loaded_world.event_manager.count() == 3

        # Verify event queries work.
        avatar_events = loaded_world.event_manager.get_events_by_avatar(avatar_id)
        assert len(avatar_events) == 2

        major_events = loaded_world.event_manager.get_major_events_by_avatar(avatar_id)
        assert len(major_events) == 1
        assert major_events[0].content == "Avatar event 2"

        loaded_world.event_manager.close()

    def test_load_migrates_json_events_to_sqlite(self, temp_save_dir):
        """Test that loading an old save (with JSON events) migrates to SQLite."""
        game_map = create_test_map()
        month_stamp = create_month_stamp(Year(100), Month.JANUARY)

        # Create a "legacy" save file with events in JSON (no _events.db).
        save_path = temp_save_dir / "legacy_save.json"
        events_db_path = get_events_db_path(save_path)

        # Make sure no DB exists.
        if events_db_path.exists():
            events_db_path.unlink()

        # Create legacy JSON save data.
        legacy_events = [
            make_event(100, 1, "Legacy event 1").to_dict(),
            make_event(100, 2, "Legacy event 2").to_dict(),
            make_event(100, 3, "Legacy event 3", is_major=True).to_dict(),
        ]

        legacy_save_data = {
            "meta": {"version": "1.0", "save_time": "2026-01-01", "game_time": "100年1月"},
            "world": {"month_stamp": int(month_stamp), "existed_sect_ids": []},
            "avatars": [],
            "events": legacy_events,
            "simulator": {"birth_rate": 0.1},
        }

        with open(save_path, "w") as f:
            json.dump(legacy_save_data, f)

        # Load - should migrate events to SQLite.
        with patch('src.run.load_map.load_cultivation_world_map', return_value=create_test_map()):
            loaded_world, _, _ = load_game(save_path)

        # Verify events were migrated.
        assert loaded_world.event_manager.count() == 3

        # Verify DB file was created.
        assert events_db_path.exists()

        # Verify events are queryable.
        events = loaded_world.event_manager.get_recent_events()
        assert len(events) == 3
        contents = [e.content for e in events]
        assert "Legacy event 1" in contents
        assert "Legacy event 2" in contents
        assert "Legacy event 3" in contents

        loaded_world.event_manager.close()

    def test_load_does_not_duplicate_events_on_reload(self, temp_save_dir):
        """Test that reloading a save doesn't duplicate events."""
        game_map = create_test_map()
        month_stamp = create_month_stamp(Year(100), Month.JANUARY)

        save_path = temp_save_dir / "test_no_dup.json"
        events_db_path = get_events_db_path(save_path)

        # Create and save.
        world = World.create_with_db(
            map=game_map,
            month_stamp=month_stamp,
            events_db_path=events_db_path,
        )

        world.event_manager.add_event(make_event(100, 1, "Event 1"))
        world.event_manager.add_event(make_event(100, 2, "Event 2"))

        sim = Simulator(world)
        save_game(world, sim, [], save_path)
        world.event_manager.close()

        # Load twice.
        for _ in range(2):
            with patch('src.run.load_map.load_cultivation_world_map', return_value=create_test_map()):
                loaded_world, _, _ = load_game(save_path)
            # Should still be 2, not 4 or 6.
            assert loaded_world.event_manager.count() == 2
            loaded_world.event_manager.close()

    def test_multiple_saves_have_separate_event_dbs(self, temp_save_dir):
        """Test that different saves use different event databases."""
        game_map = create_test_map()

        # Create first save.
        save_path1 = temp_save_dir / "save1.json"
        events_db_path1 = get_events_db_path(save_path1)
        month_stamp1 = create_month_stamp(Year(100), Month.JANUARY)

        world1 = World.create_with_db(
            map=game_map,
            month_stamp=month_stamp1,
            events_db_path=events_db_path1,
        )
        world1.event_manager.add_event(make_event(100, 1, "Save1 Event 1"))
        world1.event_manager.add_event(make_event(100, 2, "Save1 Event 2"))

        sim1 = Simulator(world1)
        save_game(world1, sim1, [], save_path1)
        world1.event_manager.close()

        # Create second save with different events.
        save_path2 = temp_save_dir / "save2.json"
        events_db_path2 = get_events_db_path(save_path2)
        month_stamp2 = create_month_stamp(Year(200), Month.JUNE)

        world2 = World.create_with_db(
            map=game_map,
            month_stamp=month_stamp2,
            events_db_path=events_db_path2,
        )
        world2.event_manager.add_event(make_event(200, 6, "Save2 Event 1"))
        world2.event_manager.add_event(make_event(200, 7, "Save2 Event 2"))
        world2.event_manager.add_event(make_event(200, 8, "Save2 Event 3"))

        sim2 = Simulator(world2)
        save_game(world2, sim2, [], save_path2)
        world2.event_manager.close()

        # Load save1 and verify its events.
        with patch('src.run.load_map.load_cultivation_world_map', return_value=create_test_map()):
            loaded1, _, _ = load_game(save_path1)

        assert loaded1.event_manager.count() == 2
        events1 = loaded1.event_manager.get_recent_events()
        assert all("Save1" in e.content for e in events1)
        loaded1.event_manager.close()

        # Load save2 and verify its events.
        with patch('src.run.load_map.load_cultivation_world_map', return_value=create_test_map()):
            loaded2, _, _ = load_game(save_path2)

        assert loaded2.event_manager.count() == 3
        events2 = loaded2.event_manager.get_recent_events()
        assert all("Save2" in e.content for e in events2)
        loaded2.event_manager.close()


class TestEventPaginationAfterLoad:
    """Tests for event pagination functionality after loading."""

    def test_pagination_works_after_load(self, temp_save_dir):
        """Test that event pagination works correctly after loading a save."""
        game_map = create_test_map()
        month_stamp = create_month_stamp(Year(100), Month.JANUARY)

        save_path = temp_save_dir / "test_pagination.json"
        events_db_path = get_events_db_path(save_path)

        world = World.create_with_db(
            map=game_map,
            month_stamp=month_stamp,
            events_db_path=events_db_path,
        )

        # Add 25 events.
        for i in range(25):
            year = 100 + (i // 12)
            month = (i % 12) + 1
            world.event_manager.add_event(make_event(year, month, f"Event {i}"))

        sim = Simulator(world)
        save_game(world, sim, [], save_path)
        world.event_manager.close()

        # Load and test pagination.
        with patch('src.run.load_map.load_cultivation_world_map', return_value=create_test_map()):
            loaded_world, _, _ = load_game(save_path)

        # First page.
        page1, cursor1, has_more1 = loaded_world.event_manager.get_events_paginated(limit=10)
        assert len(page1) == 10
        assert has_more1 is True
        assert cursor1 is not None

        # Second page.
        page2, cursor2, has_more2 = loaded_world.event_manager.get_events_paginated(limit=10, cursor=cursor1)
        assert len(page2) == 10
        assert has_more2 is True

        # Third page (only 5 remaining).
        page3, cursor3, has_more3 = loaded_world.event_manager.get_events_paginated(limit=10, cursor=cursor2)
        assert len(page3) == 5
        assert has_more3 is False
        assert cursor3 is None

        # Verify no duplicates.
        all_ids = {e.id for e in page1} | {e.id for e in page2} | {e.id for e in page3}
        assert len(all_ids) == 25

        loaded_world.event_manager.close()

    def test_avatar_filter_works_after_load(self, temp_save_dir):
        """Test that avatar filtering works correctly after loading."""
        game_map = create_test_map()
        month_stamp = create_month_stamp(Year(100), Month.JANUARY)

        save_path = temp_save_dir / "test_filter.json"
        events_db_path = get_events_db_path(save_path)

        world = World.create_with_db(
            map=game_map,
            month_stamp=month_stamp,
            events_db_path=events_db_path,
        )

        avatar1_id = get_avatar_id()
        avatar2_id = get_avatar_id()

        # Add events for different avatars.
        world.event_manager.add_event(make_event(100, 1, "Avatar1 only", [avatar1_id]))
        world.event_manager.add_event(make_event(100, 2, "Avatar2 only", [avatar2_id]))
        world.event_manager.add_event(make_event(100, 3, "Both avatars", [avatar1_id, avatar2_id]))
        world.event_manager.add_event(make_event(100, 4, "World event"))

        sim = Simulator(world)
        save_game(world, sim, [], save_path)
        world.event_manager.close()

        # Load and test filtering.
        with patch('src.run.load_map.load_cultivation_world_map', return_value=create_test_map()):
            loaded_world, _, _ = load_game(save_path)

        # Filter by avatar1.
        avatar1_events = loaded_world.event_manager.get_events_by_avatar(avatar1_id)
        assert len(avatar1_events) == 2
        contents = [e.content for e in avatar1_events]
        assert "Avatar1 only" in contents
        assert "Both avatars" in contents

        # Filter by pair.
        pair_events = loaded_world.event_manager.get_events_between(avatar1_id, avatar2_id)
        assert len(pair_events) == 1
        assert pair_events[0].content == "Both avatars"

        # Paginated filter.
        page, cursor, has_more = loaded_world.event_manager.get_events_paginated(avatar_id=avatar1_id)
        assert len(page) == 2

        loaded_world.event_manager.close()


class TestEventCleanupAfterLoad:
    """Tests for event cleanup functionality after loading."""

    def test_cleanup_works_after_load(self, temp_save_dir):
        """Test that event cleanup works correctly after loading."""
        game_map = create_test_map()
        month_stamp = create_month_stamp(Year(100), Month.JANUARY)

        save_path = temp_save_dir / "test_cleanup.json"
        events_db_path = get_events_db_path(save_path)

        world = World.create_with_db(
            map=game_map,
            month_stamp=month_stamp,
            events_db_path=events_db_path,
        )

        # Add mix of major and minor events.
        world.event_manager.add_event(make_event(100, 1, "Minor 1", is_major=False))
        world.event_manager.add_event(make_event(100, 2, "Major 1", is_major=True))
        world.event_manager.add_event(make_event(100, 3, "Minor 2", is_major=False))
        world.event_manager.add_event(make_event(100, 4, "Major 2", is_major=True))

        sim = Simulator(world)
        save_game(world, sim, [], save_path)
        world.event_manager.close()

        # Load and cleanup.
        with patch('src.run.load_map.load_cultivation_world_map', return_value=create_test_map()):
            loaded_world, _, _ = load_game(save_path)

        assert loaded_world.event_manager.count() == 4

        # Cleanup minor events (keep major).
        deleted = loaded_world.event_manager.cleanup(keep_major=True)
        assert deleted == 2
        assert loaded_world.event_manager.count() == 2

        # Verify only major events remain.
        events = loaded_world.event_manager.get_recent_events()
        assert all(e.is_major for e in events)

        loaded_world.event_manager.close()


class TestDatabaseSwitchingOnLoad:
    """Tests specifically for the database switching bug that was fixed."""

    def test_load_switches_to_correct_database(self, temp_save_dir):
        """
        Test that loading a different save properly switches the event database.

        This tests the bug where loading a save would still query the old database.
        """
        game_map = create_test_map()

        # Create "current" session with some events.
        current_db_path = temp_save_dir / "current_events.db"
        current_world = World.create_with_db(
            map=game_map,
            month_stamp=create_month_stamp(Year(100), Month.JANUARY),
            events_db_path=current_db_path,
        )
        current_world.event_manager.add_event(make_event(100, 1, "Current session event"))
        current_event_count = current_world.event_manager.count()
        assert current_event_count == 1

        # Create a different save with more events.
        other_save_path = temp_save_dir / "other_save.json"
        other_db_path = get_events_db_path(other_save_path)

        other_world = World.create_with_db(
            map=game_map,
            month_stamp=create_month_stamp(Year(200), Month.JUNE),
            events_db_path=other_db_path,
        )

        # Add 10 events to other save.
        for i in range(10):
            other_world.event_manager.add_event(make_event(200, i % 12 + 1, f"Other save event {i}"))

        sim = Simulator(other_world)
        save_game(other_world, sim, [], other_save_path)
        other_world.event_manager.close()

        # Now "load" the other save (simulating what main.py does).
        # Close current world's event manager first.
        current_world.event_manager.close()

        with patch('src.run.load_map.load_cultivation_world_map', return_value=create_test_map()):
            loaded_world, _, _ = load_game(other_save_path)

        # The loaded world should have 10 events, not 1.
        assert loaded_world.event_manager.count() == 10

        # Verify it's querying the correct database.
        events = loaded_world.event_manager.get_recent_events()
        assert all("Other save event" in e.content for e in events)

        # Pagination should work.
        page, cursor, has_more = loaded_world.event_manager.get_events_paginated(limit=5)
        assert len(page) == 5
        assert has_more is True

        loaded_world.event_manager.close()

    def test_events_persist_across_save_load_cycle(self, temp_save_dir):
        """Test that events added before save are available after load."""
        game_map = create_test_map()

        save_path = temp_save_dir / "persist_test.json"
        events_db_path = get_events_db_path(save_path)

        # Create world, add events, save.
        world = World.create_with_db(
            map=game_map,
            month_stamp=create_month_stamp(Year(100), Month.JANUARY),
            events_db_path=events_db_path,
        )

        avatar_id = get_avatar_id()
        avatar = Avatar(
            world=world,
            name="TestAvatar",
            id=avatar_id,
            birth_month_stamp=create_month_stamp(Year(80), Month.JANUARY),
            age=Age(20, Realm.Qi_Refinement),
            gender=Gender.MALE,
        )
        world.avatar_manager.avatars[avatar.id] = avatar

        # Add various events.
        world.event_manager.add_event(make_event(100, 1, "Birth event", [avatar_id], is_major=True))
        world.event_manager.add_event(make_event(100, 2, "Training event", [avatar_id]))
        world.event_manager.add_event(make_event(100, 3, "World announcement"))

        sim = Simulator(world)
        save_game(world, sim, [], save_path)

        # Get event count before closing.
        original_count = world.event_manager.count()
        original_avatar_events = len(world.event_manager.get_events_by_avatar(avatar_id))

        world.event_manager.close()

        # Load and verify.
        with patch('src.run.load_map.load_cultivation_world_map', return_value=create_test_map()):
            loaded_world, _, _ = load_game(save_path)

        assert loaded_world.event_manager.count() == original_count
        assert len(loaded_world.event_manager.get_events_by_avatar(avatar_id)) == original_avatar_events

        # Check specific event content.
        major_events = loaded_world.event_manager.get_major_events_by_avatar(avatar_id)
        assert len(major_events) == 1
        assert major_events[0].content == "Birth event"

        loaded_world.event_manager.close()


# API Load Game Tests - Race Condition Prevention
# =============================================================================

class TestApiLoadGamePausesGame:
    """
    Tests for the race condition fix in api_load_game.
    
    The bug: When loading a save, the game_loop could still be running with the
    old world, generating events with stale timestamps (e.g., 100年1月 events
    appearing after loading a 106年 save).
    
    The fix: Pause the game before loading and keep it paused after.
    """

    def test_load_game_pauses_game_instance(self, temp_save_dir):
        """Test that api_load_game sets is_paused to True."""
        from fastapi.testclient import TestClient
        from src.server import main

        # Create a simple save file.
        game_map = create_test_map()
        month_stamp = create_month_stamp(Year(200), Month.JUNE)
        world = World(map=game_map, month_stamp=month_stamp)

        avatar = Avatar(
            world=world,
            name="TestAvatar",
            id=get_avatar_id(),
            birth_month_stamp=create_month_stamp(Year(180), Month.JANUARY),
            age=Age(20, Realm.Qi_Refinement),
            gender=Gender.MALE,
        )
        world.avatar_manager.avatars[avatar.id] = avatar

        sim = Simulator(world)
        save_path = temp_save_dir / "test_pause.json"
        save_game(world, sim, [], save_path)

        # Setup: game is running (not paused).
        original_state = main.game_instance.copy()
        main.game_instance["is_paused"] = False
        main.game_instance["world"] = World(
            map=create_test_map(),
            month_stamp=create_month_stamp(Year(100), Month.JANUARY),
        )
        main.game_instance["sim"] = MagicMock()

        # Mock CONFIG.paths.saves to point to our temp dir.
        with patch.object(CONFIG.paths, "saves", temp_save_dir):
            with patch('src.run.load_map.load_cultivation_world_map', return_value=create_test_map()):
                client = TestClient(main.app)
                response = client.post(
                    "/api/game/load",
                    json={"filename": "test_pause.json"}
                )

        assert response.status_code == 200

        # Key assertion: game should be paused after load.
        assert main.game_instance["is_paused"] is True

        # Verify the world was actually replaced.
        assert main.game_instance["world"].month_stamp.get_year() == 200

        # Cleanup.
        main.game_instance.update(original_state)

    def test_load_game_prevents_stale_events(self, temp_save_dir):
        """
        Test that pausing during load prevents events with old timestamps.
        
        This simulates the race condition scenario:
        1. Old world is at 100年1月
        2. User loads a save from 200年6月
        3. Without the fix, game_loop might generate 100年1月 events
        4. With the fix, game is paused so no stale events are generated
        """
        from src.server import main

        # Create a save at 200年.
        game_map = create_test_map()
        save_world = World(
            map=game_map,
            month_stamp=create_month_stamp(Year(200), Month.JUNE),
        )
        sim = Simulator(save_world)
        save_path = temp_save_dir / "test_stale.json"
        save_game(save_world, sim, [], save_path)

        # Setup: "old" world at 100年.
        old_world = World(
            map=create_test_map(),
            month_stamp=create_month_stamp(Year(100), Month.JANUARY),
        )

        original_state = main.game_instance.copy()
        main.game_instance["world"] = old_world
        main.game_instance["sim"] = Simulator(old_world)
        main.game_instance["is_paused"] = False

        # Simulate what happens during load.
        # Before the fix, is_paused would remain False during load_game().
        # After the fix, is_paused is set to True before load_game().

        # Verify initial state.
        assert main.game_instance["is_paused"] is False
        assert main.game_instance["world"].month_stamp.get_year() == 100

        # Perform load (this should pause the game).
        with patch.object(CONFIG.paths, "saves", temp_save_dir):
            with patch('src.run.load_map.load_cultivation_world_map', return_value=create_test_map()):
                from fastapi.testclient import TestClient
                client = TestClient(main.app)
                response = client.post(
                    "/api/game/load",
                    json={"filename": "test_stale.json"}
                )

        assert response.status_code == 200

        # After load: game is paused, world is updated.
        assert main.game_instance["is_paused"] is True
        assert main.game_instance["world"].month_stamp.get_year() == 200

        # The key point: because is_paused is True, game_loop will skip
        # sim.step(), so no events with stale timestamps (100年) will be
        # generated. The frontend will receive a clean state at 200年.

        # Cleanup.
        main.game_instance.update(original_state)
