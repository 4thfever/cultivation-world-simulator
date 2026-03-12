#!/usr/bin/env python3
"""扫描所有 .py 文件，检查编码污染：BOM、非 UTF-8、声明不一致、可疑 Unicode 等。"""
from pathlib import Path
import re
import sys

# 可疑字符：BOM、零宽字符、替换字符、BOM 随附字符等
SUSPICIOUS_UNICODE = [
    ("BOM", "\ufeff"),
    ("ZERO WIDTH SPACE", "\u200b"),
    ("ZERO WIDTH NO-BREAK SPACE", "\u2060"),  # 实际是 WORD JOINER
]
WORD_JOINER = "\u2060"
REPLACEMENT_CHAR = "\ufffd"
ZERO_WIDTH = re.compile(r"[\u200b\u200c\u200d\u2060\ufeff]")


def check_file(path: Path) -> list[str]:
    issues = []
    raw = path.read_bytes()

    # 1. BOM 检测
    if raw.startswith(b"\xef\xbb\xbf"):
        issues.append("含 UTF-8 BOM（建议移除）")

    # 去掉 BOM 再解码，便于后续检查
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        issues.append(f"非 UTF-8 或含非法字节: {e}")
        return issues

    lines = text.splitlines()
    if not lines:
        return issues

    # 2. 编码声明检查（仅看前两行）
    coding_re = re.compile(r"#\s*-\*-\s*coding\s*[:=]\s*([\w\-]+)\s*-\*-")
    declared_encoding = None
    for line in lines[:2]:
        m = coding_re.search(line)
        if m:
            declared_encoding = m.group(1).strip().lower()
            if declared_encoding not in ("utf-8", "utf8"):
                issues.append(f"声明编码为 {declared_encoding}（非 utf-8）")
            break

    # 3. 可疑 Unicode 字符
    for i, line in enumerate(lines, 1):
        if REPLACEMENT_CHAR in line:
            issues.append(f"第 {i} 行含替换字符 U+FFFD")
        if WORD_JOINER in line:
            issues.append(f"第 {i} 行含零宽不换行空格 U+2060")
        if "\u200b" in line or "\u200c" in line or "\u200d" in line:
            issues.append(f"第 {i} 行含零宽字符")
        if "\ufeff" in line and not (i == 1 and line.startswith("\ufeff")):
            issues.append(f"第 {i} 行内含有 BOM 字符")

    # 4. 混合行尾（可选，仅提示）
    if b"\r\n" in raw and b"\n" in raw and raw.count(b"\r\n") < raw.count(b"\n"):
        issues.append("混合行尾 (CRLF 与 LF)")

    return issues


def main():
    root = Path(__file__).resolve().parent.parent
    py_files = sorted(root.rglob("*.py"))
    # 排除 venv / .venv 等
    py_files = [p for p in py_files if ".venv" not in p.parts and "venv" not in p.parts]
    total = 0
    with_issues = 0
    for path in py_files:
        total += 1
        issues = check_file(path)
        if issues:
            with_issues += 1
            rel = path.relative_to(root)
            print(f"{rel}")
            for i in issues:
                print(f"  - {i}")
            print()
    print(f"扫描 {total} 个 .py 文件，{with_issues} 个存在编码相关问题。")
    return 1 if with_issues else 0


if __name__ == "__main__":
    sys.exit(main())
