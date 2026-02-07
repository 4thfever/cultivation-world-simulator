from enum import Enum

class LanguageType(Enum):
    ZH_CN = "zh-CN"
    ZH_TW = "zh-TW"
    EN_US = "en-US"

class LanguageManager:
    def __init__(self):
        self._current = LanguageType.ZH_CN

    @property
    def current(self) -> LanguageType:
        return self._current

    def set_language(self, lang_code: str):
        try:
            # 尝试直接通过值匹配.
            self._current = LanguageType(lang_code)
        except ValueError:
            # 如果匹配失败，默认为 zh-CN.
            self._current = LanguageType.ZH_CN
        
        # Reload i18n translations when language changes.
        from src.i18n import reload_translations
        reload_translations()

        # Update paths and reload game configs
        from src.utils.config import update_paths_for_language
        update_paths_for_language(self._current.value)

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


    def __str__(self):
        return self._current.value

# 全局单例
language_manager = LanguageManager()
