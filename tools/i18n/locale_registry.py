import json
from pathlib import Path


def get_project_root() -> Path:
    return Path(__file__).parent.parent.parent


def get_registry_path() -> Path:
    return Path(__file__).with_name("locales.json")


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
