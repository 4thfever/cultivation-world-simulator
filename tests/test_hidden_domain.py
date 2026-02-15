import pytest
import random
from unittest.mock import MagicMock, patch, AsyncMock
from src.classes.gathering.hidden_domain import HiddenDomain
from src.systems.cultivation import Realm
from src.classes.death_reason import DeathReason, DeathType
from src.classes.items.item import Item

@pytest.fixture
def mock_domain_config():
    """Mock configuration for hidden domains."""
    return [
        {
            "id": "domain_low",
            "name": "Low Realm Domain",
            "desc": "For weaklings",
            "required_realm": "Qi Refinement",
            "danger_prob": 0.5,
            "hp_loss_percent": 0.5,
            "drop_prob": 0.5,
            "cd_years": 1,
            "open_prob": 1.0,
        },
        {
            "id": "domain_high",
            "name": "High Realm Domain",
            "desc": "For experts",
            "required_realm": "Core Formation",
            "danger_prob": 0.0, # Safe
            "hp_loss_percent": 0.0,
            "drop_prob": 0.0,
            "cd_years": 1,
            "open_prob": 0.0, # Disabled by prob
        }
    ]

@pytest.fixture
def hidden_domain(mock_domain_config):
    """Instance of HiddenDomain with mocked config."""
    # Patch game_configs dict directly
    with patch.dict("src.utils.df.game_configs", {"hidden_domain": mock_domain_config}):
        domain = HiddenDomain()
        # Clear static state
        HiddenDomain._domain_states.clear()
        yield domain
        HiddenDomain._domain_states.clear()

def test_load_configs(hidden_domain):
    """Test that configs are loaded correctly from df."""
    configs = hidden_domain._load_configs()
    assert len(configs) == 2
    
    c1 = configs[0]
    assert c1.id == "domain_low"
    assert c1.required_realm == Realm.Qi_Refinement
    assert c1.danger_prob == 0.5
    
    c2 = configs[1]
    assert c2.id == "domain_high"
    assert c2.required_realm == Realm.Core_Formation

def test_is_start_basic(hidden_domain, base_world):
    """Test start condition logic."""
    # Initial state: Year 1. CD is 1 year.
    # domain_low: open_prob 1.0
    # domain_high: open_prob 0.0
    
    # By default, last_open is -999. Year 1 - (-999) >= 1.
    
    # Mock random to ensure domain_low opens (though prob is 1.0, good to be safe)
    # and domain_high stays closed (prob 0.0)
    with patch("random.random", return_value=0.5): 
        is_started = hidden_domain.is_start(base_world)
    
    assert is_started is True
    assert len(hidden_domain._active_domains) == 1
    assert hidden_domain._active_domains[0].id == "domain_low"
    
    # Check that state was updated
    assert HiddenDomain._domain_states["domain_low"] == 1

def test_is_start_cd_check(hidden_domain, base_world):
    """Test that CD prevents opening."""
    # Mark domain_low as just opened in Year 1
    HiddenDomain._domain_states["domain_low"] = 1
    
    # Current world year is 1. Diff is 0. CD is 1. 0 < 1, so shouldn't open.
    is_started = hidden_domain.is_start(base_world)
    
    assert is_started is False
    assert len(hidden_domain._active_domains) == 0

def test_get_info_formatting(hidden_domain, base_world):
    """Test the formatted info string matches the new multi-line format."""
    # Force activate domain_low
    configs = hidden_domain._load_configs()
    hidden_domain._active_domains = [configs[0]] # Low Realm Domain
    
    info = hidden_domain.get_info(base_world)
    
    # Expected: "Hidden Domain Low Realm Domain opened! Entry restricted to Qi Refinement only."
    # Note: Using 'in' because the exact localized string might vary slightly in tests, 
    # but we look for key parts.
    assert "Low Realm Domain" in info
    assert str(Realm.Qi_Refinement) in info

@pytest.mark.asyncio
async def test_execute_entry_restriction(hidden_domain, base_world, dummy_avatar):
    """Test that only eligible avatars enter (strict realm match)."""
    # domain_low limits to Qi Refinement.
    
    # Setup domains
    configs = hidden_domain._load_configs()
    hidden_domain._active_domains = [configs[0]] # Requires Qi Refinement
    
    # Avatar 1: Qi Refinement (Eligible)
    dummy_avatar.cultivation_progress.realm = Realm.Qi_Refinement
    
    # Avatar 2: Foundation Establishment (Too high - Blocked)
    av2 = MagicMock(spec=dummy_avatar)
    av2.id = 1002
    av2.name = "StrongGuy"
    av2.cultivation_progress.realm = Realm.Foundation_Establishment
    av2.personas = []

    # Mock avatar manager
    base_world.avatar_manager.get_living_avatars = MagicMock(return_value=[dummy_avatar, av2])
    
    # Alternative: Set danger to 0, drop to 1.0. 
    # Eligible avatar gets loot => Event generated.
    # Ineligible avatar gets nothing => No event.
    configs[0].drop_prob = 1.0
    configs[0].danger_prob = 0.0
    
    # Mock _generate_loot to return a dummy item
    mock_item = MagicMock(spec=Item)
    mock_item.name = "TestTreasure"
    hidden_domain._generate_loot = MagicMock(return_value=mock_item)
    
    # Mock story generation to return nothing
    hidden_domain._generate_story = AsyncMock(return_value=None)
    
    events = await hidden_domain.execute(base_world)
    
    # Events should include:
    # 1. Opening event
    # 2. Loot event for dummy_avatar
    # 3. (No event for StrongGuy)
    
    event_texts = [e.content for e in events]
    
    # Check opening event
    assert any("Low Realm Domain" in t for t in event_texts)
    
    # Check loot event for eligible avatar
    # Since tests run in zh-CN (forced by fixture), we check for Chinese text
    # "found a treasure" -> "觅得宝物"
    assert any("觅得宝物" in t for t in event_texts)
    assert any(dummy_avatar.name in t for t in event_texts)
    
    # Check NO event for ineligible avatar
    assert not any(av2.name in t for t in event_texts if av2.name != dummy_avatar.name)

