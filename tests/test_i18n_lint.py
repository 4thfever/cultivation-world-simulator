import re
import pytest
from pathlib import Path

# Define Chinese character range
ZH_PATTERN = re.compile(r'[\u4e00-\u9fff]')
# Match msgid "content"
MSGID_PATTERN = re.compile(r'^msgid\s+"(.*)"')

def get_po_files():
    """Get all .po files in static/locales"""
    root_dir = Path(__file__).parent.parent / "static" / "locales"
    return list(root_dir.rglob("*.po"))

@pytest.mark.parametrize("po_file", get_po_files())
def test_msgid_should_not_contain_chinese(po_file):
    """
    Ensure msgid in .po files does not contain Chinese characters.
    Convention: msgid should be English source text, msgstr is the translation.
    """
    errors = []
    
    try:
        with open(po_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                match = MSGID_PATTERN.match(line)
                if match:
                    content = match.group(1)
                    if ZH_PATTERN.search(content):
                        errors.append(f"Line {line_num}: {content}")
    except FileNotFoundError:
        pytest.skip(f"File not found: {po_file}")
    
    error_msg = "\n".join(errors)
    assert not errors, f"Found Chinese characters in msgid in {po_file}:\n{error_msg}"
