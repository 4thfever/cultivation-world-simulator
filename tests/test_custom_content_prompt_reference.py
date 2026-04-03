from src.classes.language import language_manager
from src.i18n import reload_translations
from src.classes.effect import get_effect_prompt_meta_map
from src.i18n.template_resolver import resolve_locale_template_path
from src.server.services.custom_content_service import (
    _category_label,
    _format_reference_text,
    _resolve_template_path,
)
from src.utils.config import CONFIG


def test_effect_prompt_meta_covers_all_effects():
    meta_map = get_effect_prompt_meta_map()

    assert "extra_battle_strength_points" in meta_map
    assert "legal_actions" in meta_map


def test_format_reference_text_reads_structured_meta():
    original_lang = str(language_manager)
    try:
        language_manager._current = "zh-CN"
        reload_translations()
        result = _format_reference_text("extra_battle_strength_points")
        assert result == "小: 1 to 2; 中: 3 to 5; 大: 8+"
    finally:
        language_manager._current = original_lang
        reload_translations()


def test_format_reference_text_includes_constraints_from_meta():
    original_lang = str(language_manager)
    try:
        language_manager._current = "zh-CN"
        reload_translations()
        result = _format_reference_text("shop_buy_price_reduction")
        assert result == "小: 0.1; 中: 0.5; 最终乘区 >= 1.0"
    finally:
        language_manager._current = original_lang
        reload_translations()


def test_category_label_uses_gettext_translations():
    original_lang = str(language_manager)
    try:
        language_manager._current = "zh-CN"
        reload_translations()
        assert _category_label("technique") == "功法"

        language_manager._current = "vi-VN"
        reload_translations()
        assert _category_label("auxiliary") == "trang bị phụ trợ"
    finally:
        language_manager._current = original_lang
        reload_translations()


def test_resolve_template_path_falls_back_across_registered_locales(tmp_path, monkeypatch):
    original_lang = str(language_manager)
    original_templates = CONFIG.paths.templates
    original_locales = CONFIG.paths.locales

    try:
        language_manager._current = "vi-VN"
        reload_translations()

        locales_dir = tmp_path / "locales"
        current_templates = locales_dir / "vi-VN" / "templates"
        fallback_templates = locales_dir / "en-US" / "templates"
        source_templates = locales_dir / "zh-CN" / "templates"
        current_templates.mkdir(parents=True)
        fallback_templates.mkdir(parents=True)
        source_templates.mkdir(parents=True)

        fallback_file = fallback_templates / "custom_content.txt"
        fallback_file.write_text("fallback", encoding="utf-8")

        monkeypatch.setattr(CONFIG.paths, "templates", current_templates)
        monkeypatch.setattr(CONFIG.paths, "locales", locales_dir)

        assert _resolve_template_path("custom_content.txt") == fallback_file

        fallback_file.unlink()
        source_file = source_templates / "custom_content.txt"
        source_file.write_text("source", encoding="utf-8")

        assert _resolve_template_path("custom_content.txt") == source_file
    finally:
        language_manager._current = original_lang
        reload_translations()
        CONFIG.paths.templates = original_templates
        CONFIG.paths.locales = original_locales


def test_shared_template_resolver_falls_back_across_registered_locales(tmp_path):
    locales_dir = tmp_path / "locales"
    fallback_templates = locales_dir / "en-US" / "templates"
    source_templates = locales_dir / "zh-CN" / "templates"
    fallback_templates.mkdir(parents=True)
    source_templates.mkdir(parents=True)

    fallback_file = fallback_templates / "sect_thinker.txt"
    fallback_file.write_text("fallback", encoding="utf-8")
    assert resolve_locale_template_path(
        "sect_thinker.txt",
        current_locale="vi-VN",
        preferred_dir=locales_dir / "vi-VN" / "templates",
        locales_dir=locales_dir,
    ) == fallback_file

    fallback_file.unlink()
    source_file = source_templates / "sect_thinker.txt"
    source_file.write_text("source", encoding="utf-8")
    assert resolve_locale_template_path(
        "sect_thinker.txt",
        current_locale="vi-VN",
        preferred_dir=locales_dir / "vi-VN" / "templates",
        locales_dir=locales_dir,
    ) == source_file
