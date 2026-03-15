import os
import shutil
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

def create_po_file(locale):
    po = polib.POFile()
    po.metadata = {
        'Project-Id-Version': 'cultivation-world-simulator 1.0',
        'Report-Msgid-Bugs-To': '',
        'POT-Creation-Date': '2024-01-20 00:00+0000',
        'PO-Revision-Date': '2024-01-20 00:00+0000',
        'Last-Translator': '',
        'Language-Team': locale,
        'Language': locale.replace('-', '_'),
        'MIME-Version': '1.0',
        'Content-Type': 'text/plain; charset=UTF-8',
        'Content-Transfer-Encoding': '8bit',
    }
    return po


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
                            'file': rel_file,
                            'msgid_plural': entry.msgid_plural,
                            'msgstr_plural': entry.msgstr_plural,
                            'comment': entry.comment,
                            'tcomment': entry.tcomment,
                            'flags': entry.flags,
                            'occurrences': entry.occurrences,
                        }
                        
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
            if msgid.startswith('{') and msgid.endswith('}'):
                return 'modules/formatted_strings.po'
                
        if preferred_file:
            return preferred_file

        fallback_file = pick_locale_data(msgid_data[msgid], get_source_locale()).get('file')
        if fallback_file:
            if fallback_file == 'modules/misc.po':
                return 'modules/misc.po'
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
        
    for locale in locales:
        locale_dir = base_dir / locale
        # Clean up existing subdirs
        for subdir in subdirs:
            subdir_path = locale_dir / subdir
            if subdir_path.exists():
                shutil.rmtree(subdir_path)
            subdir_path.mkdir(parents=True, exist_ok=True)
            
        for rel_file, items in target_files_content.items():
            file_path = locale_dir / rel_file
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            po = create_po_file(locale)
            
            # Keep items sorted by msgid to maintain stability
            sorted_items = sorted(items, key=lambda x: x['msgid'])
            
            for item in sorted_items:
                msgid = item['msgid']
                loc_data = item['data'].get(locale)
                
                # If loc_data is missing, take metadata from another locale
                meta_source = loc_data or pick_locale_data(item['data'], locale)
                
                msgstr = loc_data['msgstr'] if loc_data else ''
                msgid_plural = meta_source.get('msgid_plural', '')
                msgstr_plural = loc_data['msgstr_plural'] if loc_data and loc_data.get('msgstr_plural') else {}
                
                entry = polib.POEntry(
                    msgid=msgid,
                    msgstr=msgstr,
                    comment=meta_source.get('comment', ''),
                    tcomment=meta_source.get('tcomment', ''),
                    flags=meta_source.get('flags', []),
                    occurrences=meta_source.get('occurrences', []),
                )
                if msgid_plural:
                    entry.msgid_plural = msgid_plural
                    if msgstr_plural:
                        entry.msgstr_plural = msgstr_plural
                    
                po.append(entry)
                
            po.save(str(file_path))
            
if __name__ == '__main__':
    main()
