# i18n Dynamic Text Implementation Spec

## Overview

This spec covers the internationalization of **dynamic text** (runtime-generated strings) using gettext.

Static content (CSV configs, LLM templates, UI labels) is already handled. This spec addresses the remaining dynamic f-strings in Python code.

---

## Current State

Dynamic Chinese strings are hardcoded in:

```python
# battle.py
text = f"{winner.name} 战胜了 {loser.name}，造成 {damage} 点伤害"

# fortune.py
event_text = f"遭遇奇遇（{theme}），{res_text}"

# misfortune.py
res_text = f"{avatar.name} 损失灵石 {loss} 枚"
```

These need to be internationalized.

---

## Solution: gettext

Use Python's standard `gettext` module with `.po/.mo` translation files.

### Why gettext?

- Python standard library (no extra dependencies).
- Industry standard for i18n.
- Good tooling support (poedit, xgettext, msgfmt).
- Supports pluralization and context.

---

## Implementation Plan

### Phase 1: Infrastructure

#### 1.1 Directory Structure

```
src/i18n/
├── __init__.py                    # Export t() function
└── locales/
    ├── zh_CN/
    │   └── LC_MESSAGES/
    │       ├── messages.po        # Chinese translations (source)
    │       └── messages.mo        # Compiled binary (runtime)
    └── en_US/
        └── LC_MESSAGES/
            ├── messages.po        # English translations (source)
            └── messages.mo        # Compiled binary (runtime)
```

#### 1.2 Create `src/i18n/__init__.py`

```python
import gettext
from pathlib import Path
from typing import Optional

from src.classes.language import language_manager, LanguageType

# Cache for loaded translations
_translations: dict[str, gettext.GNUTranslations] = {}

def _get_translation() -> Optional[gettext.GNUTranslations]:
    """Get translation object for current language."""
    lang = str(language_manager)
    
    if lang not in _translations:
        locale_dir = Path(__file__).parent / "locales"
        
        # Map language codes to gettext locale names
        locale_map = {
            "zh-CN": "zh_CN",
            "en-US": "en_US",
        }
        locale_name = locale_map.get(lang, "zh_CN")
        
        try:
            trans = gettext.translation(
                "messages",
                localedir=str(locale_dir),
                languages=[locale_name]
            )
            _translations[lang] = trans
        except FileNotFoundError:
            _translations[lang] = None
    
    return _translations.get(lang)

def t(message: str, **kwargs) -> str:
    """
    Translate a message and format with kwargs.
    
    Usage:
        t("{winner} defeated {loser}", winner="Zhang San", loser="Li Si")
    
    The message key is in English. Translations map English -> target language.
    """
    trans = _get_translation()
    
    if trans:
        translated = trans.gettext(message)
    else:
        translated = message
    
    if kwargs:
        return translated.format(**kwargs)
    return translated

def reload_translations():
    """Clear translation cache (call after language change)."""
    _translations.clear()
```

#### 1.3 Update `LanguageManager`

```python
# In src/classes/language.py, add callback for language change

def set_language(self, lang_code: str):
    try:
        self._current = LanguageType(lang_code)
    except ValueError:
        self._current = LanguageType.ZH_CN
    
    # Reload translations when language changes
    from src.i18n import reload_translations
    reload_translations()
```

---

### Phase 2: Collect Dynamic Strings

#### 2.1 Files to Scan

| File | Content Type |
|------|--------------|
| `src/classes/battle.py` | Battle result messages |
| `src/classes/fortune.py` | Fortune event messages |
| `src/classes/misfortune.py` | Misfortune event messages |
| `src/classes/tribulation.py` | Tribulation messages |
| `src/classes/death_reason.py` | Death reason text |
| `src/classes/action/*.py` | Action result messages |
| `src/classes/mutual_action/*.py` | Mutual action messages |
| `src/classes/single_choice.py` | Choice result messages |

#### 2.2 Extraction Command

```bash
# Find all f-strings with Chinese characters
grep -rn "f\".*[\u4e00-\u9fff].*\"" src/classes/ --include="*.py"
grep -rn "f'.*[\u4e00-\u9fff].*'" src/classes/ --include="*.py"
```

#### 2.3 Expected Strings (Examples)

From `battle.py`:
- `"{winner} 战胜了 {loser}，造成 {damage} 点伤害。{loser} 遭受重创，当场陨落。"`
- `"{winner} 战胜了 {loser}，{loser} 受伤 {loser_dmg} 点，{winner} 也受伤 {winner_dmg} 点。"`

From `fortune.py`:
- `"遭遇奇遇（{theme}），{result}"`
- `"发现了兵器『{weapon}』，{exchange_result}"`
- `"{name} 获得灵石 {amount} 枚"`
- `"{name} 修为增长 {exp} 点"`
- `"{apprentice} 拜 {master} 为师"`

