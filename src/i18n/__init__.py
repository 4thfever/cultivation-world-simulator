"""
i18n module for dynamic text translation using gettext.

Usage:
    from src.i18n import t
    
    text = t("{winner} defeated {loser}", winner="Zhang San", loser="Li Si")
"""

import gettext
import logging
from pathlib import Path
from typing import Optional

from src.i18n.locale_registry import get_default_locale, get_fallback_locale

# Cache for loaded translations.
_translations: dict[str, Optional[gettext.GNUTranslations]] = {}

logger = logging.getLogger(__name__)


def _get_locale_dir() -> Path:
    """Get the locales directory path."""
    # src/i18n/__init__.py -> src/i18n -> src -> root
    return Path(__file__).resolve().parent.parent.parent / "static" / "locales"


def _lang_to_locale(lang_code: str) -> str:
    """
    Convert language code to gettext locale name.
    Now we use the same code as folder name (e.g. zh-CN).
    
    Args:
        lang_code: Language code like "zh-CN" or "en-US".
        
    Returns:
        Locale name like "zh-CN" or "en-US".
    """
    return lang_code


def _get_current_lang() -> str:
    """Get current language from LanguageManager."""
    try:
        from src.classes.language import language_manager
        return str(language_manager)
    except ImportError:
        return get_default_locale()


def _get_translation() -> Optional[gettext.GNUTranslations]:
    """
    Get translation object for current language.
    
    Returns:
        GNUTranslations object or None if not found.
    """
    lang = _get_current_lang()
    
    if lang not in _translations:
        locale_dir = _get_locale_dir()
        locale_name = _lang_to_locale(lang)
        
        try:
            trans = gettext.translation(
                "messages",
                localedir=str(locale_dir),
                languages=[locale_name]
            )
        except FileNotFoundError:
            trans = None

        try:
            config_trans = gettext.translation(
                "game_configs",
                localedir=str(locale_dir),
                languages=[locale_name]
            )
            if trans:
                trans.add_fallback(config_trans)
            else:
                trans = config_trans
        except FileNotFoundError:
            pass

        _translations[lang] = trans
    
    return _translations.get(lang)


def _has_explicit_translation_entry(
    trans: Optional[gettext.GNUTranslations],
    message: str,
) -> bool:
    """
    Check whether the current catalog explicitly contains a msgid.

    We cannot rely on `translated == message` to detect missing entries because
    some valid translations are intentionally identical to the source text.
    """
    if trans is None:
        return False

    catalog = getattr(trans, "_catalog", None)
    if isinstance(catalog, dict) and message in catalog:
        return True

    fallback = getattr(trans, "_fallback", None)
    if isinstance(fallback, gettext.GNUTranslations):
        return _has_explicit_translation_entry(fallback, message)

    return False


def t(message: str, **kwargs) -> str:
    """
    Translate a message and format with kwargs.
    
    The message key should be in English. Translations map English -> target language.
    If no translation is found, the original message is returned.
    
    Args:
        message: The message to translate (English).
        **kwargs: Format arguments for the message.
        
    Returns:
        Translated and formatted string.
        
    Example:
        t("{winner} defeated {loser}", winner="Zhang San", loser="Li Si")
        # zh-CN: "Zhang San 战胜了 Li Si"
        # en-US: "Zhang San defeated Li Si"
    """
    trans = _get_translation()
    
    if trans:
        translated = trans.gettext(message)
    else:
        translated = message
    
    # Check for missing translation if not in fallback locale.
    # Do not treat "translation equals source" as missing by itself because
    # some entries are intentionally identical across locales.
    if (
        _get_current_lang() != get_fallback_locale()
        and message.strip()
        and not _has_explicit_translation_entry(trans, message)
    ):
        logger.warning(f"[i18n] Missing translation for msgid: '{message}'")
    
    if kwargs:
        try:
            return translated.format(**kwargs)
        except KeyError as e:
            # If format fails, return translated string without formatting.
            return translated
    return translated


def reload_translations() -> None:
    """
    Clear translation cache.
    
    Call this after language changes to reload translations.
    """
    _translations.clear()


__all__ = ["t", "reload_translations"]
