import os
import polib
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.i18n.locale_registry import (
    get_fallback_locale,
    get_locale_codes,
    get_source_locale,
)


def build_locale_priority(*, prefer_locale: str | None = None) -> list[str]:
    locales = get_locale_codes(enabled_only=False)
    ordered: list[str] = []

    def add(locale_code: str | None) -> None:
        if locale_code and locale_code in locales and locale_code not in ordered:
            ordered.append(locale_code)

    add(prefer_locale)
    add(get_fallback_locale())
    add(get_source_locale())

    for locale in locales:
        add(locale)

    return ordered


def pick_locale_data(item_data: dict, *preferred_locales: str | None) -> dict:
    for locale_code in build_locale_priority(prefer_locale=preferred_locales[0] if preferred_locales else None):
        locale_data = item_data.get(locale_code)
        if locale_data:
            return locale_data
    return {}

def main():
    base_dir = Path('static/locales')
    locales = get_locale_codes()
    subdirs = ['modules', 'game_configs_modules']
    
    # Collect all msgids from all locales
    # Format: msgid_data[msgid] = {locale_code: (msgstr, original_file), ...}
    msgid_data = defaultdict(dict)
    
    for locale in locales:
        locale_dir = base_dir / locale
        for subdir in subdirs:
            subdir_path = locale_dir / subdir
            if not subdir_path.exists():
                continue
            for file_path in subdir_path.glob('*.po'):
                rel_file = f"{subdir}/{file_path.name}"
                po = polib.pofile(str(file_path))
                for entry in po:
                    if entry.msgid:
                        msgid_data[entry.msgid][locale] = {
                            'msgstr': entry.msgstr,
                            'file': rel_file
                        }
                        
    # Determine target files
    def get_target_file(msgid, preferred_file):
        if msgid.startswith('appearance_'):
            return 'modules/avatar.po'
        if msgid.startswith('WORLD_INFO_'):
            return 'game_configs_modules/world_info.po'
        if msgid.startswith('relation_') or msgid in ['grand_parent', 'grand_child', 'martial_grandmaster', 'martial_grandchild', 'martial_sibling']:
            return 'modules/relation.po'
            
        if msgid in ['comma_separator', 'semicolon_separator', 'relation_separator', 'element_separator', 'material_separator']:
            return 'modules/separators.po'
            
        if preferred_file == 'modules/root_element.po':
            if not (msgid.endswith('_element') or msgid.startswith('root_')):
                return 'modules/character_status.po'
                
        if preferred_file == 'modules/sect.po':
            if msgid in ['Unknown reason'] or msgid.startswith('{name} (Deceased'):
                return 'modules/death_reasons.po'
                
        if preferred_file == 'modules/action.po':
            # things like {label}: {names}, {root_name} ({elements}), {sect} {rank}
            if msgid.startswith('{') and msgid.endswith('}'):
                return 'modules/formatted_strings.po'
                
        if preferred_file:
            return preferred_file

        fallback_file = pick_locale_data(msgid_data[msgid], get_source_locale()).get('file')
        if fallback_file:
            if fallback_file == 'modules/misc.po':
                return 'modules/misc.po' # fallback
            return fallback_file
            
        return 'modules/misc.po'

    target_files_content = defaultdict(list)
    
    for msgid, loc_data in msgid_data.items():
        preferred_file = pick_locale_data(loc_data, get_fallback_locale()).get('file')
        target_file = get_target_file(msgid, preferred_file)
        
        target_files_content[target_file].append({
            'msgid': msgid,
            'data': loc_data
        })
        
    print(f"Total msgids: {len(msgid_data)}")
    print(f"Total target files: {len(target_files_content)}")
    
    with open('mapping_preview.txt', 'w', encoding='utf-8') as f:
        for t_file, items in sorted(target_files_content.items()):
            f.write(f"\n[{t_file}] ({len(items)} items)\n")
            for item in items[:5]: # print first 5 items to preview
                f.write(f"  - {item['msgid']}\n")
            if len(items) > 5:
                f.write(f"  ... and {len(items) - 5} more\n")

if __name__ == '__main__':
    main()
