import pytest
import os
import json
import uuid
from unittest.mock import patch

from src.utils.config import CONFIG
from src.sim.save.save_game import save_game, list_saves
from src.sim.load.load_game import load_game
from src.server.main import trigger_auto_save
from src.sim.simulator import Simulator

@pytest.fixture
def temp_save_dir(tmp_path):
    """Create a temporary directory for saves and mock the config path."""
    d = tmp_path / "saves"
    d.mkdir(parents=True, exist_ok=True)
    with patch.object(CONFIG.paths, "saves", d):
        yield d

def test_save_load_auto_save_flag(base_world, temp_save_dir):
    """Test that playthrough_id and is_auto_save are properly saved and loaded."""
    sim = Simulator(base_world)
    test_uuid = "test-uuid-999"
    base_world.playthrough_id = test_uuid
    
    # Save as auto save
    success, filename = save_game(base_world, sim, existed_sects=[], custom_name="Auto", is_auto_save=True)
    assert success
    assert filename is not None
    
    save_path = temp_save_dir / filename
    assert save_path.exists()
    
    # Manually check JSON structure
    with open(save_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data["meta"]["playthrough_id"] == test_uuid
        assert data["meta"]["is_auto_save"] is True

    # Load game and check World instance
    loaded_world, loaded_sim, _ = load_game(save_path)
    assert getattr(loaded_world, "playthrough_id", None) == test_uuid

def test_trigger_auto_save_limit(base_world, temp_save_dir):
    """Test that trigger_auto_save keeps only the latest 5 auto saves for the same playthrough."""
    # Ensure event_manager has a DB so save_game copies it
    from src.sim.managers.event_manager import EventManager
    db_path = temp_save_dir / "base_events.db"
    # Touch the db file to make sure it exists
    with open(db_path, "w") as f:
        f.write("")
    base_world.event_manager = EventManager.create_with_db(db_path)
    
    sim = Simulator(base_world)
    test_uuid = "test-uuid-limits"
    base_world.playthrough_id = test_uuid
    
    def mock_now():
        from datetime import datetime, timedelta
        mock_now.current += timedelta(seconds=1)
        return mock_now.current
    from datetime import datetime
    mock_now.current = datetime.now()

    with patch("src.sim.save.save_game.datetime") as mock_datetime:
        mock_datetime.now.side_effect = mock_now
        
        # Trigger 6 times
        for i in range(6):
            trigger_auto_save(base_world, sim)
        
    # Check total saves
    saves = list_saves()
    # It should be exactly 5 saves
    assert len(saves) == 5
    for path, meta in saves:
        assert meta["is_auto_save"] is True
        assert meta["playthrough_id"] == test_uuid
        # sqlite db must exist
        from src.sim.load.load_game import get_events_db_path
        assert get_events_db_path(path).exists()

def test_trigger_auto_save_does_not_delete_manual_saves_or_other_playthroughs(base_world, temp_save_dir):
    """Test that manual saves or saves from other playthroughs are not deleted."""
    # Ensure event_manager has a DB
    from src.sim.managers.event_manager import EventManager
    db_path = temp_save_dir / "base_events2.db"
    with open(db_path, "w") as f:
        f.write("")
    base_world.event_manager = EventManager.create_with_db(db_path)
    
    sim = Simulator(base_world)
    main_uuid = "main-uuid"
    other_uuid = "other-uuid"
    
    def mock_now():
        from datetime import datetime, timedelta
        mock_now.current += timedelta(seconds=1)
        return mock_now.current
    from datetime import datetime
    mock_now.current = datetime.now()
    
    with patch("src.sim.save.save_game.datetime") as mock_datetime:
        mock_datetime.now.side_effect = mock_now
        
        # Create manual save
        base_world.playthrough_id = main_uuid
        save_game(base_world, sim, existed_sects=[], custom_name="Manual", is_auto_save=False)
        
        # Create auto save for other playthrough
        base_world.playthrough_id = other_uuid
        trigger_auto_save(base_world, sim)
        
        # Now create 5 auto saves for main_uuid
        base_world.playthrough_id = main_uuid
        for i in range(5):
            trigger_auto_save(base_world, sim)
        
    saves = list_saves()
    
    # Total saves should be: 1 manual + 1 other auto + 5 main auto = 7
    assert len(saves) == 7
    
    # Verify manual save still exists
    manual_saves = [s for s in saves if s[1].get("is_auto_save", False) is False]
    assert len(manual_saves) == 1
    
    # Verify other auto save still exists
    other_auto_saves = [s for s in saves if s[1].get("playthrough_id") == other_uuid]
    assert len(other_auto_saves) == 1
    
    # Verify main auto saves are exactly 5
    main_auto_saves = [s for s in saves if s[1].get("playthrough_id") == main_uuid and s[1].get("is_auto_save") is True]
    assert len(main_auto_saves) == 5