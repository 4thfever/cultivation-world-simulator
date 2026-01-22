import pytest
from src.classes.language import language_manager, LanguageType
from src.classes.avatar import Avatar
from src.classes.world import World
from src.utils.config import CONFIG, update_paths_for_language
from src.utils.df import reload_game_configs, game_configs
from src.classes.essence import EssenceType
import ast

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

def test_en_csv_integrity():
    """
    Verify that all English CSV config files are valid and strictly parsable.
    Specifically checks for issues like unquoted descriptions containing commas.
    """
    original_lang = language_manager.current
    try:
        # Switch to EN-US
        language_manager.set_language("en-US")
        update_paths_for_language("en-US")
        reload_game_configs()
        
        # 1. Verify Cultivate Regions (Check column alignment)
        cultivate_data = game_configs.get("cultivate_region", [])
        assert len(cultivate_data) > 0, "No cultivate_region data loaded"
        
        for row in cultivate_data:
            rid = row.get("id")
            root_type_str = row.get("root_type")
            # If CSV columns are shifted due to commas in desc, root_type will be invalid (e.g. 'cave')
            try:
                EssenceType.from_str(root_type_str)
            except ValueError as e:
                pytest.fail(f"Cultivate Region {rid}: Invalid EssenceType '{root_type_str}'. Likely CSV parsing error due to unquoted commas in description.")

        # 2. Verify City Regions (Check sell_item_ids format)
        city_data = game_configs.get("city_region", [])
        assert len(city_data) > 0, "No city_region data loaded"
        
        for row in city_data:
            rid = row.get("id")
            sell_ids_str = row.get("sell_item_ids")
            
            # If shifted, this might be something else
            assert sell_ids_str is not None, f"City Region {rid}: sell_item_ids is None"
            assert isinstance(sell_ids_str, str), f"City Region {rid}: sell_item_ids should be str"
            
            try:
                parsed = ast.literal_eval(sell_ids_str)
                assert isinstance(parsed, list), f"City Region {rid}: sell_item_ids should parse to list"
            except (ValueError, SyntaxError):
                pytest.fail(f"City Region {rid}: Failed to parse sell_item_ids '{sell_ids_str}'. Likely CSV parsing error.")

        # 3. Verify Normal Regions (Check desc)
        normal_data = game_configs.get("normal_region", [])
        assert len(normal_data) > 0, "No normal_region data loaded"
        
        for row in normal_data:
            rid = row.get("id")
            
            # A better check is that animal_ids/plant_ids are not long text descriptions.
            animal_ids = row.get("animal_ids")
            if animal_ids and len(str(animal_ids)) > 50:
                 pytest.fail(f"Normal Region {rid}: animal_ids seems too long ('{animal_ids}'). Likely CSV parsing error shifted description into this column.")

    finally:
        # Restore language
        language_manager.set_language(original_lang.value)
        update_paths_for_language(original_lang.value)
        reload_game_configs()
