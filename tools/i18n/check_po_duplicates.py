#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查 po 文件中是否有重复的 msgid"""

import re
import sys
from pathlib import Path
from collections import Counter


def extract_msgids(filepath: Path) -> list[str]:
    """
    从 po 文件中提取所有 msgid
    
    Args:
        filepath: po 文件路径
        
    Returns:
        msgid 列表（不包含空字符串）
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 匹配 msgid "..." 模式
    pattern = r'msgid\s+"([^"]*)"'
    matches = re.findall(pattern, content)
    
    # 过滤掉空字符串（文件头的 msgid ""）
    msgids = [m for m in matches if m]
    
    return msgids


def find_duplicates(msgids: list[str]) -> dict[str, int]:
    """
    找出重复的 msgid
    
    Args:
        msgids: msgid 列表
        
    Returns:
        字典，键为重复的 msgid，值为出现次数
    """
    counter = Counter(msgids)
    duplicates = {msgid: count for msgid, count in counter.items() if count > 1}
    return duplicates


def check_file(filepath: Path, lang_name: str) -> tuple[int, dict[str, int]]:
    """
    检查单个 po 文件
    
    Args:
        filepath: po 文件路径
        lang_name: 语言名称（用于显示）
        
    Returns:
        (msgid总数, 重复项字典)
    """
    print(f"\n{'='*60}")
    print(f"检查文件: {lang_name}")
    print(f"路径: {filepath}")
    print(f"{'='*60}")
    
    if not filepath.exists():
        print(f"[ERROR] 文件不存在")
        return 0, {}
    
    msgids = extract_msgids(filepath)
    print(f"总共找到 {len(msgids)} 个 msgid 条目")
    
    duplicates = find_duplicates(msgids)
    
    if duplicates:
        print(f"\n[WARNING] 发现 {len(duplicates)} 个重复的 msgid:")
        for msgid, count in sorted(duplicates.items()):
            print(f"  - '{msgid}' 出现了 {count} 次")
    else:
        print(f"\n[OK] 未发现重复的 msgid")
    
    return len(msgids), duplicates


def main():
    """主函数"""
    # 获取项目根目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    
    # po 文件路径
    zh_file = project_root / "static" / "locales" / "zh-CN" / "LC_MESSAGES" / "messages.po"
    en_file = project_root / "static" / "locales" / "en-US" / "LC_MESSAGES" / "messages.po"
    
    # 检查中文文件
    zh_count, zh_dups = check_file(zh_file, "中文 (zh_CN)")
    
    # 检查英文文件
    en_count, en_dups = check_file(en_file, "英文 (en_US)")
    
    # 打印总结
    print(f"\n{'='*60}")
    print("检查总结")
    print(f"{'='*60}")
    
    has_error = False
    
    if zh_dups or en_dups:
        print("[ERROR] 发现重复条目，需要修复")
        has_error = True
    else:
        print("[OK] 两个文件都没有重复的 msgid")
    
    if zh_count != en_count:
        print(f"[WARNING] 中英文 msgid 数量不一致: 中文 {zh_count} 个, 英文 {en_count} 个")
        has_error = True
    else:
        print(f"[OK] 中英文 msgid 数量一致: {zh_count} 个")
    
    # 检查 msgid 键是否匹配
    if zh_count > 0 and en_count > 0:
        zh_msgids = set(extract_msgids(zh_file))
        en_msgids = set(extract_msgids(en_file))
        
        zh_only = zh_msgids - en_msgids
        en_only = en_msgids - zh_msgids
        
        if zh_only:
            print(f"\n[WARNING] 只在中文中存在的 msgid ({len(zh_only)} 个):")
            for msgid in sorted(zh_only)[:5]:
                print(f"  - '{msgid}'")
            if len(zh_only) > 5:
                print(f"  ... 还有 {len(zh_only) - 5} 个")
            has_error = True
        
        if en_only:
            print(f"\n[WARNING] 只在英文中存在的 msgid ({len(en_only)} 个):")
            for msgid in sorted(en_only)[:5]:
                print(f"  - '{msgid}'")
            if len(en_only) > 5:
                print(f"  ... 还有 {len(en_only) - 5} 个")
            has_error = True
        
        if not zh_only and not en_only:
            print("[OK] 中英文 msgid 键完全匹配")
    
    # 返回状态码
    return 1 if has_error else 0


if __name__ == "__main__":
    sys.exit(main())
