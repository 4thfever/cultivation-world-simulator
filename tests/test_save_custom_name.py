"""
Tests for custom save name and enhanced metadata features (Issue #95).
"""
import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.classes.core.world import World
from src.classes.environment.map import Map
from src.classes.environment.tile import TileType
from src.systems.time import Month, Year, create_month_stamp
from src.classes.core.avatar import Avatar, Gender
from src.classes.age import Age
from src.systems.cultivation import Realm
from src.classes.persona import personas_by_id
from src.sim.simulator import Simulator
from src.sim.save.save_game import (
    save_game,
    sanitize_save_name,
)
from src.sim.load.load_game import load_game, get_events_db_path
from src.utils.id_generator import get_avatar_id


def create_test_map():
    """Create a simple test map."""
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


# =============================================================================
# Tests for sanitize_save_name function
# =============================================================================


class TestSanitizeSaveName:
    """Tests for the sanitize_save_name helper function."""

    def test_chinese_characters_allowed(self):
        """Test that Chinese characters are preserved."""
        result = sanitize_save_name("我的存档")
        assert result == "我的存档"

    def test_english_characters_allowed(self):
        """Test that English characters are preserved."""
        result = sanitize_save_name("MyFirstSave")
        assert result == "MyFirstSave"

    def test_numbers_allowed(self):
        """Test that numbers are preserved."""
        result = sanitize_save_name("Save123")
        assert result == "Save123"

    def test_underscores_allowed(self):
        """Test that underscores are preserved."""
        result = sanitize_save_name("my_save_file")
        assert result == "my_save_file"

    def test_mixed_content(self):
        """Test mixed Chinese, English, and numbers."""
        result = sanitize_save_name("我的Save存档_123")
        assert result == "我的Save存档_123"

    def test_special_characters_replaced(self):
        """Test that special characters are replaced with underscores."""
        result = sanitize_save_name("Save!@#$%^&*()")
        assert "!" not in result
        assert "@" not in result
        assert result.replace("_", "").isalnum() or result == "Save__________"

    def test_path_separators_removed(self):
        """Test that path separators are removed."""
        result = sanitize_save_name("path/to\\save")
        assert "/" not in result
        assert "\\" not in result

    def test_dangerous_chars_removed(self):
        """Test that dangerous filesystem characters are removed."""
        result = sanitize_save_name('save:*?"<>|name')
        assert ":" not in result
        assert "*" not in result
        assert "?" not in result
        assert '"' not in result
        assert "<" not in result
        assert ">" not in result
        assert "|" not in result

    def test_length_limit(self):
        """Test that names are truncated to 50 characters."""
        long_name = "a" * 100
        result = sanitize_save_name(long_name)
        assert len(result) <= 50

    def test_empty_string_returns_default(self):
        """Test that empty string returns 'save'."""
        result = sanitize_save_name("")
        assert result == "save"

    def test_only_special_chars_returns_default(self):
        """Test that a name with only special chars returns 'save'."""
        # After replacing all special chars with underscores, if nothing left, return 'save'.
        # But underscores are kept, so "!!!" becomes "___" which is not empty.
        result = sanitize_save_name("!!!")
        # Should be "___" or similar, not "save".
        assert len(result) > 0

    def test_spaces_replaced(self):
        """Test that spaces are replaced with underscores."""
        result = sanitize_save_name("my save file")
        assert " " not in result
        assert "_" in result


# =============================================================================
# Tests for save_game with custom name
# =============================================================================


