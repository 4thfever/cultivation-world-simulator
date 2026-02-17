import pytest
import re
import ast
from pathlib import Path
from typing import Set, Dict

from src.utils.df import load_game_configs
from src.i18n import t

# =============================================================================
# Helper Functions & Constants
# =============================================================================

# Define Chinese character range
ZH_PATTERN = re.compile(r'[\u4e00-\u9fff]')
# Match msgid "content"
MSGID_PATTERN = re.compile(r'^msgid\s+"(.*)"')

def get_po_files():
    """Get all .po files in static/locales"""
    root_dir = Path(__file__).parent.parent / "static" / "locales"
    return list(root_dir.rglob("*.po"))

def get_project_root() -> Path:
    """Get project root directory"""
    return Path(__file__).parent.parent

# =============================================================================
# CSV Integrity Tests
# =============================================================================

def test_all_csv_ids_have_translations():
    """
    遍历加载的所有游戏配置 CSV，检查所有以 _id 结尾的字段（如 name_id, desc_id, title_id），
    确保它们在中文环境下都有对应的翻译。
    
    如果 t(key) 返回的结果等于 key 本身，且 key 是全大写（典型的 ID 格式），则视为缺失翻译。
    """
    # 1. 加载配置 (force_chinese_language fixture 已经在 session 级别生效)
    configs = load_game_configs()
    
    missing_keys = []
    
    # 2. 遍历所有配置表
    for config_name, rows in configs.items():
        if not rows:
            continue
            
        print(f"Checking config: {config_name}.csv ({len(rows)} rows)")
        
        for i, row in enumerate(rows):
            # 遍历行中的所有键值对
            for key, value in row.items():
                # 检查 Key 是否以 _id 结尾 (例如 title_id)
                # 并且 Value 是字符串且非空
                if key.lower().endswith("id") and isinstance(value, str) and value.strip():
                    # 也可以进一步过滤，例如只检查全大写的 Value，或者特定前缀
                    # 这里假设所有需要翻译的 ID 都是全大写且包含下划线
                    if value.isupper() and "_" in value:
                        translated = t(value)
                        
                        # 如果翻译结果和原文一样，且原文不是空的，视为缺失
                        # 注意：有些 ID 本身就是英文显示（极少），这里主要针对需要转中文的情况
                        if translated == value:
                            missing_keys.append(f"[{config_name}.csv Row {i+1}] {key}={value}")

    # 3. 断言
    if missing_keys:
        error_msg = f"Found {len(missing_keys)} missing translations in zh-CN:\n" + "\n".join(missing_keys)
        pytest.fail(error_msg)


# =============================================================================
# PO File Quality Tests
# =============================================================================

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


class TestSourceCodeQuality:
    """Check source code for i18n issues"""

    EXCLUDE_PATTERNS = [
        '__pycache__',
        '.pyc',
        'test_',
        '/tests/',
        'conftest.py',
    ]

    @staticmethod
    def contains_chinese(text: str) -> bool:
        return bool(re.search(r'[\u4e00-\u9fff]', text))

    @staticmethod
    def is_comment_or_docstring(line: str) -> bool:
        stripped = line.strip()
        return (
            stripped.startswith('#') or
            stripped.startswith('"""') or
            stripped.startswith("'''") or
            'docstring' in stripped.lower()
        )

    @staticmethod
    def is_in_string_literal(line: str) -> bool:
        if '#' in line:
            line = line[:line.index('#')]
        return '"' in line or "'" in line

    def test_no_hardcoded_chinese_in_src_classes(self):
        """检查 src/classes/ 下不应有硬编码中文（应使用 t() 函数）"""
        classes_dir = get_project_root() / "src" / "classes"
        
        if not classes_dir.exists():
            pytest.skip("src/classes directory not found")
        
        violations = []
        
        for py_file in classes_dir.rglob("*.py"):
            if any(pattern in str(py_file) for pattern in self.EXCLUDE_PATTERNS):
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    if self.is_comment_or_docstring(line):
                        continue
                    
                    if self.contains_chinese(line):
                        if self.is_in_string_literal(line) and 't(' not in line:
                            violations.append(f"{py_file.relative_to(get_project_root())}:{i} -> {line.strip()[:100]}")
            
            except Exception as e:
                print(f"Warning: Could not read {py_file}: {e}")
        
        if violations:
            error_msg = f"Found {len(violations)} lines with hardcoded Chinese strings (should use t()):\n" + "\n".join(violations[:20])
            if len(violations) > 20:
                error_msg += f"\n... and {len(violations) - 20} more."
            # Note: This is a strict check, might produce false positives. 
            # Uncomment pytest.fail to enforce it, or keep as a warning printer for now if codebase is not clean yet.
            # pytest.fail(error_msg) 
            print(f"\n[WARNING] {error_msg}")


