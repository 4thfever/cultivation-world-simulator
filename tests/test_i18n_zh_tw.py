import unittest
from unittest.mock import MagicMock, patch
import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.classes.calendar import get_date_str
from src.classes.sect_region import SectRegion
from src.classes.world import World
from src.classes.language import language_manager, LanguageType
from src.classes.celestial_phenomenon import CelestialPhenomenon
from src.run.data_loader import reload_all_static_data


class TestI18nZhTW(unittest.TestCase):
    """測試繁體中文（zh-TW）i18n 功能"""

    def setUp(self):
        # 儲存當前語言
        self.original_lang = str(language_manager)

    def tearDown(self):
        # 恢復語言
        language_manager.set_language(self.original_lang)

    def test_zh_tw_language_enum_exists(self):
        """驗證 ZH_TW 語言枚舉存在"""
        self.assertTrue(hasattr(LanguageType, 'ZH_TW'))
        self.assertEqual(LanguageType.ZH_TW.value, 'zh-TW')

    def test_language_switch_to_zh_tw(self):
        """驗證可以切換到繁體中文"""
        language_manager.set_language('zh-TW')
        self.assertEqual(str(language_manager), 'zh-TW')
        self.assertEqual(language_manager.current, LanguageType.ZH_TW)

    def test_date_format_zh_tw(self):
        """驗證日期格式在繁體中文下正確顯示"""
        language_manager.set_language('zh-TW')
        # 13 = Year 1, Month 2 (formula: year*12 + month - 1 => 1*12 + 2 - 1 = 13)
        date_str = get_date_str(13)
        self.assertIn('年', date_str)
        self.assertIn('月', date_str)
        self.assertEqual(date_str, '1年2月')

    def test_calendar_i18n_zh_tw(self):
        """驗證日期格式在繁體中文下正確顯示"""
        language_manager.set_language('zh-TW')

        # 測試日期格式
        date_str = get_date_str(13)
        self.assertIn('年', date_str)
        self.assertIn('月', date_str)

    def test_dynamic_translation_zh_tw(self):
        """驗證動態翻譯在繁體中文下正常工作"""
        from src.i18n import t

        language_manager.set_language('zh-TW')

        # 測試基礎翻譯
        text = t('male')
        self.assertIn(text, ['男', '男性'])  # 接受可能的變體

        # 測試帶參數翻譯
        text = t('{winner} defeated {loser}', winner='張三', loser='李四')
        self.assertIn('張三', text)
        self.assertIn('李四', text)
        self.assertIn('戰勝', text)

    def test_realm_translation_zh_tw(self):
        """驗證境界翻譯在繁體中文下正確"""
        # 使用已測試的日期格式功能來驗證翻譯機制
        language_manager.set_language('zh-TW')

        # 驗證基本翻譯機制正常工作
        from src.i18n import t
        result = t('qi_refinement')
        self.assertIn(result, ['鍊氣', '煉氣', '練氣'])  # 接受可能的變體（簡繁轉換差異）

    def test_sect_region_desc_zh_tw(self):
        """驗證宗門駐地描述在繁體中文下正確"""
        from src.i18n import t

        language_manager.set_language('zh-TW')

        # 測試宗門駐地翻譯
        result = t('Sect Headquarters')
        self.assertIn('宗門', result)

    def test_language_fallback_zh_tw_to_zh_cn(self):
        """驗證繁體中文缺少翻譯時回退到簡體中文"""
        from src.i18n import t

        language_manager.set_language('zh-TW')

        # 測試不存在的翻譯（應回退到簡體或原文）
        text = t('non_existent_key_12345')
        self.assertEqual(text, 'non_existent_key_12345')

    def test_zh_tw_locale_files_exist(self):
        """驗證 zh-TW locale 檔案存在"""
        from pathlib import Path

        locale_dir = Path('src/i18n/locales/zh_TW/LC_MESSAGES')

        # 檢查 .po 檔案
        messages_po = locale_dir / 'messages.po'
        self.assertTrue(messages_po.exists(), 'messages.po 應該存在')

        game_configs_po = locale_dir / 'game_configs.po'
        self.assertTrue(game_configs_po.exists(), 'game_configs.po 應該存在')

        # 檢查 .mo 檔案
        messages_mo = locale_dir / 'messages.mo'
        self.assertTrue(messages_mo.exists(), 'messages.mo 應該存在')

        game_configs_mo = locale_dir / 'game_configs.mo'
        self.assertTrue(game_configs_mo.exists(), 'game_configs.mo 應該存在')

    def test_zh_tw_po_file_integrity(self):
        """驗證 zh-TW .po 檔案完整性"""
        try:
            import polib
        except ImportError:
            self.skipTest('polib 未安裝')

        locale_dir = Path('src/i18n/locales/zh_TW/LC_MESSAGES')

        # 檢查 messages.po
        messages_po = polib.pofile(str(locale_dir / 'messages.po'))
        self.assertGreater(len(messages_po), 0, 'messages.po 應包含翻譯條目')

        # 檢查 metadata
        metadata = messages_po.metadata
        self.assertIn('Language', metadata)
        self.assertEqual(metadata.get('Language'), 'zh_TW')

    def test_translation_coverage_zh_tw(self):
        """驗證 zh-TW 翻譯覆蓋率"""
        try:
            import polib
        except ImportError:
            self.skipTest('polib 未安裝')

        locale_dir = Path('src/i18n/locales/zh_TW/LC_MESSAGES')

        # 檢查 messages.po
        messages_po = polib.pofile(str(locale_dir / 'messages.po'))
        translated_count = sum(1 for entry in messages_po if entry.msgstr)
        total_count = len(messages_po)
        coverage = translated_count / total_count if total_count > 0 else 0

        # 翻譯覆蓋率應該 > 95%
        self.assertGreater(coverage, 0.95, f'翻譯覆蓋率應 > 95%，實際: {coverage:.1%}')

    def test_action_translation_zh_tw(self):
        """驗證動作名稱在繁體中文下正確"""
        from src.i18n import t

        language_manager.set_language('zh-TW')

        # 測試動作名稱翻譯
        self.assertEqual(t('cultivate_action_name'), '修煉')
        self.assertEqual(t('breakthrough_action_name'), '突破')
        self.assertEqual(t('escape_action_name'), '逃離')
        self.assertEqual(t('self_heal_action_name'), '療傷')

    def test_emotion_translation_zh_tw(self):
        """驗證情緒在繁體中文下正確"""
        from src.i18n import t

        language_manager.set_language('zh-TW')

        # 測試情緒名稱翻譯
        self.assertEqual(t('emotion_calm'), '平靜')
        self.assertEqual(t('emotion_happy'), '開心')
        self.assertEqual(t('emotion_angry'), '憤怒')
        self.assertEqual(t('emotion_sad'), '悲傷')


if __name__ == '__main__':
    unittest.main()
