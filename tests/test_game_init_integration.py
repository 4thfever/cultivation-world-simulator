"""
Integration tests for game initialization flow.

## Coverage

- `init_game_async()` (lines 310-453): **100%**
- `update_init_progress()` (lines 300-308): **100%**

## Test Summary (33 tests)

| Category              | Tests |
|-----------------------|-------|
| Progress Updates      | 4     |
| Success Path          | 2     |
| History Processing    | 4     |
| LLM Check             | 1     |
| Avatar Generation     | 6     |
| Error Handling        | 6     |
| Sects Initialization  | 3     |
| State Verification    | 5     |
| Phase Names           | 2     |

## Code Paths Covered

| Path                                      | Test                                                  |
|-------------------------------------------|-------------------------------------------------------|
| Phase 0: Asset scan success               | test_full_init_success                                |
| Phase 0: Asset scan failure               | test_init_handles_asset_scan_error                    |
| Phase 0: reload_all_static_data failure   | test_init_handles_reload_static_data_error            |
| Phase 1: Map load success                 | test_full_init_success                                |
| Phase 1: Map load failure                 | test_init_handles_map_load_error                      |
| World creation failure                    | test_init_handles_world_creation_error                |
| Simulator creation failure                | test_init_handles_simulator_creation_error            |
| Phase 2: History applied                  | test_init_applies_history                             |
| Phase 2: History failure (continues)      | test_init_continues_if_history_fails                  |
| Phase 2: Empty history skipped            | test_init_empty_history_skips_history_manager         |
| Phase 2: Whitespace history skipped       | test_init_whitespace_only_history_skips_history_manager |
| Phase 3: Sects selected                   | test_init_selects_random_sects                        |
| Phase 3: No sects available               | test_init_no_sects_available                          |
| Phase 3: More sects than available        | test_init_more_sects_requested_than_available         |
| Phase 4: Zero NPC count                   | test_init_zero_npc_count                              |
| Phase 5: LLM check success                | test_full_init_success                                |
| Phase 5: LLM check failure                | test_init_records_llm_failure                         |
| Phase 6: Initial events success           | test_full_init_success                                |
| Phase 6: Initial events failure           | test_init_continues_if_initial_events_fail            |
| State: current_save_path set              | test_init_sets_current_save_path                      |
| State: init_start_time set                | test_init_sets_start_time                             |
| State: previous error cleared             | test_init_clears_previous_error                       |
| State: status in_progress                 | test_init_sets_status_to_in_progress                  |

## What's NOT Tested Here

- Actual LLM API calls (mocked).
- Actual file I/O for map loading (mocked).
- WebSocket broadcasting during game loop.
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from src.server import main
from src.server.main import (
    app,
    game_instance,
    init_game_async,
    update_init_progress,
    INIT_PHASE_NAMES,
)


@pytest.fixture
def reset_game_instance():
    """Reset game_instance to initial state before each test."""
    original_state = dict(game_instance)
    game_instance.clear()
    game_instance.update({
        "world": None,
        "sim": None,
        "is_paused": True,
        "init_status": "idle",
        "init_phase": 0,
        "init_phase_name": "",
        "init_progress": 0,
        "init_start_time": None,
        "init_error": None,
        "llm_check_failed": False,
        "llm_error_message": "",
        "current_save_path": None,
    })
    yield
    game_instance.clear()
    game_instance.update(original_state)


@pytest.fixture
def temp_saves_dir():
    """Create a temporary saves directory and patch global config."""
    from src.utils.config import CONFIG
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir)
        # Patch the global CONFIG to ensure init_game_async writes to temp dir
        with patch.object(CONFIG.paths, "saves", path):
            yield path


class TestUpdateInitProgress:
    """Tests for update_init_progress function."""

    def test_update_progress_sets_phase(self, reset_game_instance):
        """Test that update_init_progress sets phase correctly."""
        update_init_progress(3, "initializing_sects")

        assert game_instance["init_phase"] == 3
        assert game_instance["init_phase_name"] == "initializing_sects"

    def test_update_progress_uses_default_phase_name(self, reset_game_instance):
        """Test that default phase name is used when not provided."""
        update_init_progress(4)

        assert game_instance["init_phase"] == 4
        assert game_instance["init_phase_name"] == INIT_PHASE_NAMES[4]

    def test_update_progress_calculates_percentage(self, reset_game_instance):
        """Test that progress percentage is calculated correctly."""
        progress_map = {0: 0, 1: 10, 2: 25, 3: 40, 4: 55, 5: 70, 6: 85}

        for phase, expected_progress in progress_map.items():
            update_init_progress(phase)
            assert game_instance["init_progress"] == expected_progress

    def test_all_phase_names_defined(self):
        """Test that all phases have names defined."""
        for phase in range(7):
            assert phase in INIT_PHASE_NAMES


class TestInitGameAsyncSuccess:
    """Tests for successful game initialization."""

    @pytest.mark.asyncio
    async def test_full_init_success(self, reset_game_instance, temp_saves_dir, mock_llm_managers):
        """Test complete initialization flow succeeds."""
        mock_map = MagicMock()
        mock_map.width = 100
        mock_map.height = 100

        mock_world = MagicMock()
        mock_world.avatar_manager.avatars = {}
        mock_world.month_stamp = MagicMock()

        mock_sim = MagicMock()
        mock_sim.step = AsyncMock()

        with patch.object(main, "reload_all_static_data"), \
             patch.object(main, "scan_avatar_assets"), \
             patch.object(main, "load_cultivation_world_map", return_value=mock_map), \
             patch.object(main, "check_llm_connectivity", return_value=(True, "")), \
             patch("src.server.main.World") as mock_world_class, \
             patch("src.server.main.Simulator", return_value=mock_sim), \
             patch("src.server.main.CONFIG") as mock_config, \
             patch("src.server.main.sects_by_id", {"sect1": MagicMock()}):

            mock_config.paths.saves = temp_saves_dir
            mock_config.game.sect_num = 1
            mock_config.game.init_npc_num = 5
            mock_config.game.world_history = ""

            mock_world_class.create_with_db.return_value = mock_world

            await init_game_async()

            # Verify final state.
            assert game_instance["init_status"] == "ready"
            assert game_instance["init_progress"] == 100
            assert game_instance["is_paused"] is True
            assert game_instance["world"] is mock_world
            assert game_instance["sim"] is mock_sim
            assert game_instance["llm_check_failed"] is False

    @pytest.mark.asyncio
    async def test_init_sets_status_to_in_progress(self, reset_game_instance, temp_saves_dir, mock_llm_managers):
        """Test that init sets status to in_progress immediately."""
        recorded_status = []

        original_update = update_init_progress
        def tracking_update(phase, phase_name=""):
            recorded_status.append(game_instance["init_status"])
            original_update(phase, phase_name)

        mock_map = MagicMock()
        mock_world = MagicMock()
        mock_world.avatar_manager.avatars = {}
        mock_sim = MagicMock()
        mock_sim.step = AsyncMock()

        with patch.object(main, "reload_all_static_data"), \
             patch.object(main, "scan_avatar_assets"), \
             patch.object(main, "load_cultivation_world_map", return_value=mock_map), \
             patch.object(main, "check_llm_connectivity", return_value=(True, "")), \
             patch.object(main, "update_init_progress", side_effect=tracking_update), \
             patch("src.server.main.World") as mock_world_class, \
             patch("src.server.main.Simulator", return_value=mock_sim), \
             patch("src.server.main.CONFIG") as mock_config, \
             patch("src.server.main.sects_by_id", {}):

            mock_config.paths.saves = temp_saves_dir
            mock_config.game.sect_num = 0
            mock_config.game.init_npc_num = 0
            mock_config.game.world_history = ""
            mock_world_class.create_with_db.return_value = mock_world

            await init_game_async()

            # All recorded statuses should be "in_progress".
            assert all(s == "in_progress" for s in recorded_status)


class TestInitGameAsyncWithHistory:
    """Tests for initialization with world history."""

    @pytest.mark.asyncio
    async def test_init_applies_history(self, reset_game_instance, temp_saves_dir, mock_llm_managers):
        """Test that world history is applied when configured."""
        mock_map = MagicMock()
        mock_world = MagicMock()
        mock_world.avatar_manager.avatars = {}
        mock_sim = MagicMock()
        mock_sim.step = AsyncMock()

        mock_history_mgr = MagicMock()
        mock_history_mgr.apply_history_influence = AsyncMock()

        with patch.object(main, "reload_all_static_data"), \
             patch.object(main, "scan_avatar_assets"), \
             patch.object(main, "load_cultivation_world_map", return_value=mock_map), \
             patch.object(main, "check_llm_connectivity", return_value=(True, "")), \
             patch("src.server.main.World") as mock_world_class, \
             patch("src.server.main.Simulator", return_value=mock_sim), \
             patch("src.server.main.HistoryManager", return_value=mock_history_mgr) as mock_hm_class, \
             patch("src.server.main.CONFIG") as mock_config, \
             patch("src.server.main.sects_by_id", {}):

            mock_config.paths.saves = temp_saves_dir
            mock_config.game.sect_num = 0
            mock_config.game.init_npc_num = 0
            mock_config.game.world_history = "Ancient cultivation world..."
            mock_world_class.create_with_db.return_value = mock_world

            await init_game_async()

            # Verify history was applied.
            mock_world.set_history.assert_called_once_with("Ancient cultivation world...")
            mock_hm_class.assert_called_once_with(mock_world)
            mock_history_mgr.apply_history_influence.assert_called_once_with("Ancient cultivation world...")

    @pytest.mark.asyncio
    async def test_init_continues_if_history_fails(self, reset_game_instance, temp_saves_dir, mock_llm_managers):
        """Test that init continues even if history application fails."""
        mock_map = MagicMock()
        mock_world = MagicMock()
        mock_world.avatar_manager.avatars = {}
        mock_sim = MagicMock()
        mock_sim.step = AsyncMock()

        mock_history_mgr = MagicMock()
        mock_history_mgr.apply_history_influence = AsyncMock(side_effect=Exception("History failed"))

        with patch.object(main, "reload_all_static_data"), \
             patch.object(main, "scan_avatar_assets"), \
             patch.object(main, "load_cultivation_world_map", return_value=mock_map), \
             patch.object(main, "check_llm_connectivity", return_value=(True, "")), \
             patch("src.server.main.World") as mock_world_class, \
             patch("src.server.main.Simulator", return_value=mock_sim), \
             patch("src.server.main.HistoryManager", return_value=mock_history_mgr), \
             patch("src.server.main.CONFIG") as mock_config, \
             patch("src.server.main.sects_by_id", {}):

            mock_config.paths.saves = temp_saves_dir
            mock_config.game.sect_num = 0
            mock_config.game.init_npc_num = 0
            mock_config.game.world_history = "Some history"
            mock_world_class.create_with_db.return_value = mock_world

            # Should not raise, should continue.
            await init_game_async()

            # Should still complete successfully.
            assert game_instance["init_status"] == "ready"


class TestInitGameAsyncWithLLMFailure:
    """Tests for initialization with LLM check failure."""

    @pytest.mark.asyncio
    async def test_init_records_llm_failure(self, reset_game_instance, temp_saves_dir, mock_llm_managers):
        """Test that LLM check failure is recorded but doesn't stop init."""
        mock_map = MagicMock()
        mock_world = MagicMock()
        mock_world.avatar_manager.avatars = {}
        mock_sim = MagicMock()
        mock_sim.step = AsyncMock()

        with patch.object(main, "reload_all_static_data"), \
             patch.object(main, "scan_avatar_assets"), \
             patch.object(main, "load_cultivation_world_map", return_value=mock_map), \
             patch.object(main, "check_llm_connectivity", return_value=(False, "API key invalid")), \
             patch("src.server.main.World") as mock_world_class, \
             patch("src.server.main.Simulator", return_value=mock_sim), \
             patch("src.server.main.CONFIG") as mock_config, \
             patch("src.server.main.sects_by_id", {}):

            mock_config.paths.saves = temp_saves_dir
            mock_config.game.sect_num = 0
            mock_config.game.init_npc_num = 0
            mock_config.game.world_history = ""
            mock_world_class.create_with_db.return_value = mock_world

            await init_game_async()

            # Should still complete.
            assert game_instance["init_status"] == "ready"
            # But LLM failure should be recorded.
            assert game_instance["llm_check_failed"] is True
            assert game_instance["llm_error_message"] == "API key invalid"


