import pytest
import os
from pathlib import Path
from collections import Counter

from src.i18n.locale_registry import get_locale_codes, get_source_locale

# 尝试导入 polib，如果失败则在测试中标记 skip
try:
    import polib
    HAS_POLIB = True
except ImportError:
    HAS_POLIB = False

def get_project_root() -> Path:
    return Path(__file__).parent.parent

def extract_msgids(filepath: Path) -> list[str]:
    if not HAS_POLIB:
        return []
    po = polib.pofile(str(filepath))
    # We ignore empty msgids as they are usually header entries in PO files
    return [entry.msgid for entry in po if entry.msgid]

class TestBackendLocales:
    @pytest.mark.skipif(not HAS_POLIB, reason="polib not installed")
    def test_no_duplicate_msgids(self):
        """检查所有合并后的 messages.po 是否存在重复的 msgid"""
        root = get_project_root()
        locales = get_locale_codes()
        
        errors = []
        for loc in locales:
            po_file = root / "static" / "locales" / loc / "LC_MESSAGES" / "messages.po"
            if not po_file.exists():
                errors.append(f"File not found: {po_file}")
                continue
                
            msgids = extract_msgids(po_file)
            counter = Counter(msgids)
            duplicates = {msgid: count for msgid, count in counter.items() if count > 1}
            
            if duplicates:
                errors.append(f"Found duplicates in {loc}/messages.po:")
                for msgid, count in sorted(duplicates.items()):
                    errors.append(f"  - '{msgid}' appears {count} times")
                    
        if errors:
            pytest.fail("\n".join(errors))

    @pytest.mark.skipif(not HAS_POLIB, reason="polib not installed")
    def test_po_modules_keys_consistency(self):
        """
        检查所有语言下的分模块 .po 文件，确保不同语言之间整体拥有完全相同的 msgid 集合。
        因为有些模块文件只在某种语言中存在（如开发者把词条放错了模块），
        所以我们做的是 **全局层级 (Global Level)** 的比较，
        即 `zh-CN` 所有模块的 msgid 集合与 `en-US` 所有模块的 msgid 集合必须严格一致。
        """
        root = get_project_root()
        locales = get_locale_codes()
        module_dirs = ["modules", "game_configs_modules"]
        
        errors = []
        
        # 收集每个语言在所有模块中的全局 msgids
        loc_global_keys = {loc: set() for loc in locales}
        
        for loc in locales:
            for module_dir in module_dirs:
                dir_path = root / "static" / "locales" / loc / module_dir
                if dir_path.exists():
                    for po_file in dir_path.glob("*.po"):
                        msgids = extract_msgids(po_file)
                        loc_global_keys[loc].update(msgids)
                        
        # 交叉验证
        base_loc = get_source_locale()
        base_set = loc_global_keys[base_loc]
        
        for other_loc in locales:
            if other_loc == base_loc:
                continue
                
            other_set = loc_global_keys[other_loc]
            
            missing = base_set - other_set
            extra = other_set - base_set
            
            if missing:
                errors.append(f"[{other_loc}] is missing {len(missing)} msgids present in {base_loc}:\n" + 
                                "\n".join(f"  - {m}" for m in sorted(missing)[:15]))
            if extra:
                errors.append(f"[{other_loc}] has {len(extra)} extra msgids not in {base_loc}:\n" + 
                                "\n".join(f"  + {m}" for m in sorted(extra)[:15]))

        if errors:
            pytest.fail("Backend PO global keys validation FAILED:\n" + "\n".join(errors))

