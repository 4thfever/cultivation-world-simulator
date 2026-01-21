"""
Tests for the i18n dynamic text translation module.
"""

import pytest
from src.i18n import t, reload_translations
from src.classes.language import language_manager


class TestI18nModule:
    """Tests for the i18n module."""
    
    def setup_method(self):
        """Reset translations before each test."""
        reload_translations()
        language_manager.set_language("zh-CN")
    
    def teardown_method(self):
        """Reset to default language after each test."""
        language_manager.set_language("zh-CN")
        reload_translations()
    
    def test_chinese_translation_basic(self):
        """Test basic Chinese translation."""
        language_manager.set_language("zh-CN")
        result = t("{name} lost {amount} spirit stones", name="张三", amount=100)
        assert "张三" in result
        assert "损失灵石" in result
        assert "100" in result
    
    def test_english_translation_basic(self):
        """Test basic English translation."""
        language_manager.set_language("en-US")
        result = t("{name} lost {amount} spirit stones", name="Zhang San", amount=100)
        assert "Zhang San" in result
        assert "lost" in result
        assert "spirit stones" in result
        assert "100" in result
    
    def test_battle_message_chinese(self):
        """Test battle message in Chinese."""
        language_manager.set_language("zh-CN")
        result = t(
            "{winner} defeated {loser}, dealing {damage} damage. {loser} was fatally wounded and perished.",
            winner="李明",
            loser="王五",
            damage=50
        )
        assert "李明" in result
        assert "战胜了" in result
        assert "王五" in result
        assert "50" in result
        assert "陨落" in result
    
    def test_battle_message_english(self):
        """Test battle message in English."""
        language_manager.set_language("en-US")
        result = t(
            "{winner} defeated {loser}, dealing {damage} damage. {loser} was fatally wounded and perished.",
            winner="Li Ming",
            loser="Wang Wu",
            damage=50
        )
        assert "Li Ming" in result
        assert "defeated" in result
        assert "Wang Wu" in result
        assert "50" in result
        assert "perished" in result
    
    def test_fortune_message_chinese(self):
        """Test fortune message in Chinese."""
        language_manager.set_language("zh-CN")
        result = t("Encountered fortune ({theme}), {result}", theme="误入洞府", result="获得神兵")
        assert "遭遇奇遇" in result
        assert "误入洞府" in result
        assert "获得神兵" in result
    
    def test_fortune_message_english(self):
        """Test fortune message in English."""
        language_manager.set_language("en-US")
        result = t("Encountered fortune ({theme}), {result}", theme="Cave Discovery", result="Found Treasure")
        assert "Encountered fortune" in result
        assert "Cave Discovery" in result
        assert "Found Treasure" in result
    
    def test_fallback_on_unknown_message(self):
        """Test fallback when message is not in translation file."""
        language_manager.set_language("zh-CN")
        # This message is not in the .po file.
        result = t("Unknown message: {value}", value="test")
        # Should return the original message with formatting applied.
        assert result == "Unknown message: test"
    
    def test_language_switch_reloads_translations(self):
        """Test that switching language reloads translations."""
        # Start with Chinese.
        language_manager.set_language("zh-CN")
        result_zh = t("{name} lost {amount} spirit stones", name="Test", amount=10)
        assert "损失灵石" in result_zh
        
        # Switch to English.
        language_manager.set_language("en-US")
        result_en = t("{name} lost {amount} spirit stones", name="Test", amount=10)
        assert "lost" in result_en
        assert "spirit stones" in result_en
        assert "损失灵石" not in result_en
    
    def test_reload_translations_clears_cache(self):
        """Test that reload_translations clears the cache."""
        language_manager.set_language("zh-CN")
        _ = t("{name} lost {amount} spirit stones", name="A", amount=1)
        
        # Reload should clear cache.
        reload_translations()
        
        # Should still work after reload.
        result = t("{name} lost {amount} spirit stones", name="B", amount=2)
        assert "损失灵石" in result
    
    def test_death_reason_chinese(self):
        """Test death reason translation in Chinese."""
        language_manager.set_language("zh-CN")
        
        result1 = t("Killed by {killer}", killer="敌人")
        assert "被" in result1
        assert "敌人" in result1
        assert "杀害" in result1
        
        result2 = t("Died from severe injuries")
        assert "重伤不治身亡" in result2
        
        result3 = t("Died of old age")
        assert "寿元耗尽而亡" in result3
    
    def test_death_reason_english(self):
        """Test death reason translation in English."""
        language_manager.set_language("en-US")
        
        result1 = t("Killed by {killer}", killer="Enemy")
        assert "Killed by" in result1
        assert "Enemy" in result1
        
        result2 = t("Died from severe injuries")
        assert "Died from severe injuries" in result2
        
        result3 = t("Died of old age")
        assert "Died of old age" in result3
    
    def test_missing_format_args_handled_gracefully(self):
        """Test that missing format arguments don't crash."""
        language_manager.set_language("en-US")
        # Missing 'amount' argument.
        result = t("{name} lost {amount} spirit stones", name="Test")
        # Should return translated string without formatting (or partial).
        assert "Test" in result or "{name}" in result


class TestLanguageManagerIntegration:
    """Tests for LanguageManager integration with i18n."""
    
    def setup_method(self):
        """Reset to default language."""
        reload_translations()
        language_manager.set_language("zh-CN")
    
    def test_language_manager_str(self):
        """Test LanguageManager string representation."""
        language_manager.set_language("zh-CN")
        assert str(language_manager) == "zh-CN"
        
        language_manager.set_language("en-US")
        assert str(language_manager) == "en-US"
    
    def test_invalid_language_falls_back_to_chinese(self):
        """Test that invalid language falls back to Chinese."""
        language_manager.set_language("invalid-lang")
        assert str(language_manager) == "zh-CN"
