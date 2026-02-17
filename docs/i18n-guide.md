# I18n Maintenance & Development Guide
注意目前有三个语言：zh-cn, zh-tw, en-us.

## 1. Critical Warning (PowerShell Users)

**Do NOT use redirection (`>>`) in Windows PowerShell to append to PO files.**

*   **Issue**: It appends UTF-16LE content to UTF-8 files, creating `\x00` null bytes and corrupting the file.
*   **Fix**: If corrupted, use a script to remove `\x00` bytes and save as UTF-8 without BOM.

## 2. Directory Structure

```
src/i18n/
├── __init__.py                    # Export t() function

static/locales/
    ├── zh-CN/
    │   ├── LC_MESSAGES/
    │   │   ├── messages.po        # Merged dynamic text translations (Generated)
    │   │   ├── messages.mo        # Compiled binary (Runtime)
    │   │   ├── game_configs.po    # Merged game config translations (Generated)
    │   │   ├── game_configs.mo    # Compiled binary
    │   ├── modules/               # Source modules for messages.po
    │   │   ├── battle.po
    │   │   ├── ui.po
    │   │   └── ...
    │   └── game_configs_modules/  # Source modules for game_configs.po
    │       ├── item.po
    │       └── ...
    └── en-US/
        └── ... (Same structure)
```

## 3. Workflow: Dynamic Text (Code)

Use this workflow when adding internationalization to Python code (f-strings).

1.  **Identify Strings**: Use `grep` to find hardcoded strings.
2.  **Edit Modules**: Add translations to `static/locales/{lang}/modules/{category}.po`.
    *   **Do NOT edit `LC_MESSAGES/messages.po` directly.**
    *   Use English text as `msgid`.
3.  **Update Code**:
    ```python
    from src.i18n import t
    # Before: f"{name} attacked"
    # After:  t("{name} attacked", name=name)
    ```
4.  **Compile**:
    ```bash
    python tools/i18n/build_mo.py
    ```

## 4. Workflow: Game Configs (CSV)

Use this workflow when adding new items/events to CSV files (`static/game_configs/`).

1.  **Edit CSV**:
    *   Add row with `name_id` and `desc_id` (e.g., `ITEM_SWORD_NAME`).
    *   Keep `name` and `desc` columns as reference (usually Chinese).
2.  **Generate Template (POT)**:
    *   Run the extraction tool to update the `game_configs.pot` template:
        ```bash
        python tools/i18n/extract_csv.py
        ```
    *   This script scans all CSVs, extracts `name_id`/`desc_id`, and uses the original Chinese text as comments.
3.  **Update Translations**:
    *   Add translations to `static/locales/{lang}/game_configs_modules/{category}.po`.
4.  **Compile**:
    ```bash
    python tools/i18n/build_mo.py
    ```
    *   Runtime loads CSV, checks `name_id`, and uses `t()` to fetch translation from `game_configs` domain.

## 5. Quality Assurance Tools

Before committing, run the following tools to ensure translation quality:

### Check Duplicates
Checks for duplicate `msgid` entries and inconsistencies between Chinese and English files.

```bash
python tools/i18n/check_po_duplicates.py
```

### Auto-Translate Names (Special Case)
For `last_name.csv` and `given_name.csv`, we use a specialized script to generate English names using Pinyin.

```bash
python tools/i18n/translate_name.py
```
*   This generates/updates `static/locales/en-US/game_configs/last_name.csv` and `given_name.csv` directly.
*   These files are **NOT** handled via the PO/MO system.

增加新文件时，尽量走手动修改而非脚本。
msgid用英文不用中文。
## 6. Development Rules

1.  **Source Split Strategy**: We use split `.po` files in `modules/` to avoid merge conflicts. The build script merges them.
2.  **English Keys**: Use English as `msgid` for dynamic text.
3.  **No Plurals**: Write English strings to avoid pluralization complexity (e.g., "Found {amount} spirit stone(s)").
4.  **Commit MO Files**: Commit compiled `.mo` files to git for easier deployment.
5.  **Formatting**:
    *   No duplicate headers in module files.
    *   Keep one empty line between entries.
    *   **UTF-8 without BOM**.

## 7. Emergency Fixes (Corrupted PO Files)

If a file contains `\x00` bytes (Null characters):
1.  Stop writing.
2.  Run a python script to read as binary, replace `b'\x00'` with `b''`, and save as UTF-8.

## 8. Implementation Patterns by Domain

### 8.1 Actions & MutualActions

**Pattern:** Class Variables + Class Methods

In `Action` or `MutualAction` subclasses, use class variables for static IDs and methods for retrieval.

```python
class MyAction(Action):
    # IDs
    ACTION_NAME_ID = "my_action_name"
    DESC_ID = "my_action_desc"
    REQUIREMENTS_ID = "my_action_req"
    
    # Optional: For MutualActions or Actions with Prompts
    STORY_PROMPT_ID = "my_action_story_prompt"

    # Dynamic text in execution
    def start(self, ...):
        from src.i18n import t
        msg = t("{actor} performs action on {target}", actor=self.avatar.name, target=target.name)
```

**Translation Location:** `static/locales/{lang}/modules/action.po`

### 8.2 Effects

**Pattern:** ID Mapping & JSON Overrides

1.  **Standard Effects**: Mapped in `src/classes/effect/desc.py`.
    *   Key: `extra_max_hp` -> msgid: `effect_extra_max_hp`
2.  **Custom Descriptions (JSON/CSV)**:
    *   Use `_desc` to override the entire description with a translation key.
    *   Use `when_desc` to override the condition code with a human-readable translation key.

    ```json
    {
        "extra_attack": 5,
        "when": "avatar.hp < 50",
        "when_desc": "condition_low_hp",  // msgid: "When HP is low"
        "_desc": "effect_berzerk_mode"    // msgid: "Berzerk Mode: Attack +5 when HP is low"
    }
    ```

**Translation Location:** `static/locales/{lang}/modules/effect.po`

### 8.3 Avatar Info

**Pattern:** Translated Dict Keys

When returning dictionaries for UI display (e.g., `get_avatar_info`), translate the **Keys** directly.

```python
def get_avatar_info(self):
    from src.i18n import t
    return {
        t("Name"): self.name,
        t("Level"): self.level,
        t("Sect"): self.sect.name if self.sect else t("Rogue Cultivator") # Translated values
    }
```

**Translation Location:** `static/locales/{lang}/modules/avatar.po` or `ui.po`

### 8.4 Gatherings (Events)

**Pattern:** Class Method for Prompts

Similar to Actions, use class methods for Storyteller prompts.

```python
@register_gathering
class Auction(Gathering):
    STORY_PROMPT_ID = "auction_story_prompt"
    
    @classmethod
    def get_story_prompt(cls) -> str:
        from src.i18n import t
        return t(cls.STORY_PROMPT_ID)
        
    def get_info(self, world) -> str:
        return t("Auction in progress...")
```

**Translation Location:** `static/locales/{lang}/modules/gathering.po`
