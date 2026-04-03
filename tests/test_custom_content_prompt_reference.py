from src.classes.language import language_manager
from src.i18n import reload_translations
from src.server.services.custom_content_service import (
    _category_label,
    _extract_reference_text,
    _resolve_template_path,
)
from src.utils.config import CONFIG


def test_extract_reference_text_returns_generalized_ranges():
    doc = """
类型: int
数值参考:
  - 微量: 1~2 (相当于提升1-2个小境界)
  - 中量: 3~5 (相当于提升半个大境界)
  - 大量: 8+ (相当于提升一个大境界)
"""

    result = _extract_reference_text(doc)

    assert result == "small: 1 to 2; medium: 3 to 5; large: 8+"


def test_extract_reference_text_handles_non_range_labels():
    doc = """
类型: int
数值参考:
  - 普通人: 0
  - 有福缘: 5~10
  - 主角模板: 15~25
  - 倒霉体质: -5~-10
"""

    result = _extract_reference_text(doc)

    assert result == "ordinary: 0; fortunate: 5 to 10; protagonist-tier: 15 to 25; unlucky: -5 to -10"


def test_extract_reference_text_drops_parenthetical_chinese_notes():
    doc = """
类型: float
数值参考:
  - 基础概率: 0.05 (5%)
  - 微量: 0.05 (+5%)
  - 中量: 0.1 (10%)
"""

    result = _extract_reference_text(doc)

    assert result == "base chance: 0.05; small: 0.05; medium: 0.1"


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
