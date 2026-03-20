import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock

from src.classes.core.world import World
from src.classes.environment.map import Map
from src.classes.environment.tile import TileType
from src.systems.time import Month, Year, create_month_stamp
from src.sim.simulator import Simulator
from src.sim.save.save_game import save_game
from src.classes.language import language_manager
from src.utils.config import CONFIG
from src.i18n.locale_registry import get_default_locale, get_fallback_locale

# Helper functions
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

class TestSaveLoadLanguage:
    
    def test_save_records_language(self, temp_save_dir):
        """Test that save_game records the current language in metadata."""
        # 1. Setup
        game_map = create_test_map()
        month_stamp = create_month_stamp(Year(100), Month.JANUARY)
        # Create dummy events db file to avoid errors
        events_db_path = temp_save_dir / "test_lang_zh_events.db"
        world = World.create_with_db(map=game_map, month_stamp=month_stamp, events_db_path=events_db_path)
        sim = Simulator(world)
        
        # 2. Set Language
        original_lang = language_manager.current
        try:
            default_locale = get_default_locale()
            fallback_locale = get_fallback_locale()
            language_manager.set_language(default_locale)
            
            # 3. Save
            save_path = temp_save_dir / "test_lang_zh.json"
            save_game(world, sim, [], save_path)
            
            # 4. Verify
            with open(save_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            assert "meta" in data
            assert "language" in data["meta"]
            assert data["meta"]["language"] == default_locale
            
            # Test English
            world.event_manager.close() # Close db before new save
            
            language_manager.set_language(fallback_locale)
            save_path_en = temp_save_dir / "test_lang_en.json"
            events_db_path_en = temp_save_dir / "test_lang_en_events.db"
            
            # Create new world for new db path or just update existing world?
            # Easiest is to create new world
            world_en = World.create_with_db(map=game_map, month_stamp=month_stamp, events_db_path=events_db_path_en)
            sim_en = Simulator(world_en)
            
            save_game(world_en, sim_en, [], save_path_en)
            world_en.event_manager.close()
            
            with open(save_path_en, "r", encoding="utf-8") as f:
                data_en = json.load(f)
            assert data_en["meta"]["language"] == fallback_locale
            
        finally:
            # Restore
            language_manager.set_language(str(original_lang))
            try:
                if world and hasattr(world, 'event_manager'):
                    world.event_manager.close()
            except:
                pass

    @pytest.mark.asyncio
    async def test_load_switches_language(self, temp_save_dir):
        """Test that loading a save with different language triggers switch."""
        
        fallback_locale = get_fallback_locale()
        default_locale = get_default_locale()

        # 1. Create a minimal save file with fallback language
        save_filename = "test_switch_lang.json"
        save_path = temp_save_dir / save_filename
        
        save_data = {
            "meta": {
                "version": "test",
                "save_time": "2026-01-01", 
                "game_time": "Y1M1",
                "language": fallback_locale,
                "events_db": "test_switch_lang_events.db",
                "event_count": 0
            },
            # Load game might access these, so provide minimal structure
            "world": {}, 
            "avatars": [],
            "events": [],
            "simulator": {}
        }
        
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(save_data, f)
            
        # 2. Mock dependencies
        # Ensure current is default locale
        language_manager._current = default_locale
        
        mock_broadcast = AsyncMock()
        
        # We patch load_game so we don't need a valid save file structure beyond meta.
        # Runtime language switching is now handled through apply_runtime_content_locale.
        with patch('src.server.main.manager.broadcast', mock_broadcast), \
             patch('src.server.main.apply_runtime_content_locale') as mock_apply_locale, \
             patch.object(CONFIG.paths, "saves", temp_save_dir), \
             patch('src.server.main.load_game', return_value=(MagicMock(), MagicMock(), [])), \
             patch('src.server.main.scan_avatar_assets'):
            
            from src.server.main import api_load_game, LoadGameRequest
            
            req = LoadGameRequest(filename=save_filename)
            await api_load_game(req)
            
            # 3. Verify
            # Verify broadcast was called with toast
            assert mock_broadcast.called
            call_args = mock_broadcast.call_args[0][0]
            assert call_args['type'] == 'toast'
            assert fallback_locale in call_args['message']
            
            # Verify runtime locale switch was requested
            mock_apply_locale.assert_called_once_with(fallback_locale)

    @pytest.mark.asyncio
    async def test_load_no_switch_same_language(self, temp_save_dir):
        """Test that loading same language save does NOT trigger switch."""
        
        default_locale = get_default_locale()

        # 1. Save with default locale
        save_filename = "test_same_lang.json"
        save_path = temp_save_dir / save_filename
        
        save_data = {
            "meta": {"language": default_locale},
        }
        
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(save_data, f)
            
        # 2. Mock
        language_manager._current = default_locale
        
        mock_broadcast = AsyncMock()
        mock_apply_locale = MagicMock()
        
        with patch('src.server.main.manager.broadcast', mock_broadcast), \
             patch('src.server.main.apply_runtime_content_locale', mock_apply_locale), \
             patch.object(CONFIG.paths, "saves", temp_save_dir), \
             patch('src.server.main.load_game', return_value=(MagicMock(), MagicMock(), [])), \
             patch('src.server.main.scan_avatar_assets'):
             
            from src.server.main import api_load_game, LoadGameRequest
            
            req = LoadGameRequest(filename=save_filename)
            await api_load_game(req)
            
            # 3. Verify
            # Broadcast IS called to enforce sync (toast), even if same language
            assert mock_broadcast.called
            
            # But actual backend switch (expensive operation) should NOT be called
            assert not mock_apply_locale.called