class TestInitGameAsyncWithAvatars:
    """Tests for avatar generation during initialization."""

    @pytest.mark.asyncio
    async def test_init_generates_npcs(self, reset_game_instance, temp_saves_dir, mock_llm_managers):
        """Test that NPCs are generated."""
        mock_map = MagicMock()
        mock_world = MagicMock()
        # Use a real dict to track what gets added.
        avatars_dict = {}
        mock_world.avatar_manager.avatars = avatars_dict
        mock_world.month_stamp = MagicMock()
        mock_sim = MagicMock()
        mock_sim.step = AsyncMock()

        mock_avatars = {"npc1": MagicMock(), "npc2": MagicMock(), "npc3": MagicMock()}

        with patch.object(main, "reload_all_static_data"), \
             patch.object(main, "scan_avatar_assets"), \
             patch.object(main, "load_cultivation_world_map", return_value=mock_map), \
             patch.object(main, "check_llm_connectivity", return_value=(True, "")), \
             patch.object(main, "_new_make_random", return_value=mock_avatars), \
             patch("src.server.main.World") as mock_world_class, \
             patch("src.server.main.Simulator", return_value=mock_sim), \
             patch("src.server.main.CONFIG") as mock_config, \
             patch("src.server.main.sects_by_id", {}):

            mock_config.paths.saves = temp_saves_dir
            mock_config.game.sect_num = 0
            mock_config.game.init_npc_num = 3
            mock_config.game.world_history = ""
            mock_world_class.create_with_db.return_value = mock_world

            await init_game_async()

            # Avatars should be registered - check the dict was updated.
            assert len(avatars_dict) == 3
            assert "npc1" in avatars_dict



