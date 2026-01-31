import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.classes.language import language_manager
from src.utils.df import load_game_configs, game_configs, reload_game_configs
from src.classes.name import get_random_name, Gender

class TestCsvI18n:
    """
    Test suite for the new Single Source of Truth CSV I18n architecture.
    """

    def test_load_csv_injection(self, tmp_path):
        """
        Unit test: Verify that load_csv correctly injects translations using t().
        """
        # 1. Setup Mock CSV
        config_dir = tmp_path / "game_configs"
        config_dir.mkdir(parents=True)
        
        csv_file = config_dir / "test_item.csv"
        csv_file.write_text(
            "id,name_id,name,desc_id,desc\n"
            "名称ID,名称,描述ID,描述\n"
            "1,TEST_NAME_ID,OriginalName,TEST_DESC_ID,OriginalDesc",
            encoding="utf-8"
        )
        
        # 2. Patch CONFIG to point to temp dir
        from src.utils.config import CONFIG
        original_shared_path = CONFIG.paths.shared_game_configs
        original_localized_path = getattr(CONFIG.paths, "localized_game_configs", None)
        
        # Point shared config to our temp dir
        CONFIG.paths.shared_game_configs = config_dir
        # Disable localized config for this test to avoid interference
        CONFIG.paths.localized_game_configs = tmp_path / "non_existent"
        
        try:
            # 3. Patch t() to return mock translations
            with patch('src.utils.df.t') as mock_t:
                # Mock translation logic
                def side_effect(key, **kwargs):
                    if key == "TEST_NAME_ID": return "TranslatedName"
                    if key == "TEST_DESC_ID": return "TranslatedDesc"
                    return key
                
                mock_t.side_effect = side_effect
                
                # 4. Load
                loaded = load_game_configs()
                
                # 5. Verify
                assert "test_item" in loaded
                item = loaded["test_item"][0]
                
                # Verify translation was applied
                assert item["name"] == "TranslatedName"
                assert item["desc"] == "TranslatedDesc"
                
                # Verify t() was called with correct IDs
                mock_t.assert_any_call("TEST_NAME_ID")
                mock_t.assert_any_call("TEST_DESC_ID")
                
        finally:
            CONFIG.paths.shared_game_configs = original_shared_path
            if original_localized_path:
                CONFIG.paths.localized_game_configs = original_localized_path

    def test_load_csv_fallback(self, tmp_path):
        """
        Unit test: Verify fallback to CSV values when translation is missing.
        """
        config_dir = tmp_path / "game_configs"
        config_dir.mkdir(parents=True)
        
        # Note: load_csv skips row 2 if it exists (assuming it's a comment row)
        # So we provide: Header, Comment, Data
        csv_file = config_dir / "test_fallback.csv"
        csv_file.write_text(
            "id,name_id,name\n"
            "ID,ID_KEY,NAME_KEY\n" 
            "1,MISSING_ID,OriginalName",
            encoding="utf-8"
        )
        
        from src.utils.config import CONFIG
        original_shared_path = CONFIG.paths.shared_game_configs
        original_localized_path = getattr(CONFIG.paths, "localized_game_configs", None)
        
        CONFIG.paths.shared_game_configs = config_dir
        CONFIG.paths.localized_game_configs = tmp_path / "non_existent"
        
        try:
            with patch('src.utils.df.t') as mock_t:
                # Mock t() returning the key itself (standard gettext behavior for missing keys)
                mock_t.side_effect = lambda k, **kw: k
                
                loaded = load_game_configs()
                item = loaded["test_fallback"][0]
                
                # Should fallback to "OriginalName" because t("MISSING_ID") == "MISSING_ID"
                assert item["name"] == "OriginalName"
                
        finally:
            CONFIG.paths.shared_game_configs = original_shared_path
            if original_localized_path:
                CONFIG.paths.localized_game_configs = original_localized_path

    def test_integration_switch_language(self):
        """
        Integration test: Verify real config loading and language switching.
        Requires actual static/game_configs files and compiled .mo files.
        """
        # Ensure we are using the real paths
        # 1. Switch to zh-CN
        language_manager.set_language("zh-CN")
        # Ensure reload happens
        reload_game_configs()
        
        # Check a known item (e.g. hidden_domain)
        domains = game_configs.get("hidden_domain")
        if not domains:
            pytest.skip("hidden_domain.csv not found or empty")
            
        first_domain_zh = domains[0]
        # zh-CN name should be Chinese
        # Heuristic: Check for Chinese char range
        assert any("\u4e00" <= c <= "\u9fff" for c in first_domain_zh["name"]), f"Expected Chinese name, got {first_domain_zh['name']}"
        
        # 2. Switch to en-US
        language_manager.set_language("en-US")
        reload_game_configs()
        
        domains_en = game_configs.get("hidden_domain")
        first_domain_en = domains_en[0]
        
        # en-US name should NOT be Chinese
        assert not any("\u4e00" <= c <= "\u9fff" for c in first_domain_en["name"]), f"Expected English name, got {first_domain_en['name']}"
        assert first_domain_en["name"] != first_domain_zh["name"]

    def test_name_manager_i18n(self):
        """
        Integration test: Verify NameManager loads correct files based on language.
        """
        # 1. zh-CN
        language_manager.set_language("zh-CN")
        # NameManager auto-reloads on init, but we need to force reload since it's a singleton
        from src.classes.name import reload as reload_names, _name_manager
        reload_names()
        
        # Check internal lists
        # common_last_names should contain "李", "王" etc.
        assert len(_name_manager.common_last_names) > 0
        assert "李" in _name_manager.common_last_names or "王" in _name_manager.common_last_names
        
        # 2. en-US
        language_manager.set_language("en-US")
        reload_names()
        
        # common_last_names should contain "Li", "Wang" etc. (from last_name_en.csv)
        assert len(_name_manager.common_last_names) > 0
        # Check that it's NOT Chinese chars
        first_name = _name_manager.common_last_names[0]
        assert not any("\u4e00" <= c <= "\u9fff" for c in first_name)
