from pathlib import Path
import json
import pytest

from src.i18n.locale_registry import (
    get_default_locale,
    get_locale_codes,
    get_registry_path,
    load_locale_registry,
    get_source_locale,
)


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_locale_registry_path_moved_to_static():
    project_root = get_project_root()
    expected_path = project_root / "static" / "locales" / "registry.json"

    assert get_registry_path() == expected_path
    assert expected_path.exists()


def test_runtime_code_no_longer_depends_on_tools_locale_registry():
    src_root = get_project_root() / "src"
    offenders: list[str] = []

    for py_file in src_root.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        if "tools.i18n.locale_registry" in content:
            offenders.append(str(py_file.relative_to(get_project_root())))

    assert not offenders, (
        "Runtime code should not import tools.i18n.locale_registry anymore: "
        + ", ".join(sorted(offenders))
    )


def test_locale_registry_basic_contract():
    locales = get_locale_codes(enabled_only=False)

    assert get_default_locale() == "zh-CN"
    assert get_source_locale() in locales
    assert "vi-VN" in locales


def test_locale_registry_fails_fast_when_required_fields_missing(tmp_path, monkeypatch):
    broken_registry = tmp_path / "registry.json"
    broken_registry.write_text(json.dumps({"locales": [{"code": "zh-CN", "html_lang": "zh-CN", "source_of_truth": True}]}), encoding="utf-8")

    monkeypatch.setattr("src.i18n.locale_registry.get_registry_path", lambda: broken_registry)
    load_locale_registry.cache_clear()

    try:
        with pytest.raises(ValueError, match="missing required field"):
            load_locale_registry()
    finally:
        load_locale_registry.cache_clear()
