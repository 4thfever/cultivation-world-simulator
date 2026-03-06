import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from src.systems.random_minor_event import try_trigger_random_minor_event
from src.classes.core.avatar.core import Avatar
from src.classes.core.world import World

@pytest.fixture
def mock_random_minor_event_configs():
    with patch('src.systems.random_minor_event.game_configs') as mock_configs:
        mock_configs.get.return_value = [
            {"id": 1, "participants": 1, "desc_id": "minor_event_cause_1", "desc": "心境偏移"},
            {"id": 8, "participants": 2, "desc_id": "minor_event_cause_8", "desc": "微观社交摩擦(互相打量/戒备/嘲讽)"},
        ]
        yield mock_configs

@pytest.fixture
def mock_call_llm_with_task_name():
    with patch('src.systems.random_minor_event.call_llm_with_task_name', new_callable=AsyncMock) as mock_call:
        mock_call.return_value = {"event_text": "这是一个测试生成的随机小事。"}
        yield mock_call

@pytest.mark.asyncio
async def test_try_trigger_random_minor_event_single(dummy_avatar: Avatar, mock_random_minor_event_configs, mock_call_llm_with_task_name):
    # Setup conditions
    dummy_avatar.current_action = None
    
    with patch('random.random', return_value=0.0), patch('random.choice') as mock_choice:
        # Force single participant event
        mock_choice.return_value = {"id": 1, "participants": 1, "desc_id": "minor_event_cause_1"}
        
        event = await try_trigger_random_minor_event(dummy_avatar, dummy_avatar.world)
        
        assert event is not None
        assert event.content == "这是一个测试生成的随机小事。"
        assert event.is_major is False
        assert event.is_story is False
        assert len(event.related_avatars) == 1
        assert event.related_avatars[0] == dummy_avatar.id

@pytest.mark.asyncio
async def test_try_trigger_random_minor_event_duo_with_other_avatar(dummy_avatar: Avatar, base_world: World, mock_random_minor_event_configs, mock_call_llm_with_task_name):
    # Setup conditions
    dummy_avatar.current_action = None
    
    # Create another avatar in the world
    from src.systems.time import create_month_stamp, Year, Month
    from src.classes.age import Age
    from src.systems.cultivation import Realm
    from src.classes.gender import Gender
    from src.utils.id_generator import get_avatar_id
    
    other_avatar = Avatar(
        world=base_world,
        name="Other",
        id=get_avatar_id(),
        birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
        age=Age(20, Realm.Qi_Refinement),
        gender=Gender.FEMALE,
        pos_x=dummy_avatar.pos_x,
        pos_y=dummy_avatar.pos_y
    )
    base_world.avatar_manager.register_avatar(other_avatar)
    
    with patch('random.random', return_value=0.0), patch('random.choice') as mock_choice:
        # We need mock_choice to first return the event config, and then return the other avatar
        mock_choice.side_effect = [{"id": 8, "participants": 2, "desc_id": "minor_event_cause_8"}, other_avatar]
        
        event = await try_trigger_random_minor_event(dummy_avatar, dummy_avatar.world)
        
        assert event is not None
        assert event.content == "这是一个测试生成的随机小事。"
        assert len(event.related_avatars) == 2
        assert dummy_avatar.id in event.related_avatars
        assert other_avatar.id in event.related_avatars

@pytest.mark.asyncio
async def test_try_trigger_random_minor_event_duo_fallback_to_anonymous(dummy_avatar: Avatar, mock_random_minor_event_configs, mock_call_llm_with_task_name):
    # Setup conditions
    dummy_avatar.current_action = None
    # Make sure there is no other avatar in the world (dummy_avatar is the only one)
    
    with patch('random.random', return_value=0.0), patch('random.choice') as mock_choice:
        mock_choice.return_value = {"id": 8, "participants": 2, "desc_id": "minor_event_cause_8"}
        
        event = await try_trigger_random_minor_event(dummy_avatar, dummy_avatar.world)
        
        assert event is not None
        assert event.content == "这是一个测试生成的随机小事。"
        # It fell back to anonymous extra, so only the main avatar is in related_avatars
        assert len(event.related_avatars) == 1
        assert event.related_avatars[0] == dummy_avatar.id