@pytest.mark.asyncio
async def test_execute_danger_death(hidden_domain, base_world, dummy_avatar):
    """Test death logic in hidden domain."""
    # Setup domain
    configs = hidden_domain._load_configs()
    domain = configs[0] # Low Realm
    domain.danger_prob = 1.0 # Certain danger
    domain.hp_loss_percent = 2.0 # Instant kill (>100% HP)
    hidden_domain._active_domains = [domain]
    
    dummy_avatar.cultivation_progress.realm = Realm.Qi_Refinement
    base_world.avatar_manager.get_living_avatars = MagicMock(return_value=[dummy_avatar])
    
    # Mock handle_death to avoid complex world logic
    with patch("src.classes.gathering.hidden_domain.handle_death") as mock_death:
        events = await hidden_domain.execute(base_world)
        
        # Verify death handler called
        mock_death.assert_called_once()
        args, _ = mock_death.call_args
        # args[0] is world, args[1] is avatar, args[2] is reason
        assert args[1] == dummy_avatar
        assert args[2].death_type == DeathType.HIDDEN_DOMAIN
        
        # Verify event log
        event_texts = [e.content for e in events]
        # "perished" -> "葬身于"
        assert any("葬身于" in t for t in event_texts)

@pytest.mark.asyncio
async def test_execute_loot_drop(hidden_domain, base_world, dummy_avatar):
    """Test loot drop logic."""
    # Setup domain
    configs = hidden_domain._load_configs()
    domain = configs[0]
    domain.danger_prob = 0.0
    domain.drop_prob = 1.0
    hidden_domain._active_domains = [domain]
    
    dummy_avatar.cultivation_progress.realm = Realm.Qi_Refinement
    base_world.avatar_manager.get_living_avatars = MagicMock(return_value=[dummy_avatar])
    
    # Mock generation to return a specific item type to trigger specific logic
    # Let's use Weapon
    from src.classes.items.weapon import Weapon
    mock_weapon = MagicMock(spec=Weapon)
    mock_weapon.name = "GodSlayer"
    
    hidden_domain._generate_loot = MagicMock(return_value=mock_weapon)
    dummy_avatar.change_weapon = MagicMock()
    
    # Execute
    events = await hidden_domain.execute(base_world)
    
    # Check loot generation called with next realm
    # Current: Qi Refinement -> Next: Foundation Establishment
    hidden_domain._generate_loot.assert_called_with(dummy_avatar, Realm.Foundation_Establishment)
    
    # Check weapon equipped
    dummy_avatar.change_weapon.assert_called_with(mock_weapon)
    
    # Check event
    event_texts = [e.content for e in events]
    assert any("GodSlayer" in t for t in event_texts)

@pytest.mark.asyncio
async def test_execute_empty_handed(hidden_domain, base_world, dummy_avatar):
    """Test that avatars getting nothing receive an 'empty-handed' event."""
    # Setup domain: Safe and stingy
    configs = hidden_domain._load_configs()
    domain = configs[0]
    domain.danger_prob = 0.0
    domain.drop_prob = 0.0
    hidden_domain._active_domains = [domain]
    
    # Setup avatar
    dummy_avatar.cultivation_progress.realm = Realm.Qi_Refinement
    base_world.avatar_manager.get_living_avatars = MagicMock(return_value=[dummy_avatar])
    
    # Mock story generation to capture inputs
    hidden_domain._generate_story = AsyncMock(return_value=None)
    
    # Execute
    events = await hidden_domain.execute(base_world)
    
    # Extract event texts
    event_texts = [e.content for e in events]
    
    # Verify "empty-handed" event exists
    # Based on zh-CN: "{names} 在秘境【{domain}】中一无所获，空手而归。"
    expected_text_part = "一无所获，空手而归"
    assert any(expected_text_part in t for t in event_texts), f"Expected '{expected_text_part}' in events: {event_texts}"
    assert any(dummy_avatar.name in t for t in event_texts)
    
    # Verify that _generate_story was called
    # This implies that even with no loot/death, the system considers it a valid story-worthy execution
    hidden_domain._generate_story.assert_called_once()
    
    # Verify the empty-handed event was passed to story generator
    call_args = hidden_domain._generate_story.call_args
    # args: (world, domain, event_texts, related_avatars)
    passed_event_texts = call_args[0][2]
    assert any(expected_text_part in t for t in passed_event_texts)
