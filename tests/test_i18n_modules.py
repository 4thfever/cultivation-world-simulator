import os
from pathlib import Path
import pytest
import polib
from src.i18n import t, _get_locale_dir

def test_i18n_modules_structure():
    """
    Test that the i18n modules structure is correct.
    """
    locale_dir = _get_locale_dir()
    # Directory names now use hyphens (zh-CN) to match static assets convention
    languages = ["zh-CN", "en-US", "zh-TW"]
    
    for lang in languages:
        lang_dir = locale_dir / lang
        assert lang_dir.exists(), f"Language directory {lang} does not exist"
        
        modules_dir = lang_dir / "modules"
        assert modules_dir.exists(), f"Modules directory for {lang} does not exist"
        assert modules_dir.is_dir()
        
        # Check if there are .po files in modules
        po_files = list(modules_dir.glob("*.po"))
        assert len(po_files) > 0, f"No .po files found in {modules_dir}"
        
        # Check specific expected modules
        expected_modules = ["battle.po", "action.po", "fortune.po"]
        for mod in expected_modules:
            assert (modules_dir / mod).exists(), f"Expected module {mod} missing in {lang}"

def test_merged_messages_po_integrity():
    """
    Test that the merged messages.po file in LC_MESSAGES exists and contains entries from modules.
    """
    locale_dir = _get_locale_dir()
    lang = "zh-CN" # Test with one language (hyphen)
    
    lc_messages_dir = locale_dir / lang / "LC_MESSAGES"
    messages_po_path = lc_messages_dir / "messages.po"
    
    assert messages_po_path.exists(), "Merged messages.po does not exist"
    
    merged_po = polib.pofile(str(messages_po_path))
    assert len(merged_po) > 0, "Merged messages.po is empty"
    
    # Check a random key from a module (e.g., from battle.po)
    # We know "attack_action_name" should be in action.po or battle.po
    # Actually "attack_action_name" is in action.po
    
    found_attack = False
    for entry in merged_po:
        if entry.msgid == "attack_action_name":
            found_attack = True
            break
            
    assert found_attack, "Key 'attack_action_name' (from action.po) not found in merged messages.po"

def test_translation_loading():
    """
    Test that translations are actually loaded and working.
    """
    # This relies on the force_chinese_language fixture in conftest.py if run in full suite,
    # or we explicitly set it here.
    from src.classes.language import language_manager
    language_manager.set_language("zh-CN")
    
    # Test a known key
    # "attack_action_name" -> "发起战斗"
    assert t("attack_action_name") == "发起战斗"
    
    # Test a formatted string
    # "{winner} defeated {loser}" -> "{winner} 战胜了 {loser}"
    # Note: the translation might be different, let's check exact value from file or flexible match
    res = t("{winner} defeated {loser}", winner="A", loser="B")
    assert "战胜了" in res

def test_split_po_script_exists():
    """
    Ensure the maintenance scripts exist.
    """
    root = Path(__file__).parent.parent
    split_script = root / "tools" / "i18n" / "split_po.py"
    build_script = root / "tools" / "i18n" / "build_mo.py"
    
    assert split_script.exists()
    assert build_script.exists()
