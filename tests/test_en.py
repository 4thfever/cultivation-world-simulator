import pytest
from src.classes.language import language_manager, LanguageType
from src.classes.avatar import Avatar
from src.classes.world import World

def test_system_runs_in_english(dummy_avatar, base_world):
    """
    Test that the system can run in English mode without crashing.
    """
    # 1. Set language to English
    original_lang = language_manager.current
    try:
        language_manager.set_language("en-US")
        assert language_manager.current == LanguageType.EN_US

        # 2. Check basic avatar properties in English context
        # Note: The dummy_avatar fixture creates an avatar. 
        # We just want to ensure that accessing properties or methods doesn't crash due to missing translations.
        
        assert isinstance(dummy_avatar, Avatar)
        assert dummy_avatar.world == base_world
        
        # Check if we can get a description or similar that might use i18n
        # (Even if it doesn't strictly use i18n for the name, running methods is a good check)
        info = dummy_avatar.get_desc(detailed=True)
        assert info is not None
        assert len(info) > 0

        # 3. Test retrieving some static data that depends on language
        # For example, checking if we can get a weapon or technique description
        # Ideally, we should check if the loaded static data is actually in English, 
        # but for a "runs without crashing" test, accessing it is enough.
        
        if dummy_avatar.weapon:
            weapon_info = dummy_avatar.weapon.get_detailed_info()
            assert weapon_info is not None

        # 4. Attempt a simple action or logic if possible (mocked)
        # Verify no exceptions are raised during standard operations
        dummy_avatar.action_points = 100
        # Just accessing properties is a good start.

    finally:
        # Restore original language to avoid affecting other tests if run in suite
        language_manager.set_language(original_lang.value)
