
import pytest
from src.classes.effect.desc import format_effects_to_text
from src.classes.language import language_manager
from src.i18n import reload_translations

class TestEffectDescI18n:
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        # 记录原始语言
        original_lang = str(language_manager)
        yield
        # 恢复
        language_manager.set_language(original_lang)
        reload_translations()

    def test_format_effects_with_desc_override(self):
        """测试 _desc 字段覆盖整个效果描述"""
        language_manager.set_language("zh-CN")
        reload_translations()
        
        # 模拟 弑神枪 的配置
        effects = {
            "extra_battle_strength_points": "3 + avatar.weapon_proficiency * 0.02",
            "_desc": "effect_god_slaying_spear_desc"
        }
        
        text = format_effects_to_text(effects)
        # 应直接显示翻译后的文本，而非 "战力 +3 + ..."
        assert "基于枪法资质提升战力" in text
        assert "avatar.weapon_proficiency" not in text
        
        # 切换语言测试
        language_manager.set_language("en-US")
        reload_translations()
        
        text_en = format_effects_to_text(effects)
        assert "Increases Battle Strength based on Spear Proficiency" in text_en

    def test_format_effects_with_when_desc_override(self):
        """测试 when_desc 字段覆盖条件描述"""
        language_manager.set_language("zh-CN")
        reload_translations()
        
        # 模拟 万兽笛 的配置
        effects = {
            "when": "avatar.spirit_animal is not None",
            "when_desc": "condition_has_spirit_animal",
            "extra_battle_strength_points": 2
        }
        
        text = format_effects_to_text(effects)
        # 期望格式: [拥有本命灵兽时] 战力点数 +2
        assert "[拥有本命灵兽时]" in text
        # 只要包含 "+2" 和 相关的描述词即可，避免对具体的翻译词（战力/战力点数）过于敏感
        assert "+2" in text
        assert "avatar.spirit_animal" not in text
        
        # 切换语言测试
        language_manager.set_language("en-US")
        reload_translations()
        
        text_en = format_effects_to_text(effects)
        assert "[When possessing a Spirit Animal]" in text_en
        assert "+2" in text_en

    def test_mixed_effects_list(self):
        """测试效果列表（混合有无覆盖的情况）"""
        language_manager.set_language("zh-CN")
        reload_translations()
        
        # 模拟 天道均衡 的配置 (列表形式)
        effects = [
            {
                "when": "avatar.cultivation_progress.realm.value >= 6",
                "when_desc": "condition_realm_high",
                "extra_respire_exp": -25
            },
            {
                "when": "avatar.cultivation_progress.realm.value < 6",
                "when_desc": "condition_realm_low",
                "extra_respire_exp": 10
            }
        ]
        
        text = format_effects_to_text(effects)
        
        assert "[化神期及以上时]" in text
        assert "-25" in text
        assert "[化神期以下时]" in text
        assert "+10" in text
        
    def test_fallback_behavior(self):
        """测试没有 override 字段时的回退行为（确保不影响原有功能）"""
        language_manager.set_language("zh-CN")
        reload_translations()
        
        # 普通效果，无 override
        effects = {
            "extra_max_hp": 100,
            "when": "avatar.level > 10"
        }
        
        text = format_effects_to_text(effects)
        # 应使用默认的正则解析
        # 假设 translate_condition 将 "avatar.level > 10" 翻译为 "When level > 10" (或者类似的兜底)
        # 这里只检查关键数值和默认行为存在
        assert "100" in text
        assert "level" in text or "等级" in text 
        assert "[" in text and "]" in text

