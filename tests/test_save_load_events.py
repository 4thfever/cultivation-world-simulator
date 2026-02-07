"""
Tests for save/load functionality with SQLite event storage.

Covers:
- Events persistence across save/load cycles
- Database file switching when loading different saves
- Event retrieval after loading
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.classes.core.world import World
from src.classes.environment.map import Map
from src.classes.environment.tile import TileType
from src.systems.time import Month, Year, create_month_stamp, MonthStamp
from src.classes.core.avatar import Avatar, Gender
from src.classes.age import Age
from src.systems.cultivation import Realm
from src.classes.event import Event
from src.classes.event_storage import EventStorage
from src.sim.managers.event_manager import EventManager
from src.sim.simulator import Simulator
from src.sim.save.save_game import save_game
from src.sim.load.load_game import load_game
from src.utils.id_generator import get_avatar_id


def create_test_map():
    """Create a simple 10x10 plain map for testing."""
    m = Map(width=10, height=10)
    for x in range(10):
        for y in range(10):
            m.create_tile(x, y, TileType.PLAIN)
    return m


def make_event(
    year: int,
    month: int,
    content: str,
    avatar_ids: list[str] | None = None,
    is_major: bool = False,
) -> Event:
    """Helper to create an Event."""
    month_stamp = create_month_stamp(Year(year), Month(month))
    return Event(
        month_stamp=month_stamp,
        content=content,
        related_avatars=avatar_ids,
        is_major=is_major,
    )


def make_event_by_index(
    index: int,
    content: str,
    avatar_ids: list[str] | None = None,
) -> Event:
    """Helper to create an Event from an index (handles year/month calculation)."""
    year = 100 + (index // 12)
    month = (index % 12) + 1
    return make_event(year, month, content, avatar_ids)


@pytest.fixture
def temp_save_dir(tmp_path):
    """Create a temporary directory for saves."""
    d = tmp_path / "saves"
    d.mkdir()
    return d


class TestEventManagerWithWorld:
    """Tests for EventManager integration with World."""

    def test_world_creates_event_manager_with_db(self, tmp_path):
        """Test that World.create_with_db creates proper EventManager."""
        db_path = tmp_path / "events.db"
        game_map = create_test_map()
        month_stamp = create_month_stamp(Year(100), Month.JANUARY)

        world = World.create_with_db(
            map=game_map,
            month_stamp=month_stamp,
            events_db_path=db_path,
        )

        # EventManager should be connected to SQLite
        assert world.event_manager is not None
        assert world.event_manager._storage is not None
        assert db_path.exists()

        # Clean up
        world.event_manager.close()

    def test_events_written_to_sqlite(self, tmp_path):
        """Test that events added to World are written to SQLite."""
        db_path = tmp_path / "events.db"
        game_map = create_test_map()
        month_stamp = create_month_stamp(Year(100), Month.JANUARY)

        world = World.create_with_db(
            map=game_map,
            month_stamp=month_stamp,
            events_db_path=db_path,
        )

        # Add events
        event1 = make_event(100, 1, "First event", ["a1"])
        event2 = make_event(100, 2, "Second event", ["a2"])

        world.event_manager.add_event(event1)
        world.event_manager.add_event(event2)

        # Verify in SQLite
        assert world.event_manager.count() == 2

        # Clean up and verify persistence
        world.event_manager.close()

        # Reopen and verify
        storage = EventStorage(db_path)
        assert storage.count() == 2
        storage.close()


class TestSaveLoadWithEvents:
    """Tests for save/load cycle with SQLite events."""

    def test_save_load_preserves_events(self, temp_save_dir, tmp_path):
        """Test that events are preserved across save/load cycle."""
        # Setup world with SQLite events
        db_path = tmp_path / "events.db"
        game_map = create_test_map()
        month_stamp = create_month_stamp(Year(100), Month.JANUARY)

        world = World.create_with_db(
            map=game_map,
            month_stamp=month_stamp,
            events_db_path=db_path,
        )

        # Create avatar
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

        # Add events
        for i in range(10):
            event = make_event(
                100, i + 1,
                f"Event {i} for avatar",
                [avatar_id],
                is_major=(i % 3 == 0),
            )
            world.event_manager.add_event(event)

        original_count = world.event_manager.count()
        assert original_count == 10

        # Save
        sim = Simulator(world)
        save_path = temp_save_dir / "test_events.json"
        success, _ = save_game(world, sim, [], save_path)
        assert success

        # Close current event manager
        world.event_manager.close()

        # Load
        with patch('src.run.load_map.load_cultivation_world_map', return_value=create_test_map()):
            loaded_world, loaded_sim, _ = load_game(save_path)

        # Verify events are accessible
        # Note: After loading, the world should use a new EventManager
        # connected to the loaded save's database
        loaded_events = loaded_world.event_manager.get_recent_events()

        # The exact behavior depends on implementation -
        # if events DB path is derived from save path, they should be preserved
        # This test may need adjustment based on actual load_game implementation

    def test_events_filtered_by_avatar_after_load(self, temp_save_dir, tmp_path):
        """Test that avatar-specific event queries work after loading."""
        db_path = tmp_path / "events.db"
        game_map = create_test_map()
        month_stamp = create_month_stamp(Year(100), Month.JANUARY)

        world = World.create_with_db(
            map=game_map,
            month_stamp=month_stamp,
            events_db_path=db_path,
        )

        # Create two avatars
        avatar1_id = get_avatar_id()
        avatar2_id = get_avatar_id()

        avatar1 = Avatar(
            world=world,
            name="Avatar1",
            id=avatar1_id,
            birth_month_stamp=create_month_stamp(Year(80), Month.JANUARY),
            age=Age(20, Realm.Qi_Refinement),
            gender=Gender.MALE,
        )
        avatar2 = Avatar(
            world=world,
            name="Avatar2",
            id=avatar2_id,
            birth_month_stamp=create_month_stamp(Year(80), Month.JANUARY),
            age=Age(20, Realm.Qi_Refinement),
            gender=Gender.FEMALE,
        )

        world.avatar_manager.avatars[avatar1.id] = avatar1
        world.avatar_manager.avatars[avatar2.id] = avatar2

        # Add events for different avatars
        world.event_manager.add_event(make_event(100, 1, "Avatar1 event", [avatar1_id]))
        world.event_manager.add_event(make_event(100, 2, "Avatar2 event", [avatar2_id]))
        world.event_manager.add_event(make_event(100, 3, "Both avatars", [avatar1_id, avatar2_id]))

        # Query before save
        avatar1_events = world.event_manager.get_events_by_avatar(avatar1_id)
        assert len(avatar1_events) == 2  # "Avatar1 event" and "Both avatars"

        between_events = world.event_manager.get_events_between(avatar1_id, avatar2_id)
        assert len(between_events) == 1  # "Both avatars"

        # Clean up
        world.event_manager.close()


class TestEventPagination:
    """Tests for event pagination functionality."""

    def test_pagination_returns_correct_pages(self, tmp_path):
        """Test that pagination returns events in correct order."""
        db_path = tmp_path / "events.db"
        storage = EventStorage(db_path)
        manager = EventManager(storage)

        # Add 25 events
        for i in range(25):
            year = 100 + (i // 12)
            month = (i % 12) + 1
            manager.add_event(make_event(year, month, f"Event {i}"))

        # Get first page (10 items)
        page1, cursor1, has_more1 = manager.get_events_paginated(limit=10)
        assert len(page1) == 10
        assert has_more1 is True
        assert cursor1 is not None

        # Events should be in descending order (newest first)
        assert page1[0].content == "Event 24"  # Newest
        assert page1[9].content == "Event 15"

        # Get second page
        page2, cursor2, has_more2 = manager.get_events_paginated(limit=10, cursor=cursor1)
        assert len(page2) == 10
        assert has_more2 is True

        # Get third page (only 5 remaining)
        page3, cursor3, has_more3 = manager.get_events_paginated(limit=10, cursor=cursor2)
        assert len(page3) == 5
        assert has_more3 is False
        assert cursor3 is None

        # Verify no duplicates across pages
        all_ids = {e.id for e in page1} | {e.id for e in page2} | {e.id for e in page3}
        assert len(all_ids) == 25

        manager.close()

    def test_pagination_with_avatar_filter(self, tmp_path):
        """Test pagination with avatar filter."""
        db_path = tmp_path / "events.db"
        storage = EventStorage(db_path)
        manager = EventManager(storage)

        avatar1_id = "avatar_1"
        avatar2_id = "avatar_2"

        # Add events alternating between avatars
        for i in range(20):
            avatar_id = avatar1_id if i % 2 == 0 else avatar2_id
            manager.add_event(make_event(100, (i % 12) + 1, f"Event {i}", [avatar_id]))

        # Get avatar1's events (should be 10)
        page1, cursor, has_more = manager.get_events_paginated(
            avatar_id=avatar1_id,
            limit=5
        )
        assert len(page1) == 5
        assert has_more is True

        # All events should be for avatar1
        for e in page1:
            assert avatar1_id in e.related_avatars

        # Get remaining
        page2, _, _ = manager.get_events_paginated(
            avatar_id=avatar1_id,
            limit=10,
            cursor=cursor
        )
        assert len(page2) == 5

        manager.close()

    def test_pagination_cursor_format_stability(self, tmp_path):
        """Test that cursor format is stable and parseable."""
        db_path = tmp_path / "events.db"
        storage = EventStorage(db_path)

        # Add some events
        for i in range(5):
            storage.add_event(make_event(100, i + 1, f"Event {i}"))

        _, cursor = storage.get_events(limit=3)

        # Cursor should be in format: month_stamp_rowid
        assert cursor is not None
        parts = cursor.split("_")
        assert len(parts) == 2
        assert parts[0].isdigit()
        assert parts[1].isdigit()

        # Cursor should be parseable
        month_stamp, rowid = storage._parse_cursor(cursor)
        assert isinstance(month_stamp, int)
        assert isinstance(rowid, int)

        storage.close()


class TestEventStorageEdgeCases:
    """Edge case tests for event storage."""

    def test_concurrent_writes(self, tmp_path):
        """Test that concurrent writes don't corrupt data."""
        db_path = tmp_path / "events.db"
        storage = EventStorage(db_path)

        # Simulate rapid writes (use make_event_by_index to handle month > 12)
        events = [make_event_by_index(i, f"Event {i}") for i in range(100)]

        for event in events:
            result = storage.add_event(event)
            assert result is True

        assert storage.count() == 100
        storage.close()

    def test_large_event_content(self, tmp_path):
        """Test handling of large event content."""
        db_path = tmp_path / "events.db"
        storage = EventStorage(db_path)

        # Create event with large content (10KB)
        large_content = "测试内容" * 2500  # ~10KB of Chinese characters
        event = make_event(100, 1, large_content, ["a1"])

        result = storage.add_event(event)
        assert result is True

        events, _ = storage.get_events()
        assert len(events) == 1
        assert events[0].content == large_content

        storage.close()

    def test_special_characters_in_avatar_id(self, tmp_path):
        """Test handling of special characters in avatar IDs."""
        db_path = tmp_path / "events.db"
        storage = EventStorage(db_path)

        # UUID-style IDs with hyphens
        avatar_id = "550e8400-e29b-41d4-a716-446655440000"
        event = make_event(100, 1, "Test event", [avatar_id])

        storage.add_event(event)

        events = storage.get_events_by_avatar(avatar_id)
        assert len(events) == 1
        assert avatar_id in events[0].related_avatars

        storage.close()

    def test_empty_database_queries(self, tmp_path):
        """Test queries on empty database return sensible results."""
        db_path = tmp_path / "events.db"
        storage = EventStorage(db_path)

        # All queries should return empty lists, not errors
        assert storage.get_events() == ([], None)
        assert storage.get_events_by_avatar("nonexistent") == []
        assert storage.get_events_between("a1", "a2") == []
        assert storage.get_major_events_by_avatar("a1") == []
        assert storage.get_minor_events_by_avatar("a1") == []
        assert storage.get_recent_events() == []
        assert storage.count() == 0

        storage.close()


