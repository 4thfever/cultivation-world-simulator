from enum import Enum

class LanguageType(Enum):
    ZH_CN = "zh-CN"
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
        try:
            from src.i18n import reload_translations
            reload_translations()
        except ImportError:
            pass

    def __str__(self):
        return self._current.value

# 全局单例
language_manager = LanguageManager()