From `misfortune.py`:
- `"遭遇霉运（{theme}），{result}"`
- `"{name} 损失灵石 {amount} 枚"`
- `"{name} 受到伤害 {damage} 点，剩余HP {current}/{max}"`
- `"{name} 修为倒退 {amount} 点"`

From `death_reason.py`:
- `"被{killer}杀害"`
- `"重伤不治身亡"`
- `"寿元耗尽而亡"`

---

### Phase 3: Create .po Files

#### 3.1 Message Key Convention

Use **English as the message key** (msgid). This makes the code readable and serves as fallback.

```po
msgid "{winner} defeated {loser}, dealing {damage} damage. {loser} was fatally wounded and perished."
msgstr ""
```

#### 3.2 Chinese Translation File

```po
# src/i18n/locales/zh_CN/LC_MESSAGES/messages.po

# Header
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\n"
"Language: zh_CN\n"

# Battle messages
msgid "{winner} defeated {loser}, dealing {damage} damage. {loser} was fatally wounded and perished."
msgstr "{winner} 战胜了 {loser}，造成 {damage} 点伤害。{loser} 遭受重创，当场陨落。"

msgid "{winner} defeated {loser}. {loser} took {loser_dmg} damage, {winner} also took {winner_dmg} damage."
msgstr "{winner} 战胜了 {loser}，{loser} 受伤 {loser_dmg} 点，{winner} 也受伤 {winner_dmg} 点。"

# Fortune messages
msgid "Encountered fortune ({theme}), {result}"
msgstr "遭遇奇遇（{theme}），{result}"

msgid "Found weapon '{weapon}', {exchange_result}"
msgstr "发现了兵器『{weapon}』，{exchange_result}"

msgid "{name} obtained {amount} spirit stones"
msgstr "{name} 获得灵石 {amount} 枚"

msgid "{name} cultivation increased by {exp} points"
msgstr "{name} 修为增长 {exp} 点"

msgid "{apprentice} became disciple of {master}"
msgstr "{apprentice} 拜 {master} 为师"

# Misfortune messages
msgid "Encountered misfortune ({theme}), {result}"
msgstr "遭遇霉运（{theme}），{result}"

msgid "{name} lost {amount} spirit stones"
msgstr "{name} 损失灵石 {amount} 枚"

msgid "{name} took {damage} damage, HP remaining {current}/{max}"
msgstr "{name} 受到伤害 {damage} 点，剩余HP {current}/{max}"

msgid "{name} cultivation regressed by {amount} points"
msgstr "{name} 修为倒退 {amount} 点"

# Death reasons
msgid "Killed by {killer}"
msgstr "被{killer}杀害"

msgid "Died from severe injuries"
msgstr "重伤不治身亡"

msgid "Died of old age"
msgstr "寿元耗尽而亡"
```

#### 3.3 English Translation File

```po
# src/i18n/locales/en_US/LC_MESSAGES/messages.po

# Header
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\n"
"Language: en_US\n"

# Battle messages
msgid "{winner} defeated {loser}, dealing {damage} damage. {loser} was fatally wounded and perished."
msgstr "{winner} defeated {loser}, dealing {damage} damage. {loser} was fatally wounded and perished."

# ... (msgid == msgstr for English)
```

#### 3.4 Compile .po to .mo

```bash
# Install gettext tools if needed (macOS)
brew install gettext

# Compile
msgfmt src/i18n/locales/zh_CN/LC_MESSAGES/messages.po -o src/i18n/locales/zh_CN/LC_MESSAGES/messages.mo
msgfmt src/i18n/locales/en_US/LC_MESSAGES/messages.po -o src/i18n/locales/en_US/LC_MESSAGES/messages.mo
```

Add to Makefile or script:
```makefile
compile-i18n:
	msgfmt src/i18n/locales/zh_CN/LC_MESSAGES/messages.po -o src/i18n/locales/zh_CN/LC_MESSAGES/messages.mo
	msgfmt src/i18n/locales/en_US/LC_MESSAGES/messages.po -o src/i18n/locales/en_US/LC_MESSAGES/messages.mo
```

---

### Phase 4: Modify Code

#### 4.1 Example: battle.py

```python
# Before
text = f"{winner.name} 战胜了 {loser.name}，造成 {l_dmg} 点伤害。{loser.name} 遭受重创，当场陨落。"

# After
from src.i18n import t

text = t(
    "{winner} defeated {loser}, dealing {damage} damage. {loser} was fatally wounded and perished.",
    winner=winner.name,
    loser=loser.name,
    damage=l_dmg
)
```

