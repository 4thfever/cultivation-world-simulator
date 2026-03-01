import os
import pytest
from pathlib import Path
from src.classes.language import language_manager, LanguageType
from src.utils.config import CONFIG, update_paths_for_language
from src.utils.df import load_game_configs, reload_game_configs, game_configs

class TestLanguage:
    def setup_method(self):
        # Reset language to default before each test
        language_manager.set_language("zh-CN")

    def test_language_manager_defaults(self):
        """测试语言管理器默认状态"""
        # 默认应该是 zh-CN
        assert language_manager.current == LanguageType.ZH_CN
        assert str(language_manager) == "zh-CN"

    def test_language_manager_switch(self):
        """测试语言切换"""
        language_manager.set_language("en-US")
        assert language_manager.current == LanguageType.EN_US
        assert str(language_manager) == "en-US"
        
        # 测试无效语言回退
        language_manager.set_language("invalid-lang")
        assert language_manager.current == LanguageType.ZH_CN

    def test_config_path_update(self):
        """测试路径更新逻辑"""
        # 切到 en-US
        language_manager.set_language("en-US")
        update_paths_for_language("en-US")
        
        # 重构后，game_configs 指向单一源 static/game_configs
        expected_game_configs = Path("static/game_configs")
        # 注意：Path 比较在不同系统上可能需要 resolve
        assert CONFIG.paths.game_configs.resolve() == expected_game_configs.resolve()
        assert CONFIG.paths.shared_game_configs.resolve() == Path("static/game_configs").resolve()

        # 切回 zh-CN
        language_manager.set_language("zh-CN")
        update_paths_for_language("zh-CN")
        # 依然指向单一源
        expected_zh = Path("static/game_configs")
        assert CONFIG.paths.game_configs.resolve() == expected_zh.resolve()

    def test_game_config_loading_and_override(self, tmp_path):
        """测试配置加载的 I18n 翻译逻辑"""
        # 1. 准备目录结构
        # 现在不再有 shared/localized 分离，只有一个 game_configs 目录
        game_configs_dir = tmp_path / "game_configs"
        game_configs_dir.mkdir()
        
        # 2. 创建测试文件 test.csv
        # 包含 name_id/desc_id
        csv_content = (
            "id,name_id,name,desc_id,desc\n"
            "名称ID,名称,描述ID,描述\n"
            "test_item,TEST_ITEM_NAME,TestItemCN,TEST_ITEM_DESC,TestDescCN"
        )
        (game_configs_dir / "test.csv").write_text(csv_content, encoding="utf-8")
        
        # 3. 临时修改 CONFIG.paths 指向测试目录
        original_game_configs = CONFIG.paths.game_configs
        original_shared = getattr(CONFIG.paths, "shared_game_configs", None)
        original_localized = getattr(CONFIG.paths, "localized_game_configs", None)
        
        try:
            CONFIG.paths.game_configs = game_configs_dir
            CONFIG.paths.shared_game_configs = game_configs_dir
            CONFIG.paths.localized_game_configs = game_configs_dir
            
            # Mock src.utils.df.t to simulate translation
            # We need to patch 'src.utils.df.t'
            from unittest.mock import patch
            
            # Case 1: Translation exists (Simulating English)
            with patch('src.utils.df.t') as mock_t:
                mock_t.side_effect = lambda x: "TestItemEN" if x == "TEST_ITEM_NAME" else ("TestDescEN" if x == "TEST_ITEM_DESC" else x)
                
                loaded = load_game_configs()
                
                assert "test" in loaded
                item = loaded["test"][0]
                assert item["name"] == "TestItemEN"
                assert item["desc"] == "TestDescEN"
                
            # Case 2: No translation (Simulating Fallback/Chinese)
            with patch('src.utils.df.t') as mock_t:
                # If t returns the key itself (or empty), df.py keeps the original CSV value
                mock_t.side_effect = lambda x: x 
                
                loaded = load_game_configs()
                
                item = loaded["test"][0]
                # Should fallback to CSV values
                assert item["name"] == "TestItemCN"
                assert item["desc"] == "TestDescCN"
            
        finally:
            # 恢复配置
            CONFIG.paths.game_configs = original_game_configs
            if original_shared:
                CONFIG.paths.shared_game_configs = original_shared
            if original_localized:
                CONFIG.paths.localized_game_configs = original_localized

    def test_reload_game_configs_integration(self):
        """集成测试：测试 reload_game_configs 是否真的更新了全局变量"""
        # 这个测试依赖于真实的 static 目录，只做简单检查
        # 确保不会报错
        try:
            reload_game_configs()
            # 至少应该有 sects 或者 region_map
            assert "sect" in game_configs or "region_map" in game_configs
        except Exception as e:
            pytest.fail(f"reload_game_configs failed: {e}")

    def test_i18n_objects_output(self):
        """测试对象输出的国际化"""
        from src.classes.language import language_manager
        from src.i18n import t, reload_translations
        from src.classes.items.magic_stone import MagicStone
        from src.classes.environment.region import NormalRegion
        from src.classes.persona import Persona
        from src.classes.rarity import Rarity, RarityLevel
        from src.classes.core.avatar.info_presenter import get_avatar_info
        from src.classes.emotions import EmotionType
        from src.classes.root import Root
        from src.classes.appearance import get_appearance_by_level
        from unittest.mock import MagicMock

        # 切换到英文
        language_manager.set_language("en-US")
        reload_translations()

        try:
            # 1. MagicStone
            ms = MagicStone(100)
            assert str(ms) == "100 Spirit Stones"

            # 2. Region
            region = NormalRegion(id=1, name="TestRegion", desc="TestDesc")
            assert "Normal Region" in str(region)
            assert "Resource Distribution" in str(region)
            
            # Distance check
            assert "Distance" in region.get_info(current_loc=(0,0), step_len=1)

            # 3. Persona
            p = Persona(
                id=1, key="TEST", name="TestPersona", desc="TestDesc", 
                exclusion_keys=[], rarity=Rarity(RarityLevel.N, 1.0, (255,255,255), "#FFFFFF", "Common"), 
                condition="", effects={}, effect_desc="TestEffect"
            )
            assert "Effect: TestEffect" in p.get_detailed_info()

            # 4. Avatar Emotion
            # Mock Avatar
            avatar = MagicMock()
            avatar.emotion = EmotionType.CALM
            avatar.name = "TestAvatar"
            avatar.gender = "Male"
            avatar.age = MagicMock()
            avatar.age.__str__.return_value = "20"
            avatar.hp = MagicMock()
            avatar.hp.__str__.return_value = "100/100"
            avatar.magic_stone = MagicStone(0)
            avatar.relations = {}
            avatar.sect = None
            avatar.alignment = None
            avatar.root = MagicMock()
            avatar.root.get_info.return_value = "Fire"
            avatar.technique = None
            avatar.cultivation_progress = MagicMock()
            avatar.cultivation_progress.get_info.return_value = "Qi Refinement"
            avatar.personas = []
            avatar.materials = {}
            avatar.appearance = MagicMock()
            avatar.appearance.get_info.return_value = "Handsome"
            avatar.weapon = None
            avatar.auxiliary = None
            avatar.long_term_objective = None
            avatar.short_term_objective = None
            avatar.nickname = None
            avatar.spirit_animal = None
            avatar.orthodoxy = None
            avatar.emotion = EmotionType.CALM
            avatar.tile = MagicMock()
            avatar.tile.region = None
            avatar.world = MagicMock()
            avatar.world.ranking_manager.get_avatar_rank.return_value = None

            info = get_avatar_info(avatar)
            assert info["Emotion"] == "Calm"
            
            # 5. Root (New check)
            # The logic in format_root_cn removes "Root" suffix, so we expect "Thunder"
            assert "Thunder" in Root.THUNDER.get_info()
            assert "Water" in Root.THUNDER.get_info()
            assert "Earth" in Root.THUNDER.get_info()
            
            # 6. Appearance (New check)
            app = get_appearance_by_level(7) # 7 is 俊美/Handsome
            assert "Handsome" in app.get_info()

            # 7. Cultivation Progress (New check)
            from src.systems.cultivation import CultivationProgress
            cp = CultivationProgress(1)
            # In English, we expect space separated translated values
            assert cp.get_info() == "Qi Refinement Early Stage"

            # 切换回中文验证
            language_manager.set_language("zh-CN")
            reload_translations()
            
            assert str(ms) == "100灵石"
            assert "普通区域" in str(region)
            assert "效果：TestEffect" in p.get_detailed_info()
            info_zh = get_avatar_info(avatar)
            assert info_zh["情绪"] == "平静"
            # 中文逻辑去掉了"灵根"后缀
            assert "雷" in Root.THUNDER.get_info()
            assert "俊美" in app.get_info()
            
            # In Chinese, we now expect translated values with space
            assert cp.get_info() == "练气 前期"
            
        finally:
            # Restore to default just in case
            language_manager.set_language("zh-CN")
            reload_translations()
