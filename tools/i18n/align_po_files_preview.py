import os
import polib
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.i18n.locale_registry import get_locale_codes

def main():
    base_dir = Path('static/locales')
    locales = get_locale_codes()
    subdirs = ['modules', 'game_configs_modules']
    
    # Collect all msgids from all locales
    # Format: msgid_data[msgid] = {'en-US': (msgstr, original_file), 'zh-CN': ..., 'zh-TW': ...}
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
    def get_target_file(msgid, en_us_file):
        if msgid.startswith('appearance_'):
            return 'modules/avatar.po'
        if msgid.startswith('WORLD_INFO_'):
            return 'game_configs_modules/world_info.po'
        if msgid.startswith('relation_') or msgid in ['grand_parent', 'grand_child', 'martial_grandmaster', 'martial_grandchild', 'martial_sibling']:
            return 'modules/relation.po'
            
        if msgid in ['comma_separator', 'semicolon_separator', 'relation_separator', 'element_separator', 'material_separator']:
            return 'modules/separators.po'
            
        if en_us_file == 'modules/root_element.po':
            if not (msgid.endswith('_element') or msgid.startswith('root_')):
                return 'modules/character_status.po'
                
        if en_us_file == 'modules/sect.po':
            if msgid in ['Unknown reason'] or msgid.startswith('{name} (Deceased'):
                return 'modules/death_reasons.po'
                
        if en_us_file == 'modules/action.po':
            # things like {label}: {names}, {root_name} ({elements}), {sect} {rank}
            if msgid.startswith('{') and msgid.endswith('}'):
                return 'modules/formatted_strings.po'
                
        if en_us_file:
            return en_us_file
            
        # If it wasn't in en-US (unlikely), look at zh-CN
        zh_cn_file = msgid_data[msgid].get('zh-CN', {}).get('file')
        if zh_cn_file:
            if zh_cn_file == 'modules/misc.po':
                return 'modules/misc.po' # fallback
            return zh_cn_file
            
        return 'modules/misc.po'

    target_files_content = defaultdict(list)
    
    for msgid, loc_data in msgid_data.items():
        en_us_file = loc_data.get('en-US', {}).get('file')
        target_file = get_target_file(msgid, en_us_file)
        
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
