from __future__ import annotations

from pathlib import Path

from src.classes.language import language_manager
from src.i18n.locale_registry import (
    get_fallback_locale,
    get_source_locale,
    normalize_locale_code,
)


def iter_template_locale_codes(current_locale: str | None = None) -> list[str]:
    locale_code = current_locale or str(language_manager.current)
    ordered: list[str] = []
    for candidate in (locale_code, get_fallback_locale(), get_source_locale()):
        normalized = normalize_locale_code(candidate)
        if normalized not in ordered:
            ordered.append(normalized)
    return ordered


def resolve_locale_template_path(
    filename: str,
    *,
    current_locale: str | None = None,
    preferred_dir: Path | None = None,
    locales_dir: Path | None = None,
) -> Path:
    if preferred_dir is not None:
        preferred_path = preferred_dir / filename
        if preferred_path.exists():
            return preferred_path

    if locales_dir is None:
        from src.utils.config import CONFIG

        locales_dir = Path(CONFIG.paths.get("locales", Path("static/locales")))

    for locale_code in iter_template_locale_codes(current_locale=current_locale):
        candidate = locales_dir / locale_code / "templates" / filename
        if candidate.exists():
            return candidate

    if preferred_dir is not None:
        return preferred_dir / filename
    return locales_dir / normalize_locale_code(current_locale) / "templates" / filename