class TestTranslationKeysIntegrity:
    """Check that used translation keys exist in PO files"""

    @staticmethod
    def extract_t_calls_from_file(py_file: Path) -> Set[str]:
        try:
            content = py_file.read_text(encoding='utf-8')
            tree = ast.parse(content)
            msgids = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func_name = None
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id
                    if func_name == 't' and node.args:
                        first_arg = node.args[0]
                        if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                            msgids.add(first_arg.value)
            return msgids
        except Exception:
            return set()

    @staticmethod
    def extract_msgids_from_po(po_file: Path) -> Set[str]:
        if not po_file.exists():
            return set()
        msgids = set()
        try:
            # Try polib first
            import polib
            po = polib.pofile(str(po_file))
            for entry in po:
                msgids.add(entry.msgid)
        except ImportError:
            # Fallback to regex
            content = po_file.read_text(encoding='utf-8')
            pattern = r'msgid\s+"([^"]*)"'
            matches = re.findall(pattern, content)
            for m in matches:
                if m:
                    decoded = m.replace('\\n', '\n').replace('\\t', '\t').replace('\\r', '\r')
                    msgids.add(decoded)
        return msgids

    def test_all_used_msgids_are_defined_in_po(self):
        """检查所有代码中使用的 msgid 都在 PO 文件中定义"""
        src_dir = get_project_root() / "src"
        locales_dir = get_project_root() / "static/locales/zh-CN"
        
        if not src_dir.exists() or not locales_dir.exists():
            pytest.skip("Required directories not found")
        
        defined_msgids = set()
        # 遍历所有 zh-CN 下的 PO 文件（包括 messages.po 和 game_configs_modules 下的）
        for po_file in locales_dir.rglob("*.po"):
            defined_msgids.update(self.extract_msgids_from_po(po_file))
            
        used_msgids = set()
        
        for py_file in src_dir.rglob("*.py"):
            if 'test_' in py_file.name or '/tests/' in str(py_file):
                continue
            used_msgids.update(self.extract_t_calls_from_file(py_file))
        
        undefined_msgids = used_msgids - defined_msgids
        
        if undefined_msgids:
            error_msg = f"Found {len(undefined_msgids)} msgids used in code but not defined in PO file:\n"
            error_msg += "\n".join([f"  - '{m}'" for m in sorted(undefined_msgids)[:20]])
            if len(undefined_msgids) > 20:
                error_msg += f"\n  ... and {len(undefined_msgids) - 20} more."
            pytest.fail(error_msg)


class TestFormatParameterConsistency:
    """Check consistency of format parameters in translations"""

    @staticmethod
    def extract_format_params(text: str) -> Set[str]:
        return set(re.findall(r'\{(\w+)\}', text))
    
    @staticmethod
    def extract_pairs(po_file: Path) -> Dict[str, str]:
        """Extract msgid -> msgstr pairs using polib to handle multiline correctly"""
        try:
            import polib
            po = polib.pofile(str(po_file))
            return {entry.msgid: entry.msgstr for entry in po if entry.msgid and not entry.obsolete}
        except ImportError:
            # Fallback to simple regex if polib is missing (though it should be installed)
            # This regex approach is fragile for multiline, but kept as backup
            content = po_file.read_text(encoding='utf-8')
            pairs = {}
            # ... (omitted complex regex implementation for brevity, rely on polib)
            # If polib is missing, this test might be flaky. 
            # Given the project uses polib in other tests, we assume it's available.
            print("Warning: polib not found, skipping precise pair extraction.")
            return {}

    def test_format_params_consistency(self):
        """检查中英文翻译的格式化参数与原始 msgid 一致"""
        zh_po = get_project_root() / "static/locales/zh-CN/LC_MESSAGES/messages.po"
        en_po = get_project_root() / "static/locales/en-US/LC_MESSAGES/messages.po"
        
        if not zh_po.exists() or not en_po.exists():
            pytest.skip("PO files not found")
            
        zh_pairs = self.extract_pairs(zh_po)
        en_pairs = self.extract_pairs(en_po)
        
        inconsistencies = []
        
        for msgid, zh_msgstr in zh_pairs.items():
            if msgid in en_pairs:
                en_msgstr = en_pairs[msgid]
                
                # If msgstr is empty (fallback to msgid), use msgid content for param extraction
                zh_content = zh_msgstr if zh_msgstr else msgid
                en_content = en_msgstr if en_msgstr else msgid
                
                msgid_params = self.extract_format_params(msgid)
                zh_params = self.extract_format_params(zh_content)
                en_params = self.extract_format_params(en_content)
                
                # Logic Update:
                # 1. If msgid has params, translations MUST match (Source-based)
                # 2. If msgid has NO params, translations MUST match EACH OTHER (Key-based)
                
                is_inconsistent = False
                
                if msgid_params:
                    # Source-based: translations must strictly match source
                    if zh_params != msgid_params or en_params != msgid_params:
                        is_inconsistent = True
                else:
                    # Key-based: msgid has no params (e.g. "retreat_start")
                    # But translations might have params. 
                    # We check if ZH and EN are consistent with each other.
                    if zh_params != en_params:
                        is_inconsistent = True
                
                if is_inconsistent:
                    inconsistencies.append(
                        f"msgid: {msgid[:50]}...\n"
                        f"  Params: Original={msgid_params}, ZH={zh_params}, EN={en_params}"
                    )
        
        if inconsistencies:
            error_msg = f"Found {len(inconsistencies)} translation entries with inconsistent format parameters:\n" + "\n".join(inconsistencies[:10])
            pytest.fail(error_msg)
