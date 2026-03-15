import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import polib
except ImportError:
    print("Error: polib is required. Please install it using 'pip install polib'")
    sys.exit(1)

from tools.i18n.locale_registry import (
    get_fallback_locale,
    get_locale_codes,
    get_project_root,
    get_source_locale,
)

def get_all_keys(d, prefix=''):
    keys = {}
    for k, v in d.items():
        full_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            keys.update(get_all_keys(v, full_key))
        else:
            keys[full_key] = v
    return keys

def extract_msgids(filepath: Path) -> dict:
    if not filepath.exists():
        return {}
    po = polib.pofile(str(filepath))
    return {entry.msgid: entry.msgstr for entry in po if entry.msgid}

def generate_report():
    root = get_project_root()
    report_lines = ["# I18n Missing Translations Report\n"]

    base_loc = get_source_locale()
    locales = [loc for loc in get_locale_codes() if loc != base_loc]
    
    # 1. Frontend Check
    report_lines.append("## Frontend Missing\n")
    frontend_base_dir = root / "web" / "src" / "locales"
    
    base_frontend_dir = frontend_base_dir / base_loc
    if base_frontend_dir.exists():
        modules = [f.name for f in base_frontend_dir.iterdir() if f.name.endswith('.json')]
        
        for target_loc in locales:
            report_lines.append(f"### [{target_loc}]")
            missing_found_for_loc = False
            
            for module in modules:
                base_file = base_frontend_dir / module
                target_file = frontend_base_dir / target_loc / module
                
                with open(base_file, 'r', encoding='utf-8') as f:
                    base_data = json.load(f)
                base_keys = get_all_keys(base_data)
                
                target_keys = {}
                if target_file.exists():
                    with open(target_file, 'r', encoding='utf-8') as f:
                        try:
                            target_data = json.load(f)
                            target_keys = get_all_keys(target_data)
                        except json.JSONDecodeError:
                            pass
                            
                missing_keys = {k: v for k, v in base_keys.items() if k not in target_keys or not target_keys[k]}
                
                if missing_keys:
                    missing_found_for_loc = True
                    report_lines.append(f"- File: `web/src/locales/{target_loc}/{module}`")
                    for k, v in missing_keys.items():
                        # Truncate value if it's too long
                        val_str = str(v).replace('\n', ' ')
                        if len(val_str) > 50:
                            val_str = val_str[:47] + "..."
                        report_lines.append(f"  - Missing key: `{k}` ({base_loc} value: \"{val_str}\")")
            
            if not missing_found_for_loc:
                report_lines.append("- All keys are fully translated.\n")
            else:
                report_lines.append("")
    else:
        report_lines.append(f"`{base_loc}` base directory not found for frontend.\n")

    # 2. Backend Check
    report_lines.append("## Backend Missing\n")
    module_dirs = ["modules", "game_configs_modules"]
    
    for target_loc in locales:
        report_lines.append(f"### [{target_loc}]")
        missing_found_for_loc = False
        
        for module_dir in module_dirs:
            base_dir = root / "static" / "locales" / base_loc / module_dir
            if not base_dir.exists():
                continue
                
            po_files = [f.name for f in base_dir.iterdir() if f.name.endswith('.po')]
            
            for po_file in po_files:
                base_file_path = base_dir / po_file
                target_file_path = root / "static" / "locales" / target_loc / module_dir / po_file
                
                base_entries = extract_msgids(base_file_path)
                target_entries = extract_msgids(target_file_path)
                
                missing_msgids = []
                for msgid, _ in base_entries.items():
                    # For backend, we just need the msgid to exist in target
                    # since msgid is the English string. For non-fallback locales,
                    # we also treat empty msgstr as missing.
                    if msgid not in target_entries:
                        missing_msgids.append(msgid)
                    elif target_loc != get_fallback_locale() and not target_entries[msgid]:
                        # If the entry exists but the translation is empty, it's still missing.
                        missing_msgids.append(msgid)
                
                if missing_msgids:
                    missing_found_for_loc = True
                    report_lines.append(f"- File: `static/locales/{target_loc}/{module_dir}/{po_file}`")
                    for msgid in missing_msgids:
                        val_str = msgid.replace('\n', ' ')
                        if len(val_str) > 50:
                            val_str = val_str[:47] + "..."
                        report_lines.append(f"  - Missing msgid: \"{val_str}\"")
        
        if not missing_found_for_loc:
            report_lines.append("- All msgids are present.\n")
        else:
            report_lines.append("")

    report_path = root / "i18n_missing_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
        
    print(f"Report generated successfully at: {report_path}")

if __name__ == "__main__":
    generate_report()
