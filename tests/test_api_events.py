"""
Tests for the Events API endpoints.

Covers:
- GET /api/events - pagination and filtering
- DELETE /api/events/cleanup - event cleanup

Uses FastAPI TestClient to test the API directly.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

from src.classes.core.world import World
from src.classes.environment.map import Map
from src.classes.environment.tile import TileType
from src.systems.time import Month, Year, create_month_stamp
from src.classes.event import Event
from src.classes.event_storage import EventStorage
from src.sim.managers.event_manager import EventManager


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


@pytest.fixture
def temp_db_path():
    """Create a temporary database file path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test_events.db"


@pytest.fixture
def mock_world_with_events(temp_db_path):
    """Create a mock world with event manager."""
    game_map = create_test_map()
    month_stamp = create_month_stamp(Year(100), Month.JANUARY)

    world = World.create_with_db(
        map=game_map,
        month_stamp=month_stamp,
        events_db_path=temp_db_path,
    )

    # Add some test events
    world.event_manager.add_event(make_event(100, 1, "Event 1", ["a1"]))
    world.event_manager.add_event(make_event(100, 2, "Event 2", ["a2"]))
    world.event_manager.add_event(make_event(100, 3, "Event between", ["a1", "a2"]))
    world.event_manager.add_event(make_event(100, 4, "Major event", ["a1"], is_major=True))
    world.event_manager.add_event(make_event(100, 5, "Story event", ["a1"], is_story=True))

    yield world

    world.event_manager.close()


@pytest.fixture
def client_with_world(mock_world_with_events):
    """Create a TestClient with mocked game_instance."""
    # We need to patch the game_instance in main.py
    from src.server import main

    # Backup original
    original_instance = main.game_instance.copy()

    # Set up mock
    main.game_instance["world"] = mock_world_with_events
    main.game_instance["sim"] = MagicMock()
    main.game_instance["is_paused"] = True

    client = TestClient(main.app)
    yield client

    # Restore
    main.game_instance.update(original_instance)


class TestGetEventsAPI:
    """Tests for GET /api/events endpoint."""

    def test_get_events_returns_all(self, client_with_world):
        """Test getting all events without filters."""
        response = client_with_world.get("/api/events")

        assert response.status_code == 200
        data = response.json()

        assert "events" in data
        assert "next_cursor" in data
        assert "has_more" in data

        assert len(data["events"]) == 5
        assert data["has_more"] is False

    def test_get_events_with_limit(self, client_with_world):
        """Test pagination with limit parameter."""
        response = client_with_world.get("/api/events?limit=2")

        assert response.status_code == 200
        data = response.json()

        assert len(data["events"]) == 2
        assert data["has_more"] is True
        assert data["next_cursor"] is not None

    def test_get_events_pagination_cursor(self, client_with_world):
        """Test pagination with cursor."""
        # First page
        response1 = client_with_world.get("/api/events?limit=3")
        data1 = response1.json()

        cursor = data1["next_cursor"]
        assert cursor is not None

        # Second page
        response2 = client_with_world.get(f"/api/events?limit=3&cursor={cursor}")
        data2 = response2.json()

        assert len(data2["events"]) == 2  # 5 total, 3 in first page

        # No overlap in event IDs
        ids1 = {e["id"] for e in data1["events"]}
        ids2 = {e["id"] for e in data2["events"]}
        assert ids1.isdisjoint(ids2)

    def test_get_events_by_avatar(self, client_with_world):
        """Test filtering by single avatar."""
        response = client_with_world.get("/api/events?avatar_id=a1")

        assert response.status_code == 200
        data = response.json()

        # a1 has: Event 1, Event between, Major event, Story event
        assert len(data["events"]) == 4

        for event in data["events"]:
            assert "a1" in event["related_avatar_ids"]

    def test_get_events_by_avatar_pair(self, client_with_world):
        """Test filtering by avatar pair."""
        response = client_with_world.get("/api/events?avatar_id_1=a1&avatar_id_2=a2")

        assert response.status_code == 200
        data = response.json()

        # Only "Event between" involves both
        assert len(data["events"]) == 1
        assert data["events"][0]["content"] == "Event between"

    def test_get_events_returns_correct_structure(self, client_with_world):
        """Test that events have correct structure."""
        response = client_with_world.get("/api/events?limit=1")

        assert response.status_code == 200
        data = response.json()

        assert len(data["events"]) == 1
        event = data["events"][0]

        # Check required fields
        assert "id" in event
        assert "text" in event
        assert "content" in event
        assert "year" in event
        assert "month" in event
        assert "month_stamp" in event
        assert "related_avatar_ids" in event
        assert "is_major" in event
        assert "is_story" in event

    def test_get_events_no_world(self):
        """Test API response when no world is loaded."""
        from src.server import main

        original = main.game_instance.copy()
        main.game_instance["world"] = None

        try:
            client = TestClient(main.app)
            response = client.get("/api/events")

            assert response.status_code == 200
            data = response.json()

            assert data["events"] == []
            assert data["next_cursor"] is None
            assert data["has_more"] is False
        finally:
            main.game_instance.update(original)


