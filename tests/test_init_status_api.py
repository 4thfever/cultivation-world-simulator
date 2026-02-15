"""
Tests for the initialization status API endpoints.

These tests verify the loading screen backend functionality:
- /api/init-status endpoint
- /api/game/new endpoint
- /api/control/reinit endpoint
- Initialization phases and progress tracking
"""

import pytest
import asyncio
import time
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from src.server import main
from src.server.main import app, game_instance, update_init_progress, INIT_PHASE_NAMES


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


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
    })
    yield
    game_instance.clear()
    game_instance.update(original_state)


class TestInitStatusEndpoint:
    """Tests for /api/init-status endpoint."""

    def test_init_status_idle(self, client, reset_game_instance):
        """Test init-status returns idle state correctly."""
        response = client.get("/api/init-status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "idle"
        assert data["phase"] == 0
        assert data["phase_name"] == ""
        assert data["progress"] == 0
        assert data["error"] is None
        assert data["llm_check_failed"] is False
        assert data["llm_error_message"] == ""

    def test_init_status_in_progress(self, client, reset_game_instance):
        """Test init-status during initialization."""
        game_instance["init_status"] = "in_progress"
        game_instance["init_phase"] = 3
        game_instance["init_phase_name"] = "initializing_sects"
        game_instance["init_progress"] = 33
        game_instance["init_start_time"] = time.time() - 5  # 5 seconds ago
        
        response = client.get("/api/init-status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "in_progress"
        assert data["phase"] == 3
        assert data["phase_name"] == "initializing_sects"
        assert data["progress"] == 33
        assert data["elapsed_seconds"] >= 5

    def test_init_status_ready(self, client, reset_game_instance):
        """Test init-status when initialization is complete."""
        game_instance["init_status"] = "ready"
        game_instance["init_phase"] = 6
        game_instance["init_phase_name"] = "generating_initial_events"
        game_instance["init_progress"] = 100
        
        response = client.get("/api/init-status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ready"
        assert data["progress"] == 100

    def test_init_status_error(self, client, reset_game_instance):
        """Test init-status when initialization failed."""
        game_instance["init_status"] = "error"
        game_instance["init_error"] = "LLM connection failed"
        
        response = client.get("/api/init-status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "error"
        assert data["error"] == "LLM connection failed"

    def test_init_status_llm_check_failed(self, client, reset_game_instance):
        """Test init-status includes LLM check status."""
        game_instance["init_status"] = "ready"
        game_instance["llm_check_failed"] = True
        game_instance["llm_error_message"] = "API key invalid"
        
        response = client.get("/api/init-status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["llm_check_failed"] is True
        assert data["llm_error_message"] == "API key invalid"


class TestUpdateInitProgress:
    """Tests for update_init_progress function."""

    def test_update_progress_with_phase_name(self, reset_game_instance):
        """Test updating progress with explicit phase name."""
        update_init_progress(3, "initializing_sects")
        
        assert game_instance["init_phase"] == 3
        assert game_instance["init_phase_name"] == "initializing_sects"
        assert game_instance["init_progress"] == 40

    def test_update_progress_without_phase_name(self, reset_game_instance):
        """Test updating progress uses default phase name from mapping."""
        update_init_progress(4)
        
        assert game_instance["init_phase"] == 4
        assert game_instance["init_phase_name"] == "generating_avatars"
        assert game_instance["init_progress"] == 55

    def test_all_phase_names_mapped(self):
        """Test all phases have corresponding names."""
        expected_phases = {
            0: "scanning_assets",
            1: "loading_map",
            2: "processing_history",
            3: "initializing_sects",
            4: "generating_avatars",
            5: "checking_llm",
            6: "generating_initial_events",
        }
        assert INIT_PHASE_NAMES == expected_phases


class TestNewGameEndpoint:
    """Tests for /api/game/start endpoint."""

    def test_new_game_starts_initialization(self, client, reset_game_instance):
        """Test /api/game/start starts initialization process."""
        with patch.object(main, 'init_game_async', new_callable=AsyncMock) as mock_init:
            # Prepare minimal valid request data
            payload = {
                "init_npc_num": 10,
                "sect_num": 2,
                "npc_awakening_rate_per_month": 0.01,
                "world_history": "Some history"
            }
            response = client.post("/api/game/start", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert "started" in data["message"].lower()
            assert game_instance["init_status"] == "pending"

    def test_new_game_rejects_when_in_progress(self, client, reset_game_instance):
        """Test /api/game/start rejects request when already initializing."""
        game_instance["init_status"] = "in_progress"
        
        payload = {
            "init_npc_num": 10,
            "sect_num": 2,
            "npc_awakening_rate_per_month": 0.01
        }
        response = client.post("/api/game/start", json=payload)
        
        assert response.status_code == 400
        assert "already initializing" in response.json()["detail"].lower()

    def test_new_game_clears_existing_state(self, client, reset_game_instance):
        """Test /api/game/start clears existing game state when ready."""
        mock_world = MagicMock()
        mock_sim = MagicMock()
        game_instance["world"] = mock_world
        game_instance["sim"] = mock_sim
        game_instance["init_status"] = "ready"
        
        with patch.object(main, 'init_game_async', new_callable=AsyncMock):
            payload = {
                "init_npc_num": 10,
                "sect_num": 2,
                "npc_awakening_rate_per_month": 0.01
            }
            response = client.post("/api/game/start", json=payload)
            
            assert response.status_code == 200
            assert game_instance["world"] is None
            assert game_instance["sim"] is None


class TestReinitEndpoint:
    """Tests for /api/control/reinit endpoint."""

    def test_reinit_clears_state(self, client, reset_game_instance):
        """Test /api/control/reinit clears all game state."""
        game_instance["world"] = MagicMock()
        game_instance["sim"] = MagicMock()
        game_instance["init_status"] = "error"
        game_instance["init_error"] = "Some error"
        game_instance["init_phase"] = 4
        game_instance["init_progress"] = 50
        
        with patch.object(main, 'init_game_async', new_callable=AsyncMock):
            response = client.post("/api/control/reinit")
            
            assert response.status_code == 200
            assert game_instance["world"] is None
            assert game_instance["sim"] is None
            assert game_instance["init_status"] == "pending"
            assert game_instance["init_phase"] == 0
            assert game_instance["init_progress"] == 0
            assert game_instance["init_error"] is None

    def test_reinit_starts_new_initialization(self, client, reset_game_instance):
        """Test /api/control/reinit starts new initialization task."""
        with patch.object(main, 'init_game_async', new_callable=AsyncMock) as mock_init:
            response = client.post("/api/control/reinit")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert "reinitialization" in data["message"].lower()


class TestMapAndStateAPIDuringInit:
    """Tests to verify /api/map and /api/state availability during initialization phases."""

    def test_map_available_during_checking_llm(self, client, reset_game_instance):
        """Test /api/map is available when world exists (checking_llm phase)."""
        # Simulate world being created but LLM check in progress.
        mock_world = MagicMock()
        mock_map = MagicMock()
        mock_map.width = 100
        mock_map.height = 100
        mock_map.tiles = {}
        mock_map.regions = {}
        mock_world.map = mock_map
        
        game_instance["world"] = mock_world
        game_instance["init_status"] = "in_progress"
        game_instance["init_phase"] = 5
        game_instance["init_phase_name"] = "checking_llm"
        
        # The /api/map endpoint should work.
        response = client.get("/api/map")
        # It may return data or empty, but should not error with 503.
        assert response.status_code == 200

    def test_state_available_during_generating_events(self, client, reset_game_instance):
        """Test /api/state is available during generating_initial_events phase."""
        mock_world = MagicMock()
        mock_world.month_stamp.get_year.return_value = 100
        mock_world.month_stamp.get_month.return_value = MagicMock(value=1)
        mock_world.avatar_manager.avatars = {}
        mock_world.event_manager = None
        
        game_instance["world"] = mock_world
        game_instance["init_status"] = "in_progress"
        game_instance["init_phase"] = 6
        game_instance["init_phase_name"] = "generating_initial_events"
        
        response = client.get("/api/state")
        assert response.status_code == 200


class TestInitGameAsync:
    """Tests for the async initialization flow."""

    @pytest.mark.asyncio
    async def test_init_sets_status_to_in_progress(self, reset_game_instance, mock_llm_managers):
        """Test initialization sets status to in_progress immediately."""
        with patch.object(main, 'scan_avatar_assets'), \
             patch.object(main, 'load_cultivation_world_map') as mock_load_map, \
             patch.object(main, 'check_llm_connectivity', return_value=(True, "")), \
             patch('src.server.main.World') as mock_world_class, \
             patch('src.server.main.Simulator') as mock_sim_class:
            
            mock_map = MagicMock()
            mock_load_map.return_value = mock_map
            mock_world = MagicMock()
            mock_world.avatar_manager.avatars = {}
            mock_world_class.return_value = mock_world
            mock_sim = MagicMock()
            mock_sim.step = AsyncMock()
            mock_sim_class.return_value = mock_sim
            
            # Start init but check status immediately.
            task = asyncio.create_task(main.init_game_async())
            await asyncio.sleep(0.01)  # Let it start.
            
            assert game_instance["init_status"] in ["in_progress", "ready"]
            
            await task  # Let it complete.

    @pytest.mark.asyncio
    async def test_init_error_sets_error_status(self, reset_game_instance, mock_llm_managers):
        """Test initialization error sets status to error."""
        with patch.object(main, 'scan_avatar_assets', side_effect=Exception("Test error")):
            await main.init_game_async()
            
            assert game_instance["init_status"] == "error"
            assert "Test error" in game_instance["init_error"]

    @pytest.mark.asyncio
    async def test_init_completes_with_ready_status(self, reset_game_instance, mock_llm_managers):
        """Test successful initialization sets status to ready."""
        with patch.object(main, 'scan_avatar_assets'), \
             patch.object(main, 'load_cultivation_world_map') as mock_load_map, \
             patch.object(main, 'check_llm_connectivity', return_value=(True, "")), \
             patch('src.server.main.World') as mock_world_class, \
             patch('src.server.main.Simulator') as mock_sim_class, \
             patch('src.server.main.sects_by_id', {}), \
             patch('src.server.main.CONFIG') as mock_config:
            
            mock_config.game.sect_num = 0
            mock_config.game.init_npc_num = 0
            
            mock_map = MagicMock()
            mock_load_map.return_value = mock_map
            mock_world = MagicMock()
            mock_world.avatar_manager.avatars = {}
            mock_world_class.return_value = mock_world
            mock_sim = MagicMock()
            mock_sim.step = AsyncMock()
            mock_sim_class.return_value = mock_sim
            
            await main.init_game_async()
            
            assert game_instance["init_status"] == "ready"
            assert game_instance["init_progress"] == 100

    @pytest.mark.asyncio
    async def test_init_records_llm_failure(self, reset_game_instance, mock_llm_managers):
        """Test LLM check failure is recorded but doesn't stop initialization."""
        with patch.object(main, 'scan_avatar_assets'), \
             patch.object(main, 'load_cultivation_world_map') as mock_load_map, \
             patch.object(main, 'check_llm_connectivity', return_value=(False, "API key invalid")), \
             patch('src.server.main.World') as mock_world_class, \
             patch('src.server.main.Simulator') as mock_sim_class, \
             patch('src.server.main.sects_by_id', {}), \
             patch('src.server.main.CONFIG') as mock_config:
            
            mock_config.game.sect_num = 0
            mock_config.game.init_npc_num = 0
            
            mock_map = MagicMock()
            mock_load_map.return_value = mock_map
            mock_world = MagicMock()
            mock_world.avatar_manager.avatars = {}
            mock_world_class.return_value = mock_world
            mock_sim = MagicMock()
            mock_sim.step = AsyncMock()
            mock_sim_class.return_value = mock_sim
            
            await main.init_game_async()
            
            # Should still complete successfully.
            assert game_instance["init_status"] == "ready"
            # But LLM failure should be recorded.
            assert game_instance["llm_check_failed"] is True
            assert game_instance["llm_error_message"] == "API key invalid"

    @pytest.mark.asyncio
    async def test_init_calls_history_manager(self, reset_game_instance, mock_llm_managers):
        """Test initialization calls HistoryManager when history is present."""
        with patch.object(main, 'scan_avatar_assets'), \
             patch.object(main, 'load_cultivation_world_map') as mock_load_map, \
             patch.object(main, 'check_llm_connectivity', return_value=(True, "")), \
             patch('src.server.main.World') as mock_world_class, \
             patch('src.server.main.Simulator') as mock_sim_class, \
             patch('src.server.main.sects_by_id', {}), \
             patch('src.server.main.CONFIG') as mock_config, \
             patch('src.server.main.HistoryManager') as mock_history_class:
            
            mock_config.game.sect_num = 0
            mock_config.game.init_npc_num = 0
            mock_config.game.world_history = "Ancient times..."
            
            mock_map = MagicMock()
            mock_load_map.return_value = mock_map
            mock_world = MagicMock()
            mock_world.avatar_manager.avatars = {}
            mock_world_class.create_with_db.return_value = mock_world
            mock_sim = MagicMock()
            mock_sim.step = AsyncMock()
            mock_sim_class.return_value = mock_sim
            
            # Use the mock from fixture if available, but here we patch HistoryManager class specifically 
            # to verify constructor call.
            mock_history_mgr = MagicMock()
            # We want to verify that apply_history_influence is called.
            # Even if mock_llm_managers mocks the underlying method on the real class,
            # here we mock the whole class, so we get a fresh mock instance.
            mock_history_mgr.apply_history_influence = AsyncMock()
            mock_history_class.return_value = mock_history_mgr
            
            await main.init_game_async()
            
            mock_history_class.assert_called_once_with(mock_world)
            mock_history_mgr.apply_history_influence.assert_called_once_with("Ancient times...")

    @pytest.mark.asyncio
    async def test_init_pauses_after_initial_events(self, reset_game_instance, mock_llm_managers):
        """Test game is paused after generating initial events."""
        with patch.object(main, 'scan_avatar_assets'), \
             patch.object(main, 'load_cultivation_world_map') as mock_load_map, \
             patch.object(main, 'check_llm_connectivity', return_value=(True, "")), \
             patch('src.server.main.World') as mock_world_class, \
             patch('src.server.main.Simulator') as mock_sim_class, \
             patch('src.server.main.sects_by_id', {}), \
             patch('src.server.main.CONFIG') as mock_config:
            
            mock_config.game.sect_num = 0
            mock_config.game.init_npc_num = 0
            
            mock_map = MagicMock()
            mock_load_map.return_value = mock_map
            mock_world = MagicMock()
            mock_world.avatar_manager.avatars = {}
            mock_world_class.return_value = mock_world
            mock_sim = MagicMock()
            mock_sim.step = AsyncMock()
            mock_sim_class.return_value = mock_sim
            
            await main.init_game_async()
            
            # Game should be paused after initialization.
            assert game_instance["is_paused"] is True
