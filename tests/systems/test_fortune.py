import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from src.systems.fortune import try_trigger_fortune, try_trigger_misfortune, FortuneKind, MisfortuneKind
from src.classes.core.avatar import Avatar
from src.systems.cultivation import Realm
from src.classes.action_runtime import ActionInstance
from src.classes.action.respire import Respire
from src.classes.goldfinger import goldfingers_by_id
from src.classes.persona import personas_by_id


def _find_goldfinger_by_key(key: str):
    for goldfinger in goldfingers_by_id.values():
        if goldfinger.key == key:
            return goldfinger
    raise AssertionError(f"Goldfinger not found: {key}")


def _find_persona_by_key(key: str):
    for persona in personas_by_id.values():
        if persona.key == key:
            return persona
    raise AssertionError(f"Persona not found: {key}")

@pytest.fixture
def mock_game_configs():
    with patch('src.utils.df.game_configs') as mock_configs:
        mock_configs.get.side_effect = lambda key, default=[]: {
            "fortune": [
                {"id": 1, "kind": "weapon", "min_realm": "QI_REFINEMENT", "max_realm": "NASCENT_SOUL", "weight": 10, "title_id": "fortune_title_weapon"},
                {"id": 5, "kind": "spirit_stone", "min_realm": "QI_REFINEMENT", "max_realm": "NASCENT_SOUL", "weight": 20, "title_id": "fortune_title_spirit_stone"},
            ],
            "misfortune": [
                {"id": 1, "kind": "loss_spirit_stone", "min_realm": "QI_REFINEMENT", "max_realm": "NASCENT_SOUL", "weight": 10, "title_id": "misfortune_title_loss_spirit_stone"},
                {"id": 2, "kind": "injury", "min_realm": "QI_REFINEMENT", "max_realm": "NASCENT_SOUL", "weight": 10, "title_id": "misfortune_title_injury"},
            ]
        }.get(key, default)
        yield mock_configs

@pytest.fixture
def mock_story_teller():
    with patch('src.classes.story_event_service.StoryTeller.tell_story', new_callable=AsyncMock) as mock_tell:
        mock_tell.return_value = "A generated story."
        yield mock_tell

@pytest.mark.asyncio
async def test_try_trigger_fortune(dummy_avatar: Avatar, mock_game_configs, mock_story_teller):
    dummy_avatar.goldfinger = _find_goldfinger_by_key("TRANSMIGRATOR")
    
    # Set current action for dynamic prompt
    action = Respire(dummy_avatar, dummy_avatar.world)
    dummy_avatar.current_action = ActionInstance(action=action, params={})
    
    # Mock random to pick spirit_stone
    with patch('random.choices') as mock_choices, patch('random.random', return_value=0.0):
        mock_choices.return_value = [{"id": 5, "kind": "spirit_stone", "min_realm": "QI_REFINEMENT", "max_realm": "NASCENT_SOUL", "weight": 20, "title_id": "fortune_title_spirit_stone"}]
        
        events = await try_trigger_fortune(dummy_avatar)
        
        assert len(events) == 2
        assert events[0].is_major is True
        assert events[1].is_story is True
        assert events[1].content == "A generated story."
        
        # Check dynamic prompt
        call_args = mock_story_teller.call_args
        assert call_args is not None
        prompt = call_args.kwargs.get("prompt")
        assert prompt is not None
        # In English/Chinese the prompt contains the action description
        # But during tests, if translations are missing, it might just be the msgid
        # So we check if it's the right msgid or contains the action
        assert "Respire" in prompt or "吐纳" in prompt or "吐納" in prompt or prompt == "fortune_dynamic_story_prompt"
        assert "穿越者" in prompt
        assert dummy_avatar.goldfinger.story_prompt in prompt

@pytest.mark.asyncio
async def test_try_trigger_misfortune(dummy_avatar: Avatar, mock_game_configs, mock_story_teller):
    dummy_avatar.personas = [_find_persona_by_key("JINX")]
    dummy_avatar.magic_stone.value = 1000
    
    # Set current action for dynamic prompt
    action = Respire(dummy_avatar, dummy_avatar.world)
    dummy_avatar.current_action = ActionInstance(action=action, params={})
    
    with patch('random.choices') as mock_choices, patch('random.random', return_value=0.0):
        mock_choices.return_value = [{"id": 1, "kind": "loss_spirit_stone", "min_realm": "QI_REFINEMENT", "max_realm": "NASCENT_SOUL", "weight": 10, "title_id": "misfortune_title_loss_spirit_stone"}]
        
        events = await try_trigger_misfortune(dummy_avatar)
        
        assert len(events) == 2
        assert events[0].is_major is True
        assert events[1].is_story is True
        assert events[1].content == "A generated story."
        
        assert dummy_avatar.magic_stone.value < 1000


@pytest.mark.asyncio
async def test_negative_misfortune_probability_is_clamped_to_zero(dummy_avatar: Avatar, mock_game_configs, mock_story_teller):
    dummy_avatar.goldfinger = _find_goldfinger_by_key("CHILD_OF_FORTUNE")
    dummy_avatar.magic_stone.value = 1000

    with patch('random.random', return_value=0.0):
        events = await try_trigger_misfortune(dummy_avatar)

    assert events == []
    assert dummy_avatar.magic_stone.value == 1000