class TestCleanupEventsAPI:
    """Tests for DELETE /api/events/cleanup endpoint."""

    def test_cleanup_deletes_minor_events(self, client_with_world, mock_world_with_events):
        """Test that cleanup deletes minor events."""
        initial_count = mock_world_with_events.event_manager.count()

        response = client_with_world.delete("/api/events/cleanup")

        assert response.status_code == 200
        data = response.json()

        # Should delete non-major events (4 of them)
        assert data["deleted"] == 4
        assert mock_world_with_events.event_manager.count() == 1

    def test_cleanup_with_keep_major_false(self, client_with_world, mock_world_with_events):
        """Test cleanup with keep_major=false deletes all."""
        response = client_with_world.delete("/api/events/cleanup?keep_major=false")

        assert response.status_code == 200
        data = response.json()

        assert data["deleted"] == 5
        assert mock_world_with_events.event_manager.count() == 0

    def test_cleanup_with_before_month_stamp(self, client_with_world, mock_world_with_events):
        """Test cleanup with before_month_stamp filter."""
        # Add an older event
        old_event = make_event(50, 1, "Old event", is_major=False)
        mock_world_with_events.event_manager.add_event(old_event)

        before_stamp = int(create_month_stamp(Year(99), Month.JANUARY))
        response = client_with_world.delete(
            f"/api/events/cleanup?keep_major=false&before_month_stamp={before_stamp}"
        )

        assert response.status_code == 200
        data = response.json()

        # Only the old event should be deleted
        assert data["deleted"] == 1
        assert mock_world_with_events.event_manager.count() == 5

    def test_cleanup_no_world(self):
        """Test cleanup response when no world is loaded."""
        from src.server import main

        original = main.game_instance.copy()
        main.game_instance["world"] = None

        try:
            client = TestClient(main.app)
            response = client.delete("/api/events/cleanup")

            assert response.status_code == 200
            data = response.json()

            assert data["deleted"] == 0
            assert "error" in data
        finally:
            main.game_instance.update(original)


class TestEventsPaginationIntegration:
    """Integration tests for events pagination."""

    def test_full_pagination_cycle(self, temp_db_path):
        """Test complete pagination through many events."""
        from src.server import main

        # Create world with many events
        game_map = create_test_map()
        month_stamp = create_month_stamp(Year(100), Month.JANUARY)
        world = World.create_with_db(
            map=game_map,
            month_stamp=month_stamp,
            events_db_path=temp_db_path,
        )

        # Add 50 events
        for i in range(50):
            world.event_manager.add_event(
                make_event(100 + (i // 12), (i % 12) + 1, f"Event {i}", ["a1"])
            )

        original = main.game_instance.copy()
        main.game_instance["world"] = world
        main.game_instance["sim"] = MagicMock()

        try:
            client = TestClient(main.app)

            all_event_ids = set()
            cursor = None
            page_count = 0

            while True:
                url = "/api/events?limit=15"
                if cursor:
                    url += f"&cursor={cursor}"

                response = client.get(url)
                assert response.status_code == 200
                data = response.json()

                for event in data["events"]:
                    assert event["id"] not in all_event_ids, "Duplicate event in pagination"
                    all_event_ids.add(event["id"])

                page_count += 1

                if not data["has_more"]:
                    break

                cursor = data["next_cursor"]

            # Should have gotten all 50 events
            assert len(all_event_ids) == 50
            # Should have taken 4 pages (15+15+15+5)
            assert page_count == 4

        finally:
            world.event_manager.close()
            main.game_instance.update(original)

    def test_events_order_consistency(self, temp_db_path):
        """Test that events maintain consistent ordering across pages."""
        from src.server import main

        game_map = create_test_map()
        month_stamp = create_month_stamp(Year(100), Month.JANUARY)
        world = World.create_with_db(
            map=game_map,
            month_stamp=month_stamp,
            events_db_path=temp_db_path,
        )

        # Add events with known order
        for i in range(10):
            world.event_manager.add_event(
                make_event(100, i + 1, f"Event {i}")
            )

        original = main.game_instance.copy()
        main.game_instance["world"] = world
        main.game_instance["sim"] = MagicMock()

        try:
            client = TestClient(main.app)

            # Get events in two pages
            response1 = client.get("/api/events?limit=5")
            response2 = client.get(f"/api/events?limit=5&cursor={response1.json()['next_cursor']}")

            page1 = response1.json()["events"]
            page2 = response2.json()["events"]

            # Events should be in descending order (newest first)
            all_events = page1 + page2
            month_stamps = [e["month_stamp"] for e in all_events]

            # Each month_stamp should be >= the next (descending order)
            for i in range(len(month_stamps) - 1):
                assert month_stamps[i] >= month_stamps[i + 1]

        finally:
            world.event_manager.close()
            main.game_instance.update(original)
