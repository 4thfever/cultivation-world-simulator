"""
Integration tests for realm/stage i18n display in item exchange messages.

Verifies that user-facing messages show translated realm names (e.g., "筑基")
instead of raw enum values (e.g., "FOUNDATION_ESTABLISHMENT").
"""
import pytest
from unittest.mock import Mock

from src.classes.cultivation import Realm, Stage
from src.classes.weapon import weapons_by_id, Weapon
from src.classes.single_choice import handle_item_exchange


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
    from src.classes.cultivation import CultivationProgress

    cp = CultivationProgress(level=35, exp=0)  # Foundation Establishment.
    cp_str = str(cp)

    # Should NOT contain raw enum values.
    for raw_value in RAW_REALM_VALUES + RAW_STAGE_VALUES:
        assert raw_value not in cp_str, (
            f"CultivationProgress string contains raw value '{raw_value}': {cp_str}"
        )