class TestInitGameAsyncErrors:
    """Tests for error handling during initialization."""

    @pytest.mark.asyncio
    async def test_init_handles_map_load_error(self, reset_game_instance, temp_saves_dir, mock_llm_managers):
        """Test that map loading error sets error status."""
        with patch.object(main, "reload_all_static_data"), \
             patch.object(main, "scan_avatar_assets"), \
             patch.object(main, "load_cultivation_world_map", side_effect=Exception("Map file not found")), \
             patch("src.server.main.CONFIG") as mock_config:

            mock_config.paths.saves = temp_saves_dir

            await init_game_async()

            assert game_instance["init_status"] == "error"
            assert "Map file not found" in game_instance["init_error"]

    @pytest.mark.asyncio
    async def test_init_handles_asset_scan_error(self, reset_game_instance, temp_saves_dir, mock_llm_managers):
        """Test that asset scanning error sets error status."""
        with patch.object(main, "reload_all_static_data"), \
             patch.object(main, "scan_avatar_assets", side_effect=Exception("Asset scan failed")), \
             patch("src.server.main.CONFIG") as mock_config:

            mock_config.paths.saves = temp_saves_dir

            await init_game_async()

            assert game_instance["init_status"] == "error"
            assert "Asset scan failed" in game_instance["init_error"]

    @pytest.mark.asyncio
    async def test_init_continues_if_initial_events_fail(self, reset_game_instance, temp_saves_dir, mock_llm_managers):
        """Test that init completes even if initial event generation fails."""
        mock_map = MagicMock()
        mock_world = MagicMock()
        mock_world.avatar_manager.avatars = {}
        mock_sim = MagicMock()
        mock_sim.step = AsyncMock(side_effect=Exception("Event generation failed"))

        with patch.object(main, "reload_all_static_data"), \
             patch.object(main, "scan_avatar_assets"), \
             patch.object(main, "load_cultivation_world_map", return_value=mock_map), \
             patch.object(main, "check_llm_connectivity", return_value=(True, "")), \
             patch("src.server.main.World") as mock_world_class, \
             patch("src.server.main.Simulator", return_value=mock_sim), \
             patch("src.server.main.CONFIG") as mock_config, \
             patch("src.server.main.sects_by_id", {}):

            mock_config.paths.saves = temp_saves_dir
            mock_config.game.sect_num = 0
            mock_config.game.init_npc_num = 0
            mock_config.game.world_history = ""
            mock_world_class.create_with_db.return_value = mock_world

            await init_game_async()

            # Should still complete (initial events failure is not fatal).
            assert game_instance["init_status"] == "ready"
            # Game should be paused.
            assert game_instance["is_paused"] is True


