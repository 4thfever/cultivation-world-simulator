# Game Configs I18n Refactoring Spec

## Overview

This document describes the refactoring of game configuration files (CSV) to support internationalization via `gettext` (.po/.mo files) instead of maintaining separate CSV files for each language.

## Motivation

- **Single Source of Truth**: Maintain game logic values (probabilities, stats, IDs) in one place.
- **Separation of Concerns**: Separate data configuration from text translation.
- **Standardization**: Use the same toolchain (gettext) for both code strings and config strings.

## Architecture

### 1. Data Source (`static/game_configs/`)
- All CSV files reside in `static/game_configs/`.
- **No language-specific folders** for CSVs (e.g., no `locales/zh-CN/game_configs`).
- CSV Structure Changes:
    - Added `name_id`: Translation key for the name.
    - Added `desc_id`: Translation key for the description.
    - `name` and `desc` columns remain as **Reference/Fallback** (usually containing Chinese).

Example:
```csv
id,name_id,name,desc_id,desc,danger_prob
hidden_domain_wood,HIDDEN_DOMAIN_WOOD_NAME,万木残界,HIDDEN_DOMAIN_WOOD_DESC,此乃...,0.3
```

### 2. Translation Files (`static/locales/`)
- **`game_configs.po`**: Contains translations for config IDs.
    - Generated/Updated via tool scanning CSVs.
- **`messages.po`**: Contains translations for dynamic code strings (existing).

### 3. Build Process
- `tools/i18n/build_mo.py` compiles `game_configs.po` into `game_configs.mo`.
- Runtime uses separate domains: `messages` (default) and `game_configs` (fallback).

### 4. Runtime Loading (`src/utils/df.py`)
1. Load CSV from `static/game_configs/`.
2. For each row:
   - If `name_id` exists: Try `t(name_id)`. If translation found, overwrite `row['name']`.
   - If `desc_id` exists: Try `t(desc_id)`. If translation found, overwrite `row['desc']`.
3. Fallback: If no translation (or `t()` returns key), keep original `name`/`desc` from CSV.

## Maintenance Workflow

### Adding/Modifying Items
1. Edit `static/game_configs/xxx.csv`.
2. Add row with `id`.
3. Fill `name`/`desc` with Chinese text (Reference).
4. Fill `name_id`/`desc_id` (Convention: `{FILE}_{ID}_NAME`).
5. Run extraction tool (to be created) to update `game_configs.pot` and `.po` files.
6. Add English translation in `static/locales/en-US/LC_MESSAGES/game_configs.po`.
7. Run `python tools/i18n/build_mo.py` to compile translation files.

## Tools

- `tools/i18n/migrate_csv.py`: One-off script to migrate existing split CSVs to single CSV + PO.
- `tools/i18n/extract_csv.py`: Script to scan CSVs and update POT/PO files.
