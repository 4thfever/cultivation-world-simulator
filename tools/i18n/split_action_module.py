#!/usr/bin/env python3
"""Split modules/action.po into smaller action module files."""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
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
        "--write",
        action="store_true",
        help="Actually write the split files back to disk. Default is dry-run.",
    )
    return parser


def build_split_outputs(po: polib.POFile) -> dict[str, polib.POFile]:
    buckets: dict[str, list[polib.POEntry]] = defaultdict(list)
    for entry in po:
        if not entry.msgid:
            continue
        target = get_action_target_file(entry.msgid)
        buckets[target].append(entry)

    outputs: dict[str, polib.POFile] = {}
    for filename, entries in buckets.items():
        target_po = polib.POFile()
        target_po.metadata = dict(po.metadata)
        for entry in entries:
            target_po.append(entry)
        outputs[filename] = target_po
    return outputs


def split_locale(locale: str, write: bool) -> None:
    modules_dir = PROJECT_ROOT / "static" / "locales" / locale / "modules"
    action_path = modules_dir / "action.po"
    po = polib.pofile(str(action_path))
    outputs = build_split_outputs(po)

    for filename in ("action.po", "action_combat.po", "action_progression.po", "action_world.po"):
        if filename not in outputs:
            continue
        target_path = modules_dir / filename
        print(f"{'WRITE' if write else 'DRY-RUN'} {target_path.relative_to(PROJECT_ROOT)} ({len(outputs[filename])} entries)")
        if write:
            outputs[filename].save(str(target_path))


def main() -> int:
    args = build_parser().parse_args()
    locales = (
        [item.strip() for item in args.locales.split(",") if item.strip()]
        if args.locales
        else get_locale_codes()
    )
    for locale in locales:
        split_locale(locale, args.write)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
