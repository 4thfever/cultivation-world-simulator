from src.i18n.locale_registry import coerce_locale_code, get_default_locale


class LanguageManager:
    def __init__(self):
        self._current = get_default_locale()

    @property
    def current(self) -> str:
        return self._current

    def set_language(self, lang_code: str):
        self._current = coerce_locale_code(lang_code, enabled_only=False)

        # Reload i18n translations when language changes.
        from src.i18n import reload_translations
        reload_translations()

        # Update paths and reload game configs
        from src.utils.config import update_paths_for_language
        update_paths_for_language(self._current)

        try:
            from src.utils.df import reload_game_configs
            reload_game_configs()
        except ImportError:
            # Prevent circular import crash during initialization
            pass

        try:
            from src.utils.name_generator import reload as reload_names
            reload_names()
        except ImportError:
            pass

        try:
            from src.classes.core.dynasty import reload as reload_dynasties
            reload_dynasties()
        except ImportError:
            pass

    def __str__(self):
        return self._current


# 全局单例
language_manager = LanguageManager()