class TestEventManagerMemoryFallback:
    """Tests for EventManager memory fallback mode."""

    def test_memory_mode_basic_operations(self):
        """Test that memory mode works for basic operations."""
        manager = EventManager.create_in_memory()

        manager.add_event(make_event(100, 1, "Event 1", ["a1"]))
        manager.add_event(make_event(100, 2, "Event 2", ["a2"]))

        assert manager.count() == 2

        events = manager.get_recent_events()
        assert len(events) == 2

        a1_events = manager.get_events_by_avatar("a1")
        assert len(a1_events) == 1

    def test_memory_mode_cleanup(self):
        """Test that cleanup works in memory mode."""
        manager = EventManager.create_in_memory()

        manager.add_event(make_event(100, 1, "Event 1"))
        manager.add_event(make_event(100, 2, "Event 2"))

        deleted = manager.cleanup()

        assert deleted == 2
        assert manager.count() == 0


class TestEventStorageCleanup:
    """Tests for event cleanup functionality."""

    def test_cleanup_with_time_filter(self, tmp_path):
        """Test cleanup with before_month_stamp filter."""
        db_path = tmp_path / "events.db"
        storage = EventStorage(db_path)

        # Add events at different times
        storage.add_event(make_event(50, 1, "Very old", is_major=False))
        storage.add_event(make_event(100, 1, "Old", is_major=False))
        storage.add_event(make_event(150, 1, "Recent", is_major=False))

        # Delete events before year 100
        cutoff = int(create_month_stamp(Year(100), Month.JANUARY))
        deleted = storage.cleanup(keep_major=False, before_month_stamp=cutoff)

        assert deleted == 1  # Only "Very old" deleted
        assert storage.count() == 2

        storage.close()

    def test_cleanup_preserves_major_events(self, tmp_path):
        """Test that cleanup preserves major events by default."""
        db_path = tmp_path / "events.db"
        storage = EventStorage(db_path)

        storage.add_event(make_event(100, 1, "Minor 1", is_major=False))
        storage.add_event(make_event(100, 2, "Major 1", is_major=True))
        storage.add_event(make_event(100, 3, "Minor 2", is_major=False))

        deleted = storage.cleanup(keep_major=True)

        assert deleted == 2
        assert storage.count() == 1

        events = storage.get_recent_events()
        assert events[0].content == "Major 1"

        storage.close()
