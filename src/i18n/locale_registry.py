import json
from functools import lru_cache
from pathlib import Path


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def get_registry_path() -> Path:
    return get_project_root() / "static" / "locales" / "registry.json"


@lru_cache(maxsize=1)
def load_locale_registry() -> dict:
    with open(get_registry_path(), "r", encoding="utf-8") as f:
        registry = json.load(f)
    _validate_registry(registry)
    return registry


def _validate_registry(registry: dict) -> None:
    if not isinstance(registry, dict):
        raise ValueError("Locale registry must be a JSON object")

    required_fields = ("default_locale", "fallback_locale", "schema_locale", "locales")
    missing_fields = [field for field in required_fields if field not in registry]
    if missing_fields:
        raise ValueError(f"Locale registry missing required field(s): {', '.join(missing_fields)}")

    locales = registry["locales"]
    if not isinstance(locales, list) or not locales:
        raise ValueError("Locale registry must define a non-empty 'locales' list")

    codes: list[str] = []
    source_of_truth_count = 0
    for item in locales:
        if not isinstance(item, dict):
            raise ValueError("Each locale entry must be an object")
        code = str(item.get("code", "")).strip()
        if not code:
            raise ValueError("Each locale entry must define a non-empty 'code'")
        if "html_lang" not in item:
            raise ValueError(f"Locale entry '{code}' is missing required field 'html_lang'")
        codes.append(code)
        if item.get("source_of_truth"):
            source_of_truth_count += 1

    duplicates = sorted({code for code in codes if codes.count(code) > 1})
    if duplicates:
        raise ValueError(f"Locale registry contains duplicate code(s): {', '.join(duplicates)}")

    for field in ("default_locale", "fallback_locale", "schema_locale"):
        if str(registry[field]) not in codes:
            raise ValueError(f"Locale registry field '{field}' must reference an existing locale code")

    if source_of_truth_count != 1:
        raise ValueError("Locale registry must contain exactly one source_of_truth locale")


def get_locale_entries(enabled_only: bool = True) -> list[dict]:
    registry = load_locale_registry()
    locales = list(registry.get("locales", []))
    if enabled_only:
        return [item for item in locales if item.get("enabled", True)]
    return locales


def get_locale_codes(enabled_only: bool = True) -> list[str]:
    return [item["code"] for item in get_locale_entries(enabled_only=enabled_only)]


def get_default_locale() -> str:
    return str(load_locale_registry()["default_locale"])


def get_fallback_locale() -> str:
    return str(load_locale_registry()["fallback_locale"])


def get_schema_locale() -> str:
    return str(load_locale_registry()["schema_locale"])


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
    default_entry = get_locale_entry(get_default_locale(), enabled_only=False)
    if default_entry and default_entry.get("html_lang"):
        return str(default_entry["html_lang"])
    return "en"


def uses_space_separated_names(locale_code: str | None) -> bool:
    html_lang = get_html_lang(locale_code).lower()
    return not html_lang.startswith(("zh", "ja", "ko"))
