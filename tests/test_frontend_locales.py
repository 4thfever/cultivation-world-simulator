import json
import os
import pytest

class TestFrontendLocales:
    def test_popup_types_coverage(self):
        """Verify that specific Chinese keys used by backend are mapped in frontend locales"""
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
        
        # The key causing issue was "暗器"
        required_keys = ["暗器"]
        
        for key in required_keys:
            assert key in zh_types, f"Key '{key}' missing in zh-CN.json types"
            assert key in en_types, f"Key '{key}' missing in en-US.json types"
            
            # Verify translation content
            assert zh_types[key] == "暗器"
            assert en_types[key] == "Hidden Weapon"
