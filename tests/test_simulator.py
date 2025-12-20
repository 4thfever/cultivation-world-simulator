import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from src.sim.simulator import Simulator
from src.classes.action.move_to_direction import MoveToDirection
from src.classes.tile import TileType
from src.classes.action_runtime import ActionInstance

def test_simulator_step_moves_avatar_and_sets_tile(base_world, dummy_avatar):
    # Set initial position
    dummy_avatar.pos_x = 1
    dummy_avatar.pos_y = 1
    # Ensure tile is updated to initial position (fixture puts it at 0,0)
    dummy_avatar.tile = base_world.map.get_tile(1, 1)

    sim = Simulator(base_world)
    base_world.avatar_manager.avatars[dummy_avatar.id] = dummy_avatar

    # Manually assign a MoveToDirection action to avoid relying on LLM
    action = MoveToDirection(dummy_avatar, base_world)
    # "East" means x + 1
    direction = "East"
    action.start(direction=direction) # Initialize start_monthstamp etc.
    
    # Wrap in ActionInstance
    dummy_avatar.current_action = ActionInstance(action=action, params={"direction": direction})

    # Mock LLM to avoid external calls or errors
    # We need to patch where it is imported or used. 
    # simulator.py imports process_avatar_long_term_objective, etc.
    # The easiest way is to patch call_llm globally or specifically the phases.
    with patch("src.sim.simulator.llm_ai") as mock_ai, \
         patch("src.sim.simulator.process_avatar_long_term_objective", new_callable=AsyncMock) as mock_lto, \
         patch("src.classes.nickname.process_avatar_nickname", new_callable=AsyncMock) as mock_nick, \
         patch("src.classes.relation_resolver.RelationResolver.run_batch", new_callable=AsyncMock) as mock_rr:
        
        mock_ai.decide = MagicMock(return_value={})
        # Mock async returns for gathered tasks
        mock_lto.return_value = None 
        mock_nick.return_value = None
        mock_rr.return_value = []
        
        print(f"DEBUG: Before step: pos_x={dummy_avatar.pos_x}")
        # Run step synchronously
        asyncio.run(sim.step())
        print(f"DEBUG: After step: pos_x={dummy_avatar.pos_x}")
        print(f"DEBUG: move_step_length={getattr(dummy_avatar, 'move_step_length', 'Not set')}")
        print(f"DEBUG: effects={dummy_avatar.effects}")

    # Assert moved East (x increased by move_step_length)
    # Current move step for Qi Refinement is 2
    assert dummy_avatar.pos_x == 3
    assert dummy_avatar.pos_y == 1

    # Assert tile is updated
    assert dummy_avatar.tile is not None
    assert dummy_avatar.tile.x == 3
    assert dummy_avatar.tile.y == 1
