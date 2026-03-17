#!/usr/bin/env python3
"""Clean low-risk PO comment noise while preserving entry content."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.i18n.locale_registry import get_locale_codes


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--locales",
        help="Comma-separated locale codes to process. Defaults to all enabled locales.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Actually write changes back to disk. Default is dry-run.",
    )
    return parser


def iter_target_files(locales: list[str]) -> list[Path]:
    files: list[Path] = []
    for locale in locales:
        locale_root = PROJECT_ROOT / "static" / "locales" / locale
        for subdir in ("modules", "game_configs_modules"):
            target_dir = locale_root / subdir
            if not target_dir.exists():
                continue
            files.extend(sorted(target_dir.glob("*.po")))
    return files


def collapse_comments(lines: list[str]) -> tuple[list[str], int, int]:
    output: list[str] = []
    collapsed_separator_blocks = 0
    removed_empty_extracted_comments = 0
    index = 0

    while index < len(lines):
        line = lines[index]
        if (
            index + 2 < len(lines)
            and lines[index].startswith("#")
            and set(lines[index].replace("#", "").strip()) == {"="}
            and lines[index + 1].startswith("# ")
            and lines[index + 2].startswith("#")
            and set(lines[index + 2].replace("#", "").strip()) == {"="}
        ):
            output.append(lines[index + 1])
            collapsed_separator_blocks += 1
            index += 3
            continue

        if line.startswith("#.") and ":" in line and line.split(":", 1)[1].strip() == "":
            removed_empty_extracted_comments += 1
            index += 1
            continue

        output.append(line)
        index += 1

    return output, collapsed_separator_blocks, removed_empty_extracted_comments


def main() -> int:
    args = build_parser().parse_args()
    locales = (
        [item.strip() for item in args.locales.split(",") if item.strip()]
        if args.locales
        else get_locale_codes()
    )

    changed_files = 0
    separator_blocks = 0
    empty_extracted_comments = 0

    for path in iter_target_files(locales):
        original = path.read_text(encoding="utf-8")
        lines = original.splitlines()
        rewritten_lines, collapsed, removed_empty = collapse_comments(lines)
        rewritten = "\n".join(rewritten_lines) + "\n"

        if rewritten == original:
            continue

        changed_files += 1
        separator_blocks += collapsed
        empty_extracted_comments += removed_empty
        print(f"{'WRITE' if args.write else 'DRY-RUN'} {path.relative_to(PROJECT_ROOT)}")

        if args.write:
            path.write_text(rewritten, encoding="utf-8")

    print(
        "Summary:",
        {
            "changed_files": changed_files,
            "separator_blocks": separator_blocks,
            "empty_extracted_comments": empty_extracted_comments,
            "mode": "write" if args.write else "dry-run",
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
