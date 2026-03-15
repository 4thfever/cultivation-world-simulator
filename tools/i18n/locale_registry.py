import json
from functools import lru_cache
from pathlib import Path


def get_project_root() -> Path:
    return Path(__file__).parent.parent.parent


def get_registry_path() -> Path:
    return Path(__file__).with_name("locales.json")


@lru_cache(maxsize=1)
def load_locale_registry() -> dict:
    with open(get_registry_path(), "r", encoding="utf-8") as f:
        return json.load(f)


def get_locale_entries(enabled_only: bool = True) -> list[dict]:
    registry = load_locale_registry()
    locales = list(registry.get("locales", []))
    if enabled_only:
        return [item for item in locales if item.get("enabled", True)]
    return locales


def get_locale_codes(enabled_only: bool = True) -> list[str]:
    return [item["code"] for item in get_locale_entries(enabled_only=enabled_only)]


def get_default_locale() -> str:
    return str(load_locale_registry().get("default_locale", "zh-CN"))


def get_fallback_locale() -> str:
    return str(load_locale_registry().get("fallback_locale", "en-US"))


def get_schema_locale() -> str:
    return str(load_locale_registry().get("schema_locale", get_fallback_locale()))


def get_source_locale() -> str:
    for item in get_locale_entries(enabled_only=False):
        if item.get("source_of_truth"):
            return str(item["code"])
    return get_default_locale()


def normalize_locale_code(locale_code: str | None) -> str:
    if not locale_code:
        return get_default_locale()
    return str(locale_code).replace("_", "-")


def get_locale_entry(locale_code: str | None, enabled_only: bool = False) -> dict | None:
    normalized = normalize_locale_code(locale_code)
    for item in get_locale_entries(enabled_only=enabled_only):
        if str(item.get("code")) == normalized:
            return item
    return None


def is_locale_supported(locale_code: str | None, enabled_only: bool = False) -> bool:
    return get_locale_entry(locale_code, enabled_only=enabled_only) is not None


def coerce_locale_code(locale_code: str | None, enabled_only: bool = False) -> str:
    normalized = normalize_locale_code(locale_code)
    if is_locale_supported(normalized, enabled_only=enabled_only):
        return normalized
    return get_default_locale()


def get_html_lang(locale_code: str | None) -> str:
    entry = get_locale_entry(locale_code, enabled_only=False)
    if entry and entry.get("html_lang"):
        return str(entry["html_lang"])
    return "en"


def uses_space_separated_names(locale_code: str | None) -> bool:
    html_lang = get_html_lang(locale_code).lower()
    return not html_lang.startswith(("zh", "ja", "ko"))
