import sys
import pytest
from pathlib import Path
import polib

# Ensure project root is in sys.path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import the module under test
try:
    from tools.i18n.build_mo import compile_domain_modules, process_language
except ImportError:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "build_mo", 
        project_root / "tools/i18n/build_mo.py"
    )
    build_mo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build_mo)
    compile_domain_modules = build_mo.compile_domain_modules
    process_language = build_mo.process_language

@pytest.fixture
def temp_lang_dir(tmp_path):
    """Create a temporary language directory structure."""
    lang_dir = tmp_path / "zh-CN"
    lang_dir.mkdir()
    return lang_dir

def create_po_file(path, entries):
    """Helper to create a PO file with given entries."""
    po = polib.POFile()
    po.metadata = {
        'Content-Type': 'text/plain; charset=UTF-8',
    }
    for msgid, msgstr in entries.items():
        entry = polib.POEntry(
            msgid=msgid,
            msgstr=msgstr
        )
        po.append(entry)
    po.save(str(path))

def test_compile_domain_modules_merge(temp_lang_dir):
    """Test merging multiple PO files from a module directory."""
    # Setup modules
    modules_dir = temp_lang_dir / "game_configs_modules"
    modules_dir.mkdir()
    
    create_po_file(modules_dir / "part1.po", {"Item A": "物品A"})
    create_po_file(modules_dir / "part2.po", {"Item B": "物品B"})
    
    # Run merge
    result = compile_domain_modules(temp_lang_dir, "game_configs_modules", "game_configs")
    
    assert result is True
    
    # Verify PO output
    target_po = temp_lang_dir / "LC_MESSAGES" / "game_configs.po"
    assert target_po.exists()
    
    po = polib.pofile(str(target_po))
    entries = {e.msgid: e.msgstr for e in po}
    assert "Item A" in entries
    assert entries["Item A"] == "物品A"
    assert "Item B" in entries
    assert entries["Item B"] == "物品B"
    
    # Verify MO output
    target_mo = temp_lang_dir / "LC_MESSAGES" / "game_configs.mo"
    assert target_mo.exists()

def test_compile_domain_modules_no_modules(temp_lang_dir):
    """Test behavior when module directory is missing but target PO exists (legacy mode)."""
    lc_messages_dir = temp_lang_dir / "LC_MESSAGES"
    lc_messages_dir.mkdir()
    
    # Create an existing target PO
    create_po_file(lc_messages_dir / "game_configs.po", {"Legacy Item": "旧物品"})
    
    # Run merge (pointing to non-existent modules dir)
    result = compile_domain_modules(temp_lang_dir, "non_existent_modules", "game_configs")
    
    assert result is True
    
    # Verify MO was compiled from the existing PO
    target_mo = lc_messages_dir / "game_configs.mo"
    assert target_mo.exists()

def test_process_language_integration(temp_lang_dir):
    """Test the full process_language function."""
    # Setup modules for messages
    modules_dir = temp_lang_dir / "modules"
    modules_dir.mkdir()
    create_po_file(modules_dir / "battle.po", {"Battle Start": "战斗开始"})
    
    # Setup modules for game_configs
    configs_dir = temp_lang_dir / "game_configs_modules"
    configs_dir.mkdir()
    create_po_file(configs_dir / "items.po", {"Sword": "剑"})
    
    # Setup standalone PO
    lc_messages_dir = temp_lang_dir / "LC_MESSAGES"
    lc_messages_dir.mkdir(parents=True, exist_ok=True)
    create_po_file(lc_messages_dir / "standalone.po", {"Hello": "你好"})
    
    # Run process
    result = process_language(temp_lang_dir)
    
    assert result is True
    
    # Check messages.mo
    assert (lc_messages_dir / "messages.po").exists()
    assert (lc_messages_dir / "messages.mo").exists()
    
    # Check game_configs.mo
    assert (lc_messages_dir / "game_configs.po").exists()
    assert (lc_messages_dir / "game_configs.mo").exists()
    
    # Check standalone.mo
    assert (lc_messages_dir / "standalone.mo").exists()