#### 4.2 Example: fortune.py

```python
# Before
event_text = f"遭遇奇遇（{theme}），{res_text}"

# After
from src.i18n import t

event_text = t("Encountered fortune ({theme}), {result}", theme=theme, result=res_text)
```

#### 4.3 Files to Modify

- [ ] `src/classes/battle.py`
- [ ] `src/classes/fortune.py`
- [ ] `src/classes/misfortune.py`
- [ ] `src/classes/tribulation.py`
- [ ] `src/classes/death_reason.py`
- [ ] `src/classes/single_choice.py`
- [ ] Other files as discovered

---

### Phase 5: Testing

#### 5.1 Unit Tests

```python
# tests/test_i18n.py

import pytest
from src.i18n import t, reload_translations
from src.classes.language import language_manager

class TestI18n:
    def setup_method(self):
        reload_translations()
    
    def test_chinese_translation(self):
        language_manager.set_language("zh-CN")
        result = t("{name} lost {amount} spirit stones", name="张三", amount=100)
        assert "张三" in result
        assert "损失灵石" in result
        assert "100" in result
    
    def test_english_translation(self):
        language_manager.set_language("en-US")
        result = t("{name} lost {amount} spirit stones", name="Zhang San", amount=100)
        assert "Zhang San" in result
        assert "lost" in result
        assert "spirit stones" in result
    
    def test_fallback_on_missing(self):
        language_manager.set_language("en-US")
        # Unknown key returns the key itself
        result = t("Unknown message {x}", x="test")
        assert result == "Unknown message test"
```

#### 5.2 Integration Test

Run a game session, switch languages, verify event log displays correctly.

---

### Phase 6: Save/Load Language

#### 6.1 Save Structure

```python
# Add language to save data
save_data = {
    "version": "1.0",
    "language": str(language_manager),  # "zh-CN" or "en-US"
    "timestamp": ...,
    "world": ...,
    "avatars": ...,
}
```

#### 6.2 Load Logic

```python
def load_save(path: str):
    data = load_json(path)
    
    # Restore language setting
    if "language" in data:
        from src.classes.language import language_manager
        from src.utils.config import update_paths_for_language
        
        language_manager.set_language(data["language"])
        update_paths_for_language()
    
    # Load rest of save data...
```

#### 6.3 Files to Modify

- [ ] Save function (add language field)
- [ ] Load function (restore language)

---

## File Summary

### New Files

| File | Description |
|------|-------------|
| `src/i18n/__init__.py` | Translation module with `t()` function |
| `src/i18n/locales/zh_CN/LC_MESSAGES/messages.po` | Chinese translations |
| `src/i18n/locales/zh_CN/LC_MESSAGES/messages.mo` | Compiled Chinese |
| `src/i18n/locales/en_US/LC_MESSAGES/messages.po` | English translations |
| `src/i18n/locales/en_US/LC_MESSAGES/messages.mo` | Compiled English |
| `tests/test_i18n.py` | Unit tests |

### Modified Files

| File | Changes |
|------|---------|
| `src/classes/language.py` | Add `reload_translations()` callback |
| `src/classes/battle.py` | Replace f-strings with `t()` |
| `src/classes/fortune.py` | Replace f-strings with `t()` |
| `src/classes/misfortune.py` | Replace f-strings with `t()` |
| `src/classes/death_reason.py` | Replace f-strings with `t()` |
| Save/Load code | Add language persistence |

---

## Estimated Effort

| Phase | Time |
|-------|------|
| Phase 1: Infrastructure | 1 hour |
| Phase 2: Collect strings | 1-2 hours |
| Phase 3: Create .po files | 1-2 hours |
| Phase 4: Modify code | 2-3 hours |
| Phase 5: Testing | 1 hour |
| Phase 6: Save/Load | 30 min |
| **Total** | **~8 hours** |

---

## Decisions

1. **Commit `.mo` files to git** - Simpler workflow, no CI compilation needed. `.mo` files are cross-platform compatible (macOS/Windows/Linux).

2. **Pluralization** - Not needed for now. Chinese doesn't have plural forms, and English strings can be written to avoid pluralization (e.g., "lost 100 spirit stones" works for any number).

3. **Fortune/misfortune themes go through `t()`** - Yes. The theme values come from CSV (already translated), but the wrapper strings like `"遭遇奇遇（{theme}）"` need to be translated via `t()`:
   ```python
   # Theme from CSV (already translated based on language)
   theme = "Stumbled into Cave Dwelling"  # or "误入洞府"
   
   # Wrapper string needs t()
   event_text = t("Encountered fortune ({theme}), {result}", theme=theme, result=res_text)
   ```
