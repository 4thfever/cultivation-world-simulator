#!/usr/bin/env python3
"""Preview low-risk PO comment cleanup opportunities."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.i18n.locale_registry import get_locale_codes

SEPARATOR_RE = re.compile(r"^#\s*=+\s*$")
EXTRACTED_EMPTY_RE = re.compile(r"^#\.\s+[^:]+:\s*$")
EXTRACTED_RE = re.compile(r"^#\.\s+([^:]+):\s*(.*)$")


@dataclass
class FilePreview:
    path: str
    collapsed_separator_blocks: int
    removed_empty_extracted_comments: int
    suspicious_short_extracted_comments: list[str]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--locales",
        help="Comma-separated locale codes to scan. Defaults to all enabled locales.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "tmp" / "i18n_cleanup_preview.json",
        help="Where to write the JSON preview report.",
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


def preview_file(path: Path) -> FilePreview:
    lines = path.read_text(encoding="utf-8").splitlines()
    collapsed = 0
    removed_empty = 0
    suspicious: list[str] = []

    index = 0
    while index < len(lines):
        line = lines[index]
        if (
            index + 2 < len(lines)
            and SEPARATOR_RE.match(lines[index])
            and lines[index + 1].startswith("# ")
            and SEPARATOR_RE.match(lines[index + 2])
        ):
            collapsed += 1
            index += 3
            continue

        if EXTRACTED_EMPTY_RE.match(line):
            removed_empty += 1
            index += 1
            continue

        match = EXTRACTED_RE.match(line)
        if match:
            content = match.group(2).strip()
            # Preview only: short source echoes are often low-value, but keep manual review.
            if content and len(content) <= 4 and content not in suspicious:
                suspicious.append(content)

        index += 1

    return FilePreview(
        path=str(path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        collapsed_separator_blocks=collapsed,
        removed_empty_extracted_comments=removed_empty,
        suspicious_short_extracted_comments=suspicious[:20],
    )


def main() -> int:
    args = build_parser().parse_args()
    locales = (
        [item.strip() for item in args.locales.split(",") if item.strip()]
        if args.locales
        else get_locale_codes()
    )
    previews = [preview_file(path) for path in iter_target_files(locales)]
    previews = [
        item
        for item in previews
        if item.collapsed_separator_blocks
        or item.removed_empty_extracted_comments
        or item.suspicious_short_extracted_comments
    ]

    payload = {
        "locales": locales,
        "files": [asdict(item) for item in previews],
        "summary": {
            "files_with_changes": len(previews),
            "separator_blocks": sum(item.collapsed_separator_blocks for item in previews),
            "empty_extracted_comments": sum(
                item.removed_empty_extracted_comments for item in previews
            ),
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Preview report written to: {args.output}")
    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
