import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.systems.time import get_date_str
from src.classes.environment.sect_region import SectRegion
from src.classes.core.world import World
from src.classes.language import language_manager
from src.classes.celestial_phenomenon import CelestialPhenomenon
from src.run.data_loader import reload_all_static_data

class TestI18nDynamic(unittest.TestCase):
    
    def setUp(self):
        # Save current language
        self.original_lang = str(language_manager)
        
    def tearDown(self):
        # Restore language
        language_manager.set_language(self.original_lang)
        
    def test_date_format_switching(self):
        """验证日期字符串随语言切换"""
        # Test ZH
        language_manager.set_language("zh-CN")
        # 13 = Year 1, Month 2 (formula: year*12 + month - 1 => 1*12 + 2 - 1 = 13)
        date_str_zh = get_date_str(13)
        self.assertIn("年", date_str_zh)
        self.assertIn("月", date_str_zh)
        self.assertEqual(date_str_zh, "1年2月")
        
        # Test EN
        # Use 'en-US' (hyphen) which is the correct enum value
        language_manager.set_language("en-US")
        date_str_en = get_date_str(13)
        self.assertNotIn("年", date_str_en)
        self.assertNotIn("月", date_str_en)
        self.assertEqual(date_str_en, "Year 1 Month 2")

    def test_sect_region_desc_switching(self):
        """验证宗门驻地描述随语言切换"""
        # Provide dummy id, name, desc for SectRegion
        region = SectRegion(id=1, name="Dummy", desc="DummyDesc", sect_name="TestSect", sect_id=1)
        
        # Test ZH
        language_manager.set_language("zh-CN")
        desc_zh = region._get_desc()
        self.assertIn("【TestSect】", desc_zh)
        self.assertIn("宗门驻地", desc_zh)
        
        # Test EN
        language_manager.set_language("en-US")
        desc_en = region._get_desc()
        self.assertIn("(TestSect HQ)", desc_en)
        self.assertNotIn("宗门驻地", desc_en)

    def test_world_info_key_switching(self):
        """验证世界信息 Prompt Key 随语言切换"""
        # Mock World and Phenomenon
        
        # Mock dependencies
        mock_map = MagicMock()
        mock_map.get_info.return_value = {}
        mock_month = MagicMock()
        
        world = World(map=mock_map, month_stamp=mock_month)
        
        # Set phenomenon
        # Provide all required fields
        phenom = CelestialPhenomenon(
            id=1, 
            name="TestPhenomenon", 
            desc="TestDesc",
            rarity=None,
            effects={},
            effect_desc="",
            duration_years=5
        )
        world.current_phenomenon = phenom
        
        # Test ZH
        language_manager.set_language("zh-CN")
        info_zh = world.get_info()
        
        # Verify Key
        self.assertIn("当前天地灵机", info_zh)
        self.assertNotIn("Current World Phenomenon", info_zh)
        
        # Verify Value Format
        val_zh = info_zh["当前天地灵机"]
        self.assertEqual(val_zh, "【TestPhenomenon】TestDesc")
        
        # Test EN
        language_manager.set_language("en-US")
        info_en = world.get_info()
        
        # Verify Key
        self.assertIn("Current World Phenomenon", info_en)
        self.assertNotIn("当前天地灵机", info_en)
        
        # Verify Value Format
        val_en = info_en["Current World Phenomenon"]
        self.assertEqual(val_en, "TestPhenomenon: TestDesc")

if __name__ == '__main__':
    unittest.main()
