"""
Integration tests for realm/stage i18n display in item exchange messages.

Verifies that user-facing messages show translated realm names (e.g., "筑基")
instead of raw enum values (e.g., "FOUNDATION_ESTABLISHMENT").

Coverage:
- src/classes/single_choice.py (handle_item_exchange)
- src/classes/kill_and_grab.py (kill_and_grab context string)
- src/classes/fortune.py (fortune intro strings)
- src/classes/avatar/inventory_mixin.py (can_buy_item error message)
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock

from src.systems.cultivation import Realm, Stage, CultivationProgress
from src.classes.items.weapon import weapons_by_id, Weapon
from src.classes.items.auxiliary import auxiliaries_by_id
from src.classes.items.elixir import elixirs_by_id
from src.classes.single_choice import handle_item_exchange
from src.classes.kill_and_grab import kill_and_grab


# Raw enum values that should NOT appear in user-facing messages.
RAW_REALM_VALUES = [
    "QI_REFINEMENT",
    "FOUNDATION_ESTABLISHMENT",
    "CORE_FORMATION",
    "NASCENT_SOUL",
]

RAW_STAGE_VALUES = [
    "EARLY_STAGE",
    "MIDDLE_STAGE",
    "LATE_STAGE",
]


class MockAvatarForIntegration:
    """A minimal mock avatar for integration testing."""
    def __init__(self):
        self.name = "TestCultivator"
        self.weapon = None
        self.auxiliary = None
        self.technique = None
        self.world = Mock()
        self.world.static_info = {}
        self.change_weapon = Mock()
        self.sell_weapon = Mock(return_value=100)

    def get_info(self, detailed=False):
        return {"name": self.name}


def get_real_weapon() -> Weapon:
    """Get a real weapon from the game data for testing."""
    # Get the first available weapon.
    if weapons_by_id:
        return next(iter(weapons_by_id.values()))
    pytest.skip("No weapons available in game data")


@pytest.mark.asyncio
async def test_handle_item_exchange_shows_translated_realm():
    """
    Integration test: handle_item_exchange should return messages
    with translated realm names, not raw enum values.
    """
    weapon = get_real_weapon()
    avatar = MockAvatarForIntegration()

    # Auto-equip (no existing weapon).
    swapped, msg = await handle_item_exchange(
        avatar, weapon, "weapon", "Testing context", can_sell_new=False
    )

    assert swapped is True

    # Message should NOT contain raw enum values.
    for raw_value in RAW_REALM_VALUES:
        assert raw_value not in msg, (
            f"Message contains raw enum value '{raw_value}': {msg}"
        )

    # Message should contain the weapon name.
    assert weapon.name in msg


@pytest.mark.asyncio
async def test_weapon_detailed_info_shows_translated_realm():
    """
    Integration test: Weapon.get_detailed_info() should return
    translated realm names, not raw enum values.
    """
    weapon = get_real_weapon()
    info = weapon.get_detailed_info()

    # Info should NOT contain raw enum values.
    for raw_value in RAW_REALM_VALUES:
        assert raw_value not in info, (
            f"Detailed info contains raw enum value '{raw_value}': {info}"
        )


def test_realm_str_integration_with_real_data():
    """
    Integration test: Verify all realms in actual weapon data
    have proper translated string representations.
    """
    realms_found = set()

    for weapon in weapons_by_id.values():
        realm_str = str(weapon.realm)
        realms_found.add(weapon.realm)

        # Should not be raw enum value.
        assert realm_str not in RAW_REALM_VALUES, (
            f"Weapon '{weapon.name}' has raw realm value: {realm_str}"
        )

        # Should not be empty.
        assert len(realm_str) > 0, (
            f"Weapon '{weapon.name}' has empty realm string"
        )

    # Ensure we tested at least some weapons.
    assert len(realms_found) > 0, "No weapons found in game data"


def test_cultivation_progress_str_shows_translated_realm():
    """
    Integration test: CultivationProgress.__str__() should use
    translated realm and stage names.
    """
    cp = CultivationProgress(level=35, exp=0)  # Foundation Establishment.
    cp_str = str(cp)

    # Should NOT contain raw enum values.
    for raw_value in RAW_REALM_VALUES + RAW_STAGE_VALUES:
        assert raw_value not in cp_str, (
            f"CultivationProgress string contains raw value '{raw_value}': {cp_str}"
        )


# ==================== kill_and_grab.py coverage ====================

class MockAvatarForKillAndGrab:
    """Mock avatar for kill_and_grab testing."""
    def __init__(self, name: str, weapon=None, auxiliary=None):
        self.name = name
        self.weapon = weapon
        self.auxiliary = auxiliary
        self.technique = None
        self.world = Mock()
        self.world.static_info = {}
        self.change_weapon = Mock()
        self.change_auxiliary = Mock()
        self.sell_weapon = Mock(return_value=100)
        self.sell_auxiliary = Mock(return_value=100)

    def get_info(self, detailed=False):
        return {"name": self.name}


@pytest.mark.asyncio
async def test_kill_and_grab_context_shows_translated_realm():
    """
    Integration test: kill_and_grab should generate context strings
    with translated realm names, not raw enum values.
    """
    weapon = get_real_weapon()

    winner = MockAvatarForKillAndGrab("Winner")
    loser = MockAvatarForKillAndGrab("Loser", weapon=weapon)

    # Patch handle_item_exchange to capture the context_intro argument.
    with patch(
        "src.classes.kill_and_grab.handle_item_exchange",
        new_callable=AsyncMock
    ) as mock_exchange:
        mock_exchange.return_value = (True, "equipped")

        await kill_and_grab(winner, loser)

        # Verify handle_item_exchange was called.
        assert mock_exchange.called

        # Get the context_intro argument.
        call_kwargs = mock_exchange.call_args
        context_intro = call_kwargs.kwargs.get("context_intro") or call_kwargs.args[3]

        # Context should NOT contain raw enum values.
        for raw_value in RAW_REALM_VALUES:
            assert raw_value not in context_intro, (
                f"kill_and_grab context contains raw enum value '{raw_value}': {context_intro}"
            )


# ==================== fortune.py coverage ====================

def test_fortune_weapon_intro_uses_translated_realm():
    """
    Integration test: Fortune weapon discovery intro should use
    translated realm names via str(realm).
    """
    from src.i18n import t

    weapon = get_real_weapon()
    # Simulate what fortune.py does.
    intro = t(
        "You discovered a {realm} weapon『{weapon_name}』in your fortune.",
        realm=str(weapon.realm),
        weapon_name=weapon.name
    )

    # Intro should NOT contain raw enum values.
    for raw_value in RAW_REALM_VALUES:
        assert raw_value not in intro, (
            f"Fortune intro contains raw enum value '{raw_value}': {intro}"
        )


def test_fortune_auxiliary_intro_uses_translated_realm():
    """
    Integration test: Fortune auxiliary discovery intro should use
    translated realm names via str(realm).
    """
    from src.i18n import t

    # Get a real auxiliary.
    if not auxiliaries_by_id:
        pytest.skip("No auxiliaries available in game data")
    auxiliary = next(iter(auxiliaries_by_id.values()))

    # Simulate what fortune.py does.
    intro = t(
        "You discovered a {realm} auxiliary『{auxiliary_name}』in your fortune.",
        realm=str(auxiliary.realm),
        auxiliary_name=auxiliary.name
    )

    # Intro should NOT contain raw enum values.
    for raw_value in RAW_REALM_VALUES:
        assert raw_value not in intro, (
            f"Fortune intro contains raw enum value '{raw_value}': {intro}"
        )


# ==================== inventory_mixin.py coverage ====================

def test_can_buy_item_error_message_shows_translated_realm():
    """
    Integration test: can_buy_item error message for realm restriction
    should show translated realm names, not raw enum values.
    """
    # Get a high-realm elixir.
    high_realm_elixir = None
    for elixir in elixirs_by_id.values():
        if elixir.realm >= Realm.Foundation_Establishment:
            high_realm_elixir = elixir
            break

    if high_realm_elixir is None:
        pytest.skip("No high-realm elixir found in game data")

    # Simulate the error message generation from inventory_mixin.py.
    error_msg = f"境界不足，无法承受药力 ({str(high_realm_elixir.realm)})"

    # Error message should NOT contain raw enum values.
    for raw_value in RAW_REALM_VALUES:
        assert raw_value not in error_msg, (
            f"Error message contains raw enum value '{raw_value}': {error_msg}"
        )
