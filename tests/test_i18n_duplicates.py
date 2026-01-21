#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试 i18n po 文件中是否有重复的 msgid

注意：此测试独立于 conftest.py，可以单独运行
使用方法：python tests/test_i18n_duplicates.py
"""

import re
import sys
from pathlib import Path
from collections import Counter

# 不导入 pytest，避免触发 conftest.py
# 使用标准库实现简单的测试


def extract_msgids(filepath: Path) -> list[str]:
    """从 po 文件中提取所有 msgid"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 匹配 msgid "..." 模式
    pattern = r'msgid\s+"([^"]*)"'
    matches = re.findall(pattern, content)
    
    # 过滤掉空字符串（文件头的 msgid ""）
    msgids = [m for m in matches if m]
    
    return msgids


def find_duplicates(msgids: list[str]) -> dict[str, int]:
    """找出重复的 msgid"""
    counter = Counter(msgids)
    duplicates = {msgid: count for msgid, count in counter.items() if count > 1}
    return duplicates


def get_po_file_path(lang: str) -> Path:
    """获取指定语言的 po 文件路径"""
    project_root = Path(__file__).parent.parent
    po_file = project_root / "src" / "i18n" / "locales" / lang / "LC_MESSAGES" / "messages.po"
    return po_file


def test_zh_cn_no_duplicates() -> bool:
    """测试中文 po 文件没有重复的 msgid"""
    po_file = get_po_file_path("zh_CN")
    
    if not po_file.exists():
        print(f"[FAIL] 中文 po 文件不存在: {po_file}")
        return False
    
    msgids = extract_msgids(po_file)
    duplicates = find_duplicates(msgids)
    
    if duplicates:
        print(f"[FAIL] 中文 po 文件中发现 {len(duplicates)} 个重复的 msgid:")
        for msgid, count in sorted(duplicates.items()):
            print(f"  - '{msgid}' 出现了 {count} 次")
        return False
    
    print(f"[PASS] 中文 po 文件没有重复的 msgid (共 {len(msgids)} 个)")
    return True


def test_en_us_no_duplicates() -> bool:
    """测试英文 po 文件没有重复的 msgid"""
    po_file = get_po_file_path("en_US")
    
    if not po_file.exists():
        print(f"[FAIL] 英文 po 文件不存在: {po_file}")
        return False
    
    msgids = extract_msgids(po_file)
    duplicates = find_duplicates(msgids)
    
    if duplicates:
        print(f"[FAIL] 英文 po 文件中发现 {len(duplicates)} 个重复的 msgid:")
        for msgid, count in sorted(duplicates.items()):
            print(f"  - '{msgid}' 出现了 {count} 次")
        return False
    
    print(f"[PASS] 英文 po 文件没有重复的 msgid (共 {len(msgids)} 个)")
    return True


def test_msgid_count_consistency() -> bool:
    """测试中英文 po 文件的 msgid 数量一致"""
    zh_file = get_po_file_path("zh_CN")
    en_file = get_po_file_path("en_US")
    
    zh_msgids = extract_msgids(zh_file)
    en_msgids = extract_msgids(en_file)
    
    if len(zh_msgids) != len(en_msgids):
        print(f"[FAIL] 中英文 po 文件的 msgid 数量不一致: "
              f"中文 {len(zh_msgids)} 个, 英文 {len(en_msgids)} 个")
        return False
    
    print(f"[PASS] 中英文 po 文件的 msgid 数量一致: {len(zh_msgids)} 个")
    return True


def test_msgid_keys_match() -> bool:
    """测试中英文 po 文件的 msgid 键完全匹配"""
    zh_file = get_po_file_path("zh_CN")
    en_file = get_po_file_path("en_US")
    
    zh_msgids = set(extract_msgids(zh_file))
    en_msgids = set(extract_msgids(en_file))
    
    # 找出只在中文中存在的 msgid
    zh_only = zh_msgids - en_msgids
    # 找出只在英文中存在的 msgid
    en_only = en_msgids - zh_msgids
    
    if zh_only or en_only:
        print(f"[FAIL] 中英文 po 文件的 msgid 键不完全匹配")
        
        if zh_only:
            print(f"  只在中文中存在的 msgid ({len(zh_only)} 个):")
            for msgid in sorted(zh_only)[:3]:
                print(f"    - '{msgid}'")
            if len(zh_only) > 3:
                print(f"    ... 还有 {len(zh_only) - 3} 个")
        
        if en_only:
            print(f"  只在英文中存在的 msgid ({len(en_only)} 个):")
            for msgid in sorted(en_only)[:3]:
                print(f"    - '{msgid}'")
            if len(en_only) > 3:
                print(f"    ... 还有 {len(en_only) - 3} 个")
        
        return False
    
    print(f"[PASS] 中英文 po 文件的 msgid 键完全匹配")
    return True


def main():
    """运行所有测试"""
    print("="*60)
    print("i18n PO 文件重复项检查")
    print("="*60)
    
    tests = [
        ("检查中文 po 文件没有重复", test_zh_cn_no_duplicates),
        ("检查英文 po 文件没有重复", test_en_us_no_duplicates),
        ("检查中英文 msgid 数量一致", test_msgid_count_consistency),
        ("检查中英文 msgid 键完全匹配", test_msgid_keys_match),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}...")
        passed = test_func()
        results.append(passed)
    
    print("\n" + "="*60)
    passed_count = sum(results)
    total_count = len(results)
    
    if all(results):
        print(f"[OK] 所有测试通过 ({passed_count}/{total_count})")
        return 0
    else:
        print(f"[FAIL] 部分测试失败 ({passed_count}/{total_count})")
        return 1


if __name__ == "__main__":
    sys.exit(main())
