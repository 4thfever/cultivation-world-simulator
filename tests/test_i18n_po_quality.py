#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试 PO 文件质量和代码中翻译键的使用

此测试独立于 conftest.py，专注于静态分析：
1. 检查代码中是否有硬编码的中文字符串
2. 检查代码中使用的翻译键是否都在 PO 文件中定义
3. 检查格式化参数的一致性
"""

import re
import ast
import sys
from pathlib import Path
from typing import Set


class TestHardcodedChineseStrings:
    """检查源代码中是否有硬编码的中文字符串"""
    
    # 排除的文件模式
    EXCLUDE_PATTERNS = [
        '__pycache__',
        '.pyc',
        'test_',  # 测试文件可以有中文
        '/tests/',
        'conftest.py',
    ]
    
    @staticmethod
    def contains_chinese(text: str) -> bool:
        """检查字符串是否包含中文字符"""
        return bool(re.search(r'[\u4e00-\u9fff]', text))
    
    @staticmethod
    def is_comment_or_docstring(line: str) -> bool:
        """检查是否是注释或文档字符串"""
        stripped = line.strip()
        return (
            stripped.startswith('#') or
            stripped.startswith('"""') or
            stripped.startswith("'''") or
            'docstring' in stripped.lower()
        )
    
    @staticmethod
    def is_in_string_literal(line: str) -> bool:
        """简单检查行中是否包含字符串字面量（引号）"""
        # 移除注释部分
        if '#' in line:
            line = line[:line.index('#')]
        return '"' in line or "'" in line
    
    def test_no_hardcoded_chinese_in_src_classes(self):
        """检查 src/classes/ 下不应有硬编码中文（应使用 t() 函数）"""
        classes_dir = Path("src/classes")
        
        if not classes_dir.exists():
            print("SKIP: src/classes directory not found")
            return
        
        violations = []
        
        for py_file in classes_dir.rglob("*.py"):
            # 跳过排除的文件
            if any(pattern in str(py_file) for pattern in self.EXCLUDE_PATTERNS):
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    # 跳过注释和文档字符串
                    if self.is_comment_or_docstring(line):
                        continue
                    
                    # 检查是否包含中文
                    if self.contains_chinese(line):
                        # 如果在字符串中且不是 t() 调用，可能有问题
                        if self.is_in_string_literal(line) and 't(' not in line:
                            violations.append({
                                'file': str(py_file.relative_to('src')),
                                'line': i,
                                'content': line.strip()[:100]
                            })
            
            except Exception as e:
                print(f"Warning: Could not read {py_file}: {e}")
        
        if violations:
            print("\n" + "="*60)
            print("警告：发现可能的硬编码中文字符串（应使用 t() 函数）:")
            print("="*60)
            for v in violations[:20]:  # 显示前20个
                print(f"  {v['file']}:{v['line']}")
                print(f"    {v['content']}")
            if len(violations) > 20:
                print(f"  ... 还有 {len(violations) - 20} 个")
            print("\n注意：这可能包括误报，请手动检查")


class TestTranslationKeysDefinition:
    """检查代码中使用的翻译键是否都在 PO 文件中定义"""
    
    @staticmethod
    def extract_t_calls_from_file(py_file: Path) -> Set[str]:
        """从 Python 文件中提取所有 t() 函数调用的 msgid"""
        try:
            content = py_file.read_text(encoding='utf-8')
            tree = ast.parse(content)
            
            msgids = set()
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # 检查是否是 t() 调用
                    func_name = None
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id
                    
                    if func_name == 't' and node.args:
                        first_arg = node.args[0]
                        if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                            msgids.add(first_arg.value)
            
            return msgids
        
        except SyntaxError as e:
            print(f"Warning: Syntax error in {py_file}: {e}")
            return set()
        except Exception as e:
            print(f"Warning: Could not parse {py_file}: {e}")
            return set()
    
    @staticmethod
    def extract_msgids_from_po(po_file: Path) -> Set[str]:
        """从 PO 文件中提取所有定义的 msgid"""
        if not po_file.exists():
            return set()
        
        msgids = set()
        try:
            content = po_file.read_text(encoding='utf-8')
            pattern = r'msgid\s+"([^"]*)"'
            matches = re.findall(pattern, content)
            # 手动处理常见的转义序列
            for m in matches:
                if m:  # 排除空字符串
                    # 只替换常见的转义序列，保留Unicode字符
                    decoded = m.replace('\\n', '\n').replace('\\t', '\t').replace('\\r', '\r')
                    msgids.add(decoded)
        except Exception as e:
            print(f"Warning: Could not read {po_file}: {e}")
        
        return msgids
    
    def test_all_used_msgids_are_defined_in_po(self):
        """检查所有代码中使用的 msgid 都在 PO 文件中定义"""
        src_dir = Path("src")
        po_file = Path("src/i18n/locales/zh_CN/LC_MESSAGES/messages.po")
        
        if not src_dir.exists() or not po_file.exists():
            print("SKIP: Required directories not found")
            return
        
        # 提取 PO 文件中定义的所有 msgid
        defined_msgids = self.extract_msgids_from_po(po_file)
        print(f"\nPO 文件中定义了 {len(defined_msgids)} 个 msgid")
        
        # 提取代码中使用的所有 msgid
        used_msgids = set()
        python_files = list(src_dir.rglob("*.py"))
        
        for py_file in python_files:
            # 跳过测试文件
            if 'test_' in py_file.name or '/tests/' in str(py_file):
                continue
            
            file_msgids = self.extract_t_calls_from_file(py_file)
            used_msgids.update(file_msgids)
        
        print(f"代码中使用了 {len(used_msgids)} 个唯一的 msgid")
        
        # 找出未定义的 msgid
        undefined_msgids = used_msgids - defined_msgids
        
        if undefined_msgids:
            print("\n" + "="*60)
            print(f"错误：发现 {len(undefined_msgids)} 个未在 PO 文件中定义的 msgid:")
            print("="*60)
            for msgid in sorted(undefined_msgids)[:20]:
                print(f"  - '{msgid}'")
            if len(undefined_msgids) > 20:
                print(f"  ... 还有 {len(undefined_msgids) - 20} 个")
            print("\n这些翻译键需要添加到 PO 文件中")
            sys.exit(1)
        else:
            print("[OK] 所有使用的 msgid 都已在 PO 文件中定义")


