import os
import pytest
from pathlib import Path
from src.classes.language import language_manager, LanguageType
from src.utils.config import CONFIG, update_paths_for_language
from src.utils.df import load_game_configs, reload_game_configs, game_configs

class TestLanguage:
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
        
        expected_game_configs = Path("static/locales/en-US/game_configs")
        # 注意：Path 比较在不同系统上可能需要 resolve
        assert CONFIG.paths.game_configs.resolve() == expected_game_configs.resolve()
        assert CONFIG.paths.shared_game_configs.resolve() == Path("static/game_configs").resolve()

        # 切回 zh-CN
        language_manager.set_language("zh-CN")
        update_paths_for_language("zh-CN")
        expected_zh = Path("static/locales/zh-CN/game_configs")
        assert CONFIG.paths.game_configs.resolve() == expected_zh.resolve()

    def test_game_config_loading_and_override(self, tmp_path):
        """测试配置加载的合并与覆盖逻辑"""
        # 1. 准备目录结构
        shared_dir = tmp_path / "shared"
        shared_dir.mkdir()
        
        locales_dir = tmp_path / "locales"
        zh_dir = locales_dir / "zh-CN" / "game_configs"
        zh_dir.mkdir(parents=True)
        
        # 2. 创建测试文件
        # shared/common.csv - 只有共享有
        (shared_dir / "common.csv").write_text("id,val\ndesc,val_desc\n1,common_val", encoding="utf-8")
        
        # shared/override_me.csv - 共享有，将被覆盖
        (shared_dir / "override_me.csv").write_text("id,val\ndesc,val_desc\n1,original_val", encoding="utf-8")
        
        # locales/zh-CN/game_configs/override_me.csv - 覆盖版本
        (zh_dir / "override_me.csv").write_text("id,val\ndesc,val_desc\n1,localized_val", encoding="utf-8")
        
        # locales/zh-CN/game_configs/local_only.csv - 只有本地有
        (zh_dir / "local_only.csv").write_text("id,val\ndesc,val_desc\n1,local_val", encoding="utf-8")

        # 3. 临时修改 CONFIG.paths 指向测试目录
        original_shared = CONFIG.paths.shared_game_configs
        original_localized = CONFIG.paths.game_configs
        
        try:
            CONFIG.paths.shared_game_configs = shared_dir
            CONFIG.paths.game_configs = zh_dir
            
            # 4. 执行加载
            loaded = load_game_configs()
            
            # 5. 验证
            # 验证 common.csv 存在
            assert "common" in loaded
            assert loaded["common"][0]["val"] == "common_val"
            
            # 验证 override_me.csv 被覆盖
            assert "override_me" in loaded
            assert loaded["override_me"][0]["val"] == "localized_val"
            
            # 验证 local_only.csv 存在
            assert "local_only" in loaded
            assert loaded["local_only"][0]["val"] == "local_val"
            
        finally:
            # 恢复配置
            CONFIG.paths.shared_game_configs = original_shared
            CONFIG.paths.game_configs = original_localized

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
        from src.classes.magic_stone import MagicStone
        from src.classes.region import NormalRegion
        from src.classes.persona import Persona
        from src.classes.rarity import Rarity, RarityLevel
        from src.classes.avatar.info_presenter import get_avatar_info
        from src.classes.emotions import EmotionType
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
            # Assuming current_loc is None
            assert "Normal Region" in str(region)
            assert "Resource Distribution" in str(region)
            
            # Distance check
            # We mock chebyshev_distance or just rely on it working
            # Distance from (0,0) to (0,0) is 0, months = 1
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
            # Mock other attributes used in get_avatar_info to avoid errors
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
            avatar.tile = None # Fix AttributeError: Mock object has no attribute 'tile' if accessed directly without setup, but get_avatar_info handles it via avatar.tile check? 
            # Actually get_avatar_info accesses avatar.tile.region
            avatar.tile = MagicMock()
            avatar.tile.region = None

            # We need to ensure t("平静") returns "Calm" (based on my PO update)
            info = get_avatar_info(avatar)
            # Emotion key might be translated too "Emotion" -> "Emotion"
            assert info["Emotion"] == "Calm"

            # 切换回中文验证
            language_manager.set_language("zh-CN")
            reload_translations()
            
            assert str(ms) == "100灵石"
            assert "普通区域" in str(region)
            assert "效果：TestEffect" in p.get_detailed_info()
            info_zh = get_avatar_info(avatar)
            assert info_zh["情绪"] == "平静"
            
        finally:
            # Restore to default just in case
            language_manager.set_language("zh-CN")
            reload_translations()
