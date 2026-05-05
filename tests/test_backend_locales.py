import pytest
import os
import re
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

def extract_po_pairs(filepath: Path) -> dict[str, str]:
    if not HAS_POLIB or not filepath.exists():
        return {}
    po = polib.pofile(str(filepath))
    return {entry.msgid: entry.msgstr for entry in po if entry.msgid and not entry.obsolete}

def contains_chinese(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text or ""))

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

    def test_template_files_consistency(self):
        """检查所有启用语言的 templates 目录与 source locale 保持同名模板集合。"""
        root = get_project_root()
        locales = get_locale_codes()
        base_loc = get_source_locale()
        base_template_dir = root / "static" / "locales" / base_loc / "templates"

        assert base_template_dir.exists(), f"Base template directory not found: {base_template_dir}"

        base_templates = {
            path.name
            for path in base_template_dir.glob("*.txt")
        }
        errors = []

        for loc in locales:
            target_template_dir = root / "static" / "locales" / loc / "templates"
            if not target_template_dir.exists():
                errors.append(f"Template directory not found: {target_template_dir}")
                continue

            target_templates = {path.name for path in target_template_dir.glob("*.txt")}
            missing = sorted(base_templates - target_templates)
            if missing:
                errors.append(
                    f"[{loc}] missing template files present in {base_loc}:\n"
                    + "\n".join(f"  - {name}" for name in missing)
                )

        if errors:
            pytest.fail("Backend template validation FAILED:\n" + "\n".join(errors))

    @pytest.mark.skipif(not HAS_POLIB, reason="polib not installed")
    def test_non_chinese_locale_critical_race_entries_do_not_use_chinese_msgstr(self):
        """
        关键 race/yao 词条一旦存在于非中文 locale，就不能用中文 msgstr 伪装已翻译。
        Phase 1 可以缺目标语言词条，但不能把中文副本合进 en-US 等目录。
        """
        root = get_project_root()
        source_loc = get_source_locale()
        cjk_free_locales = {"en-US", "vi-VN"}
        locales = [
            loc
            for loc in get_locale_codes()
            if loc != source_loc and loc in cjk_free_locales
        ]
        critical_msgids = {
            "Race",
            "Race [{name}]",
            "Race: {race}",
            "yao_backstory_constraint",
            "effect_extra_eat_mortals_exp_multiplier",
            "effect_extra_cross_race_friendliness",
            "RACE_HUMAN_NAME",
            "RACE_WOLF_NAME",
            "RACE_WOLF_DESC",
            "PERSONA_1015_NAME",
            "PERSONA_1015_DESC",
            "PERSONA_1016_NAME",
            "PERSONA_1016_DESC",
            "WORLD_INFO_RACE_TITLE",
            "WORLD_INFO_RACE_NAME",
            "WORLD_INFO_RACE_DESC",
        }

        errors = []
        for loc in locales:
            for domain in ("messages", "game_configs"):
                po_file = root / "static" / "locales" / loc / "LC_MESSAGES" / f"{domain}.po"
                pairs = extract_po_pairs(po_file)
                for msgid in sorted(critical_msgids & pairs.keys()):
                    msgstr = pairs[msgid]
                    if contains_chinese(msgstr):
                        errors.append(f"[{loc}/{domain}] {msgid!r} has Chinese msgstr: {msgstr!r}")

        if errors:
            pytest.fail("Critical race/yao i18n entries contain Chinese in non-Chinese locales:\n" + "\n".join(errors))