class TestFormatParameterConsistency:
    """检查格式化参数在 msgid 和 msgstr 中的一致性"""
    
    @staticmethod
    def extract_format_params(text: str) -> Set[str]:
        """提取字符串中的所有格式化参数 {param}"""
        return set(re.findall(r'\{(\w+)\}', text))
    
    def test_format_params_consistency(self):
        """检查中英文翻译的格式化参数与原始 msgid 一致"""
        zh_po = Path("src/i18n/locales/zh_CN/LC_MESSAGES/messages.po")
        en_po = Path("src/i18n/locales/en_US/LC_MESSAGES/messages.po")
        
        if not zh_po.exists() or not en_po.exists():
            print("SKIP: PO files not found")
            return
        
        def extract_pairs(po_file):
            """提取 msgid -> msgstr 映射"""
            content = po_file.read_text(encoding='utf-8')
            pairs = {}
            
            lines = content.split('\n')
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                if line.startswith('msgid "') and line != 'msgid ""':
                    msgid = line[7:-1]
                    
                    # 查找对应的 msgstr
                    i += 1
                    while i < len(lines) and not lines[i].strip().startswith('msgstr '):
                        i += 1
                    
                    if i < len(lines):
                        msgstr_line = lines[i].strip()
                        if msgstr_line.startswith('msgstr "'):
                            msgstr = msgstr_line[8:-1]
                            pairs[msgid] = msgstr
                i += 1
            
            return pairs
        
        zh_pairs = extract_pairs(zh_po)
        en_pairs = extract_pairs(en_po)
        
        print(f"\n检查 {len(zh_pairs)} 个翻译条目的格式化参数一致性...")
        
        inconsistencies = []
        
        for msgid, zh_msgstr in zh_pairs.items():
            if msgid in en_pairs:
                en_msgstr = en_pairs[msgid]
                
                # 提取参数
                msgid_params = self.extract_format_params(msgid)
                zh_params = self.extract_format_params(zh_msgstr)
                en_params = self.extract_format_params(en_msgstr)
                
                # 检查一致性
                if zh_params != msgid_params or en_params != msgid_params:
                    inconsistencies.append({
                        'msgid': msgid,
                        'msgid_params': msgid_params,
                        'zh_params': zh_params,
                        'en_params': en_params
                    })
        
        if inconsistencies:
            print("\n" + "="*60)
            print(f"警告：发现 {len(inconsistencies)} 个格式化参数不一致的条目:")
            print("="*60)
            for item in inconsistencies[:10]:
                print(f"\nmsgid: {item['msgid'][:60]}...")
                print(f"  原始参数: {item['msgid_params']}")
                print(f"  中文参数: {item['zh_params']}")
                print(f"  英文参数: {item['en_params']}")
            if len(inconsistencies) > 10:
                print(f"\n  ... 还有 {len(inconsistencies) - 10} 个")
        else:
            print("[OK] 所有翻译的格式化参数都一致")


def main():
    """运行所有测试"""
    print("="*60)
    print("PO 文件质量和翻译键使用检查")
    print("="*60)
    
    tests = [
        ("检查硬编码中文字符串", TestHardcodedChineseStrings().test_no_hardcoded_chinese_in_src_classes),
        ("检查翻译键定义", TestTranslationKeysDefinition().test_all_used_msgids_are_defined_in_po),
        ("检查格式化参数一致性", TestFormatParameterConsistency().test_format_params_consistency),
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"测试: {test_name}")
        print(f"{'='*60}")
        try:
            test_func()
        except Exception as e:
            print(f"测试失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


if __name__ == "__main__":
    main()
