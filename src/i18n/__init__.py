"""
i18n module for dynamic text translation using gettext.

Usage:
    from src.i18n import t
    
    text = t("{winner} defeated {loser}", winner="Zhang San", loser="Li Si")
"""

import gettext
from pathlib import Path
from typing import Optional

# Cache for loaded translations.
_translations: dict[str, Optional[gettext.GNUTranslations]] = {}


def _get_locale_dir() -> Path:
    """Get the locales directory path."""
    return Path(__file__).parent / "locales"


def _lang_to_locale(lang_code: str) -> str:
    """
    Convert language code to gettext locale name.
    
    Args:
        lang_code: Language code like "zh-CN" or "en-US".
        
    Returns:
        Locale name like "zh_CN" or "en_US".
    """
    locale_map = {
        "zh-CN": "zh_CN",
        "en-US": "en_US",
    }
    return locale_map.get(lang_code, "zh_CN")


def _get_current_lang() -> str:
    """Get current language from LanguageManager."""
    try:
        from src.classes.language import language_manager
        return str(language_manager)
    except ImportError:
        return "zh-CN"


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
            _translations[lang] = trans
        except FileNotFoundError:
            # No translation file found, will use message as-is.
            _translations[lang] = None
    
    return _translations.get(lang)


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
