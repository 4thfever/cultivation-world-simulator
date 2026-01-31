import sys
import os
from pathlib import Path

# Add src to sys.path
sys.path.append(os.getcwd())

from src.classes.language import language_manager
from src.i18n import t, reload_translations, _get_translation, _get_current_lang

print(f"Initial Language: {_get_current_lang()}")

# Try translating without setting language (should be zh-CN by default per LanguageManager)
print(f"Default 'History' translation: {t('History')}")

# Explicitly set to zh-CN
print("Setting language to zh-CN...")
language_manager.set_language("zh-CN")
print(f"Current Language: {_get_current_lang()}")
print(f"Translated 'History': {t('History')}")
print(f"Translated 'Killed by {{killer}}': {t('Killed by {killer}', killer='张三')}")

# Check internal translation object
trans = _get_translation()
print(f"Translation Object: {trans}")
if trans:
    print(f"Info: {trans.info()}")

# Check file paths
locale_dir = Path("src/i18n/locales")
mo_path = locale_dir / "zh_CN" / "LC_MESSAGES" / "messages.mo"
print(f"MO file exists: {mo_path.exists()}")
print(f"MO file absolute path: {mo_path.absolute()}")
