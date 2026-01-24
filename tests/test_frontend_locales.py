import json
import os
import pytest
import sys

# Add src to path to import WeaponType
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.classes.weapon_type import WeaponType

class TestFrontendLocales:
    def test_popup_types_coverage(self):
        """Verify that ALL WeaponType keys are mapped in frontend locales"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        zh_path = os.path.join(base_dir, "web", "src", "locales", "zh-CN.json")
        en_path = os.path.join(base_dir, "web", "src", "locales", "en-US.json")
        
        assert os.path.exists(zh_path), "zh-CN.json not found"
        assert os.path.exists(en_path), "en-US.json not found"
        
        with open(zh_path, "r", encoding="utf-8") as f:
            zh_data = json.load(f)
            
        with open(en_path, "r", encoding="utf-8") as f:
            en_data = json.load(f)
            
        # Check for 'game.info_panel.popup.types'
        zh_types = zh_data.get("game", {}).get("info_panel", {}).get("popup", {}).get("types", {})
        en_types = en_data.get("game", {}).get("info_panel", {}).get("popup", {}).get("types", {})
        
        # Verify all WeaponType enum values exist in locales
        for member in WeaponType:
            key = member.value
            assert key in zh_types, f"Key '{key}' missing in zh-CN.json types"
            assert key in en_types, f"Key '{key}' missing in en-US.json types"
            
            # Ensure no Chinese keys exist (double check)
            # The key itself should be the English enum value (e.g. "SPEAR"), not "枪"
            assert not any(char > '\u4e00' and char < '\u9fff' for char in key), \
                f"Key '{key}' contains Chinese characters, which is not allowed for localization keys."

        print("All WeaponType keys verified successfully.")
