#!/usr/bin/env python3
"""Preview how modules/action.po would be split into smaller files."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import polib

from tools.i18n.action_split_rules import get_action_target_file
from tools.i18n.locale_registry import get_locale_codes


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--locales",
        help="Comma-separated locale codes to process. Defaults to all enabled locales.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "tmp" / "action_split_preview.json",
        help="Where to write the JSON preview report.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    locales = (
        [item.strip() for item in args.locales.split(",") if item.strip()]
        if args.locales
        else get_locale_codes()
    )

    preview: dict[str, dict[str, int]] = {}
    mismatches: dict[str, dict[str, list[str]]] = defaultdict(dict)
    reference: set[str] | None = None

    for locale in locales:
        action_path = PROJECT_ROOT / "static" / "locales" / locale / "modules" / "action.po"
        po = polib.pofile(str(action_path))
        assignments = Counter(get_action_target_file(entry.msgid) for entry in po if entry.msgid)
        preview[locale] = dict(assignments)

        msgids = {entry.msgid for entry in po if entry.msgid}
        if reference is None:
            reference = msgids
        else:
            missing = sorted(reference - msgids)
            extra = sorted(msgids - reference)
            if missing:
                mismatches[locale]["missing"] = missing[:20]
            if extra:
                mismatches[locale]["extra"] = extra[:20]

    payload = {
        "locales": locales,
        "preview": preview,
        "mismatches": mismatches,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Preview report written to: {args.output}")
    print(json.dumps(preview, ensure_ascii=False, indent=2))
    if mismatches:
        print("Locale mismatches detected:")
        print(json.dumps(mismatches, ensure_ascii=False, indent=2))
    return 0 if not mismatches else 1


if __name__ == "__main__":
    raise SystemExit(main())