@pytest.mark.asyncio
async def test_try_trigger_random_minor_event_prob_not_met(dummy_avatar: Avatar, mock_random_minor_event_configs, mock_call_llm_with_task_name):
    dummy_avatar.current_action = None
    
    # Random roll is 1.0, which is >= base_prob (0.05)
    with patch('random.random', return_value=1.0):
        event = await try_trigger_random_minor_event(dummy_avatar, dummy_avatar.world)
        assert event is None

@pytest.mark.asyncio
async def test_try_trigger_random_minor_event_cannot_trigger(dummy_avatar: Avatar, mock_random_minor_event_configs, mock_call_llm_with_task_name):
    # Avatar is occupied/closed
    from src.classes.action.breakthrough import Breakthrough
    from src.classes.action_runtime import ActionInstance
    action = Breakthrough(dummy_avatar, dummy_avatar.world)
    dummy_avatar.current_action = ActionInstance(action=action, params={})
    
    with patch('random.random', return_value=0.0):
        event = await try_trigger_random_minor_event(dummy_avatar, dummy_avatar.world)
        assert event is None

@pytest.mark.asyncio
async def test_try_trigger_random_minor_event_no_configs(dummy_avatar: Avatar, mock_call_llm_with_task_name):
    # Setup conditions
    dummy_avatar.current_action = None
    
    with patch('src.systems.random_minor_event.game_configs') as mock_configs:
        mock_configs.get.return_value = [] # Empty configs
        
        with patch('random.random', return_value=0.0):
            event = await try_trigger_random_minor_event(dummy_avatar, dummy_avatar.world)
            assert event is None

@pytest.mark.asyncio
async def test_try_trigger_random_minor_event_llm_error(dummy_avatar: Avatar, mock_random_minor_event_configs):
    # Setup conditions
    dummy_avatar.current_action = None
    
    with patch('src.systems.random_minor_event.call_llm_with_task_name', new_callable=AsyncMock) as mock_call:
        mock_call.side_effect = Exception("LLM Error")
        
        with patch('random.random', return_value=0.0), patch('random.choice') as mock_choice:
            mock_choice.return_value = {"id": 1, "participants": 1, "desc_id": "minor_event_cause_1"}
            
            event = await try_trigger_random_minor_event(dummy_avatar, dummy_avatar.world)
            assert event is None

@pytest.mark.asyncio
async def test_try_trigger_random_minor_event_empty_llm_result(dummy_avatar: Avatar, mock_random_minor_event_configs):
    # Setup conditions
    dummy_avatar.current_action = None
    
    with patch('src.systems.random_minor_event.call_llm_with_task_name', new_callable=AsyncMock) as mock_call:
        mock_call.return_value = {"event_text": "   "} # Empty after strip
        
        with patch('random.random', return_value=0.0), patch('random.choice') as mock_choice:
            mock_choice.return_value = {"id": 1, "participants": 1, "desc_id": "minor_event_cause_1"}
            
            event = await try_trigger_random_minor_event(dummy_avatar, dummy_avatar.world)
            assert event is None

@pytest.mark.asyncio
async def test_try_trigger_random_minor_event_with_phenomenon(dummy_avatar: Avatar, mock_random_minor_event_configs, mock_call_llm_with_task_name):
    # Setup conditions
    dummy_avatar.current_action = None
    
    # Mock world phenomenon
    from src.classes.celestial_phenomenon import CelestialPhenomenon
    from src.classes.rarity import RARITY_CONFIGS, RarityLevel
    phenomenon = CelestialPhenomenon(
        id=1,
        name="灵气复苏",
        rarity=RARITY_CONFIGS[RarityLevel.SSR],
        effects={},
        effect_desc="None",
        desc="desc",
        duration_years=12
    )
    dummy_avatar.world.current_phenomenon = phenomenon
    
    with patch('random.random', return_value=0.0), patch('random.choice') as mock_choice:
        mock_choice.return_value = {"id": 1, "participants": 1, "desc_id": "minor_event_cause_1"}
        
        event = await try_trigger_random_minor_event(dummy_avatar, dummy_avatar.world)
        
        assert event is not None
        assert event.content == "这是一个测试生成的随机小事。"
    
    # Clean up
    dummy_avatar.world.current_phenomenon = None