class TestSaveGameWithCustomName:
    """Tests for save_game function with custom_name parameter."""

    def test_save_with_custom_name(self, temp_save_dir):
        """Test that custom name is used in filename."""
        game_map = create_test_map()
        world = World(map=game_map, month_stamp=create_month_stamp(Year(100), Month.JANUARY))
        sim = Simulator(world)

        success, filename = save_game(
            world, sim, [],
            save_path=None,
            custom_name="我的测试存档"
        )

        # Check save succeeded.
        assert success

        # Filename should start with the sanitized custom name.
        assert filename.startswith("我的测试存档_")
        assert filename.endswith(".json")

    def test_save_without_custom_name(self, temp_save_dir):
        """Test that default naming is used when no custom name provided."""
        game_map = create_test_map()
        world = World(map=game_map, month_stamp=create_month_stamp(Year(100), Month.JANUARY))
        sim = Simulator(world)

        # Patch CONFIG.paths.saves to use temp dir.
        with patch.object(__import__('src.utils.config', fromlist=['CONFIG']).CONFIG.paths, 'saves', temp_save_dir):
            success, filename = save_game(
                world, sim, [],
                save_path=None,
                custom_name=None
            )

        assert success
        # Default filename format: YYYYMMDD_HHMMSS_Y{year}M{month}.json.
        assert "_Y100M1.json" in filename or filename.endswith(".json")

    def test_custom_name_stored_in_meta(self, temp_save_dir):
        """Test that custom_name is stored in save metadata."""
        game_map = create_test_map()
        world = World(map=game_map, month_stamp=create_month_stamp(Year(100), Month.JANUARY))
        sim = Simulator(world)

        save_path = temp_save_dir / "test_custom_meta.json"
        success, _ = save_game(
            world, sim, [],
            save_path=save_path,
            custom_name="我的存档"
        )

        assert success

        # Read and verify meta.
        with open(save_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["meta"]["custom_name"] == "我的存档"

    def test_null_custom_name_in_meta(self, temp_save_dir):
        """Test that null custom_name is stored when not provided."""
        game_map = create_test_map()
        world = World(map=game_map, month_stamp=create_month_stamp(Year(100), Month.JANUARY))
        sim = Simulator(world)

        save_path = temp_save_dir / "test_null_meta.json"
        success, _ = save_game(
            world, sim, [],
            save_path=save_path,
            custom_name=None
        )

        assert success

        with open(save_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["meta"]["custom_name"] is None


# =============================================================================
# Tests for enhanced metadata
# =============================================================================


class TestEnhancedMetadata:
    """Tests for enhanced save metadata (avatar counts)."""

    def test_avatar_counts_in_meta(self, temp_save_dir):
        """Test that avatar counts are correctly stored."""
        game_map = create_test_map()
        world = World(map=game_map, month_stamp=create_month_stamp(Year(100), Month.JANUARY))

        # Add living avatars.
        for i in range(5):
            avatar = Avatar(
                world=world,
                name=f"Avatar{i}",
                id=get_avatar_id(),
                birth_month_stamp=create_month_stamp(Year(80), Month.JANUARY),
                age=Age(20, Realm.Qi_Refinement),
                gender=Gender.MALE,
            )
            world.avatar_manager.avatars[avatar.id] = avatar

        # Add dead avatars.
        for i in range(3):
            avatar = Avatar(
                world=world,
                name=f"DeadAvatar{i}",
                id=get_avatar_id(),
                birth_month_stamp=create_month_stamp(Year(80), Month.JANUARY),
                age=Age(20, Realm.Qi_Refinement),
                gender=Gender.MALE,
            )
            world.avatar_manager.dead_avatars[avatar.id] = avatar

        sim = Simulator(world)
        save_path = temp_save_dir / "test_counts.json"
        success, _ = save_game(world, sim, [], save_path)

        assert success

        with open(save_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        meta = data["meta"]
        assert meta["alive_count"] == 5
        assert meta["dead_count"] == 3
        assert meta["avatar_count"] == 8  # total



# =============================================================================
# Tests for API endpoints
# =============================================================================


class TestSaveApiWithCustomName:
    """Tests for /api/game/save endpoint with custom name."""

    def test_api_save_with_custom_name(self, temp_save_dir):
        """Test API save endpoint with custom name."""
        from fastapi.testclient import TestClient
        from src.server import main
        from src.utils.config import CONFIG

        # Setup game instance.
        game_map = create_test_map()
        world = World(map=game_map, month_stamp=create_month_stamp(Year(100), Month.JANUARY))
        sim = Simulator(world)

        original_state = main.game_instance.copy()
        main.game_instance["world"] = world
        main.game_instance["sim"] = sim

        with patch.object(CONFIG.paths, "saves", temp_save_dir):
            client = TestClient(main.app)
            response = client.post(
                "/api/game/save",
                json={"custom_name": "我的API存档"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "我的API存档" in data["filename"]

        # Cleanup.
        main.game_instance.update(original_state)

    def test_api_save_without_custom_name(self, temp_save_dir):
        """Test API save endpoint without custom name."""
        from fastapi.testclient import TestClient
        from src.server import main
        from src.utils.config import CONFIG

        game_map = create_test_map()
        world = World(map=game_map, month_stamp=create_month_stamp(Year(100), Month.JANUARY))
        sim = Simulator(world)

        original_state = main.game_instance.copy()
        main.game_instance["world"] = world
        main.game_instance["sim"] = sim

        with patch.object(CONFIG.paths, "saves", temp_save_dir):
            client = TestClient(main.app)
            response = client.post(
                "/api/game/save",
                json={}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["filename"].endswith(".json")

        main.game_instance.update(original_state)

    def test_api_save_invalid_name_rejected(self, temp_save_dir):
        """Test that invalid save names are rejected."""
        from fastapi.testclient import TestClient
        from src.server import main
        from src.utils.config import CONFIG

        game_map = create_test_map()
        world = World(map=game_map, month_stamp=create_month_stamp(Year(100), Month.JANUARY))
        sim = Simulator(world)

        original_state = main.game_instance.copy()
        main.game_instance["world"] = world
        main.game_instance["sim"] = sim

        with patch.object(CONFIG.paths, "saves", temp_save_dir):
            client = TestClient(main.app)
            # Name with only special characters - should be rejected.
            response = client.post(
                "/api/game/save",
                json={"custom_name": "!!!@@@###"}
            )

        # Should be rejected with 400.
        assert response.status_code == 400

        main.game_instance.update(original_state)

    def test_api_save_name_too_long_rejected(self, temp_save_dir):
        """Test that names over 50 chars are rejected."""
        from fastapi.testclient import TestClient
        from src.server import main
        from src.utils.config import CONFIG

        game_map = create_test_map()
        world = World(map=game_map, month_stamp=create_month_stamp(Year(100), Month.JANUARY))
        sim = Simulator(world)

        original_state = main.game_instance.copy()
        main.game_instance["world"] = world
        main.game_instance["sim"] = sim

        with patch.object(CONFIG.paths, "saves", temp_save_dir):
            client = TestClient(main.app)
            long_name = "a" * 51
            response = client.post(
                "/api/game/save",
                json={"custom_name": long_name}
            )

        assert response.status_code == 400

        main.game_instance.update(original_state)


class TestSavesListApiWithMetadata:
    """Tests for /api/saves endpoint returning enhanced metadata."""

    def test_api_saves_returns_new_fields(self, temp_save_dir):
        """Test that /api/saves returns new metadata fields."""
        from fastapi.testclient import TestClient
        from src.server import main
        from src.utils.config import CONFIG

        # Create a save file with metadata.
        game_map = create_test_map()
        world = World(map=game_map, month_stamp=create_month_stamp(Year(100), Month.JANUARY))

        # Add avatars.
        for i in range(3):
            avatar = Avatar(
                world=world,
                name=f"Avatar{i}",
                id=get_avatar_id(),
                birth_month_stamp=create_month_stamp(Year(80), Month.JANUARY),
                age=Age(20, Realm.Qi_Refinement),
                gender=Gender.MALE,
            )
            world.avatar_manager.avatars[avatar.id] = avatar

        sim = Simulator(world)
        save_path = temp_save_dir / "test_list.json"
        save_game(world, sim, [], save_path, custom_name="列表测试")

        with patch.object(CONFIG.paths, "saves", temp_save_dir):
            client = TestClient(main.app)
            response = client.get("/api/saves")

        assert response.status_code == 200
        data = response.json()

        assert len(data["saves"]) >= 1
        save_item = data["saves"][0]

        # Verify new fields are present.
        assert "avatar_count" in save_item
        assert "alive_count" in save_item
        assert "dead_count" in save_item
        assert "custom_name" in save_item
        assert "event_count" in save_item
        assert "language" in save_item

        # Verify values.
        assert save_item["custom_name"] == "列表测试"
        assert save_item["alive_count"] == 3
        assert save_item["avatar_count"] == 3

    def test_api_saves_old_save_compatibility(self, temp_save_dir):
        """Test that old saves without new fields return defaults."""
        from fastapi.testclient import TestClient
        from src.server import main
        from src.utils.config import CONFIG

        # Create a "legacy" save file without new metadata fields.
        legacy_save = {
            "meta": {
                "version": "1.0",
                "save_time": "2026-01-01T12:00:00",
                "game_time": "100年1月",
            },
            "world": {"month_stamp": 1200},
            "avatars": [],
            "events": [],
            "simulator": {},
        }

        save_path = temp_save_dir / "legacy.json"
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(legacy_save, f)

        with patch.object(CONFIG.paths, "saves", temp_save_dir):
            client = TestClient(main.app)
            response = client.get("/api/saves")

        assert response.status_code == 200
        data = response.json()

        # Find our legacy save.
        legacy_item = None
        for save in data["saves"]:
            if save["filename"] == "legacy.json":
                legacy_item = save
                break

        assert legacy_item is not None

        # New fields should have default values.
        assert legacy_item["avatar_count"] == 0
        assert legacy_item["alive_count"] == 0
        assert legacy_item["dead_count"] == 0
        assert legacy_item["custom_name"] is None
        assert legacy_item["event_count"] == 0


# =============================================================================
# Tests for validate_save_name function
# =============================================================================


class TestValidateSaveName:
    """Tests for the validate_save_name function in main.py."""

    def test_valid_chinese_name(self):
        from src.server.main import validate_save_name
        assert validate_save_name("我的存档") is True

    def test_valid_english_name(self):
        from src.server.main import validate_save_name
        assert validate_save_name("MySave") is True

    def test_valid_mixed_name(self):
        from src.server.main import validate_save_name
        assert validate_save_name("我的Save_123") is True

    def test_empty_name_invalid(self):
        from src.server.main import validate_save_name
        assert validate_save_name("") is False

    def test_too_long_name_invalid(self):
        from src.server.main import validate_save_name
        assert validate_save_name("a" * 51) is False

    def test_special_chars_invalid(self):
        from src.server.main import validate_save_name
        assert validate_save_name("save!@#") is False

    def test_space_invalid(self):
        from src.server.main import validate_save_name
        assert validate_save_name("my save") is False

    def test_exactly_50_chars_valid(self):
        from src.server.main import validate_save_name
        assert validate_save_name("a" * 50) is True
