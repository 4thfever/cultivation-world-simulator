import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from src.classes.battle import handle_battle_finish
from src.classes.death_reason import DeathType

@pytest.mark.asyncio
async def test_attacker_dies_killer_is_winner():
    # Setup mocks
    world = MagicMock()
    world.month_stamp = 100

    attacker = MagicMock()
    attacker.id = "attacker"
    attacker.name = "Attacker"
    attacker.hp = -10 # Dead

    defender = MagicMock()
    defender.id = "defender"
    defender.name = "Defender"
    defender.hp = 50 # Alive

    # res: (winner, loser, loser_damage, winner_damage)
    # Defender wins, Attacker loses
    res = (defender, attacker, 110, 10)

    start_content = "Battle start"
    story_prompt = "Story prompt"

    # Patch StoryTeller and handle_death
    with patch("src.classes.story_teller.StoryTeller.tell_story", new_callable=AsyncMock) as mock_tell_story, \
         patch("src.classes.death.handle_death") as mock_handle_death:
        
        mock_tell_story.return_value = "Story content"

        await handle_battle_finish(
            world,
            attacker,
            defender,
            res,
            start_content,
            story_prompt
        )

        # Assert handle_death called
        assert mock_handle_death.called

        # Get the DeathReason object passed to handle_death
        # handle_death(world, loser, death_reason)
        call_args = mock_handle_death.call_args
        death_reason = call_args[0][2]

        assert death_reason.death_type == DeathType.BATTLE
        # This is the bug: it was attacker.name (Attacker), should be winner.name (Defender)
        assert death_reason.killer_name == defender.name
