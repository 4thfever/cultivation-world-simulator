import json
import os
import pytest
import sys

# Add src to path to import WeaponType
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.classes.weapon_type import WeaponType
from src.i18n.locale_registry import get_locale_codes, get_schema_locale, get_source_locale

class TestFrontendLocales:
    def test_popup_types_coverage(self):
        """Verify that ALL WeaponType keys are mapped in frontend locales"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        source_locale = get_source_locale()
        schema_locale = get_schema_locale()
        source_path = os.path.join(base_dir, "web", "src", "locales", source_locale, "game.json")
        schema_path = os.path.join(base_dir, "web", "src", "locales", schema_locale, "game.json")
        
        assert os.path.exists(source_path), f"{source_locale}/game.json not found"
        assert os.path.exists(schema_path), f"{schema_locale}/game.json not found"
        
        with open(source_path, "r", encoding="utf-8") as f:
            source_data = json.load(f)
            
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_data = json.load(f)
            
        # Check for 'info_panel.popup.types' (since it's inside game.json)
        source_types = source_data.get("info_panel", {}).get("popup", {}).get("types", {})
        schema_types = schema_data.get("info_panel", {}).get("popup", {}).get("types", {})
        
        # Verify all WeaponType enum values exist in locales
        for member in WeaponType:
            key = member.value
            assert key in source_types, f"Key '{key}' missing in {source_locale}/game.json types"
            assert key in schema_types, f"Key '{key}' missing in {schema_locale}/game.json types"
            
            # Ensure no Chinese keys exist (double check)
            # The key itself should be the English enum value (e.g. "SPEAR"), not "枪"
            assert not any(char > '\u4e00' and char < '\u9fff' for char in key), \
                f"Key '{key}' contains Chinese characters, which is not allowed for localization keys."

        print("All WeaponType keys verified successfully.")

    def get_all_keys(self, d, prefix=''):
        keys = set()
        for k, v in d.items():
            full_key = f"{prefix}.{k}" if prefix else k
            keys.add(full_key)
            if isinstance(v, dict):
                keys.update(self.get_all_keys(v, full_key))
        return keys

    def test_locale_keys_consistency(self):
        """Verify that all language directories have the same JSON files and same nested keys."""
        base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web", "src", "locales")
        locales = get_locale_codes()
        base_loc = get_source_locale()
        
        # Ensure directories exist
        for loc in locales:
            loc_dir = os.path.join(base_dir, loc)
            assert os.path.exists(loc_dir), f"Directory {loc_dir} not found!"
                
        # Collect all JSON modules
        all_modules = set()
        for loc in locales:
            loc_dir = os.path.join(base_dir, loc)
            modules = [f for f in os.listdir(loc_dir) if f.endswith('.json')]
            all_modules.update(modules)
            
        has_error = False
        error_msgs = []
        
        for module in all_modules:
            loc_keys = {}
            # 1. Try to read the module under each locale
            for loc in locales:
                target_path = os.path.join(base_dir, loc, module)
                if not os.path.exists(target_path):
                    error_msgs.append(f"Missing module file {target_path}!")
                    has_error = True
                    continue
                    
                with open(target_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                loc_keys[loc] = self.get_all_keys(data)
            
            # 2. Cross-check keys to ensure they are identical
            if base_loc in loc_keys:
                base_set = loc_keys[base_loc]
                for other_loc in locales:
                    if other_loc == base_loc or other_loc not in loc_keys:
                        continue
                    other_set = loc_keys[other_loc]
                    
                    missing_in_other = base_set - other_set
                    extra_in_other = other_set - base_set
                    
                    if missing_in_other:
                        error_msgs.append(f"{other_loc}/{module} is missing keys present in {base_loc}/{module}:\n" + "\n".join([f"  - {k}" for k in sorted(missing_in_other)]))
                        has_error = True
                    
                    if extra_in_other:
                        error_msgs.append(f"{other_loc}/{module} has extra keys not in {base_loc}/{module}:\n" + "\n".join([f"  + {k}" for k in sorted(extra_in_other)]))
                        has_error = True

        if has_error:
            pytest.fail("Frontend locale validation FAILED:\n" + "\n".join(error_msgs))