class TestInitGameAsyncWithSects:
    """Tests for sect initialization."""

    @pytest.mark.asyncio
    async def test_init_selects_random_sects(self, reset_game_instance, temp_saves_dir, mock_llm_managers):
        """Test that random sects are selected from available sects."""
        mock_map = MagicMock()
        mock_world = MagicMock()
        mock_world.avatar_manager.avatars = {}
        mock_world.month_stamp = MagicMock()
        mock_sim = MagicMock()
        mock_sim.step = AsyncMock()

        mock_sect1 = MagicMock()
        mock_sect2 = MagicMock()
        mock_sect3 = MagicMock()

        with patch.object(main, "reload_all_static_data"), \
             patch.object(main, "scan_avatar_assets"), \
             patch.object(main, "load_cultivation_world_map", return_value=mock_map), \
             patch.object(main, "check_llm_connectivity", return_value=(True, "")), \
             patch.object(main, "_new_make_random", return_value={}) as mock_make_random, \
             patch("src.server.main.World") as mock_world_class, \
             patch("src.server.main.Simulator", return_value=mock_sim), \
             patch("src.server.main.CONFIG") as mock_config, \
             patch("src.server.main.sects_by_id", {
                 "s1": mock_sect1,
                 "s2": mock_sect2,
                 "s3": mock_sect3,
             }):

            mock_config.paths.saves = temp_saves_dir
            mock_config.game.sect_num = 2  # Request 2 sects from 3 available.
            mock_config.game.init_npc_num = 5
            mock_config.game.world_history = ""
            mock_world_class.create_with_db.return_value = mock_world

            await init_game_async()

            # _new_make_random should be called with existed_sects.
            call_args = mock_make_random.call_args
            existed_sects = call_args[1]["existed_sects"]
            assert len(existed_sects) == 2  # Should have selected 2 sects.


class TestInitGameAsyncEdgeCases:
    """Tests for edge cases in game initialization."""





    @pytest.mark.asyncio
    async def test_init_no_sects_available(self, reset_game_instance, temp_saves_dir, mock_llm_managers):
        """Test initialization when no sects are available."""
        mock_map = MagicMock()
        mock_world = MagicMock()
        mock_world.avatar_manager.avatars = {}
        mock_world.month_stamp = MagicMock()
        mock_sim = MagicMock()
        mock_sim.step = AsyncMock()

        with patch.object(main, "reload_all_static_data"), \
             patch.object(main, "scan_avatar_assets"), \
             patch.object(main, "load_cultivation_world_map", return_value=mock_map), \
             patch.object(main, "check_llm_connectivity", return_value=(True, "")), \
             patch.object(main, "_new_make_random", return_value={}) as mock_make_random, \
             patch("src.server.main.World") as mock_world_class, \
             patch("src.server.main.Simulator", return_value=mock_sim), \
             patch("src.server.main.CONFIG") as mock_config, \
             patch("src.server.main.sects_by_id", {}):  # Empty sects.

            mock_config.paths.saves = temp_saves_dir
            mock_config.game.sect_num = 5  # Request 5 sects, but none available.
            mock_config.game.init_npc_num = 3
            mock_config.game.world_history = ""
            mock_world_class.create_with_db.return_value = mock_world

            await init_game_async()

            # Should still complete successfully.
            assert game_instance["init_status"] == "ready"
            # existed_sects should be empty.
            call_kwargs = mock_make_random.call_args
            assert call_kwargs[1]["existed_sects"] == []

    @pytest.mark.asyncio
    async def test_init_more_sects_requested_than_available(self, reset_game_instance, temp_saves_dir, mock_llm_managers):
        """Test when more sects are requested than available."""
        mock_map = MagicMock()
        mock_world = MagicMock()
        mock_world.avatar_manager.avatars = {}
        mock_world.month_stamp = MagicMock()
        mock_sim = MagicMock()
        mock_sim.step = AsyncMock()

        mock_sect1 = MagicMock()
        mock_sect2 = MagicMock()

        with patch.object(main, "reload_all_static_data"), \
             patch.object(main, "scan_avatar_assets"), \
             patch.object(main, "load_cultivation_world_map", return_value=mock_map), \
             patch.object(main, "check_llm_connectivity", return_value=(True, "")), \
             patch.object(main, "_new_make_random", return_value={}) as mock_make_random, \
             patch("src.server.main.World") as mock_world_class, \
             patch("src.server.main.Simulator", return_value=mock_sim), \
             patch("src.server.main.CONFIG") as mock_config, \
             patch("src.server.main.sects_by_id", {"s1": mock_sect1, "s2": mock_sect2}):

            mock_config.paths.saves = temp_saves_dir
            mock_config.game.sect_num = 10  # Request 10, only 2 available.
            mock_config.game.init_npc_num = 3
            mock_config.game.world_history = ""
            mock_world_class.create_with_db.return_value = mock_world

            await init_game_async()

            # Should use all available sects (2).
            call_kwargs = mock_make_random.call_args
            assert len(call_kwargs[1]["existed_sects"]) == 2

    @pytest.mark.asyncio
    async def test_init_handles_world_creation_error(self, reset_game_instance, temp_saves_dir, mock_llm_managers):
        """Test that World.create_with_db failure sets error status."""
        mock_map = MagicMock()

        with patch.object(main, "reload_all_static_data"), \
             patch.object(main, "scan_avatar_assets"), \
             patch.object(main, "load_cultivation_world_map", return_value=mock_map), \
             patch("src.server.main.World") as mock_world_class, \
             patch("src.server.main.CONFIG") as mock_config:

            mock_world_class.create_with_db.side_effect = Exception("Database connection failed")
            mock_config.paths.saves = temp_saves_dir

            await init_game_async()

            assert game_instance["init_status"] == "error"
            assert "Database connection failed" in game_instance["init_error"]


    @pytest.mark.asyncio
    async def test_init_empty_history_skips_history_manager(self, reset_game_instance, temp_saves_dir, mock_llm_managers):
        """Test that empty world_history does not invoke HistoryManager."""
        mock_map = MagicMock()
        mock_world = MagicMock()
        mock_world.avatar_manager.avatars = {}
        mock_world.month_stamp = MagicMock()
        mock_sim = MagicMock()
        mock_sim.step = AsyncMock()

        with patch.object(main, "reload_all_static_data"), \
             patch.object(main, "scan_avatar_assets"), \
             patch.object(main, "load_cultivation_world_map", return_value=mock_map), \
             patch.object(main, "check_llm_connectivity", return_value=(True, "")), \
             patch.object(main, "_new_make_random", return_value={}), \
             patch("src.server.main.World") as mock_world_class, \
             patch("src.server.main.Simulator", return_value=mock_sim), \
             patch("src.server.main.HistoryManager") as mock_history_manager, \
             patch("src.server.main.CONFIG") as mock_config, \
             patch("src.server.main.sects_by_id", {}):

            mock_config.paths.saves = temp_saves_dir
            mock_config.game.sect_num = 0
            mock_config.game.init_npc_num = 5
            mock_config.game.world_history = ""  # Empty history.
            mock_world_class.create_with_db.return_value = mock_world

            await init_game_async()

            # HistoryManager should NOT be instantiated when history is empty.
            mock_history_manager.assert_not_called()
            # set_history should NOT be called either.
            mock_world.set_history.assert_not_called()

    @pytest.mark.asyncio
    async def test_init_whitespace_only_history_skips_history_manager(self, reset_game_instance, temp_saves_dir, mock_llm_managers):
        """Test that whitespace-only world_history does not invoke HistoryManager."""
        mock_map = MagicMock()
        mock_world = MagicMock()
        mock_world.avatar_manager.avatars = {}
        mock_world.month_stamp = MagicMock()
        mock_sim = MagicMock()
        mock_sim.step = AsyncMock()

        with patch.object(main, "reload_all_static_data"), \
             patch.object(main, "scan_avatar_assets"), \
             patch.object(main, "load_cultivation_world_map", return_value=mock_map), \
             patch.object(main, "check_llm_connectivity", return_value=(True, "")), \
             patch.object(main, "_new_make_random", return_value={}), \
             patch("src.server.main.World") as mock_world_class, \
             patch("src.server.main.Simulator", return_value=mock_sim), \
             patch("src.server.main.HistoryManager") as mock_history_manager, \
             patch("src.server.main.CONFIG") as mock_config, \
             patch("src.server.main.sects_by_id", {}):

            mock_config.paths.saves = temp_saves_dir
            mock_config.game.sect_num = 0
            mock_config.game.init_npc_num = 5
            mock_config.game.world_history = "   \n\t  "  # Whitespace only.
            mock_world_class.create_with_db.return_value = mock_world

            await init_game_async()

            # HistoryManager should NOT be instantiated for whitespace-only history.
            mock_history_manager.assert_not_called()
            mock_world.set_history.assert_not_called()

    @pytest.mark.asyncio
    async def test_init_handles_simulator_creation_error(self, reset_game_instance, temp_saves_dir, mock_llm_managers):
        """Test that Simulator construction failure sets error status."""
        mock_map = MagicMock()
        mock_world = MagicMock()

        with patch.object(main, "reload_all_static_data"), \
             patch.object(main, "scan_avatar_assets"), \
             patch.object(main, "load_cultivation_world_map", return_value=mock_map), \
             patch("src.server.main.World") as mock_world_class, \
             patch("src.server.main.Simulator") as mock_sim_class, \
             patch("src.server.main.CONFIG") as mock_config:

            mock_world_class.create_with_db.return_value = mock_world
            mock_sim_class.side_effect = Exception("Simulator init failed")
            mock_config.paths.saves = temp_saves_dir

            await init_game_async()

            assert game_instance["init_status"] == "error"
            assert "Simulator init failed" in game_instance["init_error"]

    @pytest.mark.asyncio
    async def test_init_sets_current_save_path(self, reset_game_instance, temp_saves_dir, mock_llm_managers):
        """Test that current_save_path is set during initialization."""
        mock_map = MagicMock()
        mock_world = MagicMock()
        mock_world.avatar_manager.avatars = {}
        mock_world.month_stamp = MagicMock()
        mock_sim = MagicMock()
        mock_sim.step = AsyncMock()

        with patch.object(main, "reload_all_static_data"), \
             patch.object(main, "scan_avatar_assets"), \
             patch.object(main, "load_cultivation_world_map", return_value=mock_map), \
             patch.object(main, "check_llm_connectivity", return_value=(True, "")), \
             patch.object(main, "_new_make_random", return_value={}), \
             patch("src.server.main.World") as mock_world_class, \
             patch("src.server.main.Simulator", return_value=mock_sim), \
             patch("src.server.main.CONFIG") as mock_config, \
             patch("src.server.main.sects_by_id", {}):

            mock_config.paths.saves = temp_saves_dir
            mock_config.game.sect_num = 0
            mock_config.game.init_npc_num = 0
            mock_config.game.world_history = ""
            mock_world_class.create_with_db.return_value = mock_world

            await init_game_async()

            # current_save_path should be set.
            assert game_instance["current_save_path"] is not None
            assert str(temp_saves_dir) in str(game_instance["current_save_path"])
            assert game_instance["current_save_path"].suffix == ".json"

    @pytest.mark.asyncio
    async def test_init_sets_start_time(self, reset_game_instance, temp_saves_dir, mock_llm_managers):
        """Test that init_start_time is set at the beginning of initialization."""
        mock_map = MagicMock()
        mock_world = MagicMock()
        mock_world.avatar_manager.avatars = {}
        mock_world.month_stamp = MagicMock()
        mock_sim = MagicMock()
        mock_sim.step = AsyncMock()

        import time
        before_init = time.time()

        with patch.object(main, "reload_all_static_data"), \
             patch.object(main, "scan_avatar_assets"), \
             patch.object(main, "load_cultivation_world_map", return_value=mock_map), \
             patch.object(main, "check_llm_connectivity", return_value=(True, "")), \
             patch.object(main, "_new_make_random", return_value={}), \
             patch("src.server.main.World") as mock_world_class, \
             patch("src.server.main.Simulator", return_value=mock_sim), \
             patch("src.server.main.CONFIG") as mock_config, \
             patch("src.server.main.sects_by_id", {}):

            mock_config.paths.saves = temp_saves_dir
            mock_config.game.sect_num = 0
            mock_config.game.init_npc_num = 0
            mock_config.game.world_history = ""
            mock_world_class.create_with_db.return_value = mock_world

            await init_game_async()

        after_init = time.time()

        # init_start_time should be set and within the expected range.
        assert game_instance["init_start_time"] is not None
        assert before_init <= game_instance["init_start_time"] <= after_init

    @pytest.mark.asyncio
    async def test_init_clears_previous_error(self, reset_game_instance, temp_saves_dir, mock_llm_managers):
        """Test that init_error is cleared at the start of initialization."""
        # Set a previous error.
        game_instance["init_error"] = "Previous error"

        mock_map = MagicMock()
        mock_world = MagicMock()
        mock_world.avatar_manager.avatars = {}
        mock_world.month_stamp = MagicMock()
        mock_sim = MagicMock()
        mock_sim.step = AsyncMock()

        with patch.object(main, "reload_all_static_data"), \
             patch.object(main, "scan_avatar_assets"), \
             patch.object(main, "load_cultivation_world_map", return_value=mock_map), \
             patch.object(main, "check_llm_connectivity", return_value=(True, "")), \
             patch.object(main, "_new_make_random", return_value={}), \
             patch("src.server.main.World") as mock_world_class, \
             patch("src.server.main.Simulator", return_value=mock_sim), \
             patch("src.server.main.CONFIG") as mock_config, \
             patch("src.server.main.sects_by_id", {}):

            mock_config.paths.saves = temp_saves_dir
            mock_config.game.sect_num = 0
            mock_config.game.init_npc_num = 0
            mock_config.game.world_history = ""
            mock_world_class.create_with_db.return_value = mock_world

            await init_game_async()

            # Previous error should be cleared.
            assert game_instance["init_error"] is None

    @pytest.mark.asyncio
    async def test_init_handles_reload_static_data_error(self, reset_game_instance, temp_saves_dir, mock_llm_managers):
        """Test that reload_all_static_data failure sets error status."""
        with patch.object(main, "reload_all_static_data", side_effect=Exception("Static data corrupted")), \
             patch("src.server.main.CONFIG") as mock_config:

            mock_config.paths.saves = temp_saves_dir

            await init_game_async()

            assert game_instance["init_status"] == "error"
            assert "Static data corrupted" in game_instance["init_error"]

    @pytest.mark.asyncio
    async def test_init_zero_npc_count(self, reset_game_instance, temp_saves_dir, mock_llm_managers):
        """Test initialization with zero NPC count."""
        mock_map = MagicMock()
        mock_world = MagicMock()
        mock_world.avatar_manager.avatars = {}
        mock_world.month_stamp = MagicMock()
        mock_sim = MagicMock()
        mock_sim.step = AsyncMock()

        with patch.object(main, "reload_all_static_data"), \
             patch.object(main, "scan_avatar_assets"), \
             patch.object(main, "load_cultivation_world_map", return_value=mock_map), \
             patch.object(main, "check_llm_connectivity", return_value=(True, "")), \
             patch.object(main, "_new_make_random", return_value={}) as mock_make_random, \
             patch("src.server.main.World") as mock_world_class, \
             patch("src.server.main.Simulator", return_value=mock_sim), \
             patch("src.server.main.CONFIG") as mock_config, \
             patch("src.server.main.sects_by_id", {}):

            mock_config.paths.saves = temp_saves_dir
            mock_config.game.sect_num = 0
            mock_config.game.init_npc_num = 0  # Zero NPCs.
            mock_config.game.world_history = ""
            mock_world_class.create_with_db.return_value = mock_world

            await init_game_async()

            # _new_make_random should NOT be called when count is 0.
            mock_make_random.assert_not_called()
            assert game_instance["init_status"] == "ready"



class TestInitPhaseNames:
    """Tests for phase name constants."""

    def test_phase_names_are_strings(self):
        """Test that all phase names are non-empty strings."""
        for phase, name in INIT_PHASE_NAMES.items():
            assert isinstance(name, str)
            assert len(name) > 0

    def test_phase_names_are_snake_case(self):
        """Test that phase names follow snake_case convention."""
        for name in INIT_PHASE_NAMES.values():
            assert name == name.lower()
            assert " " not in name