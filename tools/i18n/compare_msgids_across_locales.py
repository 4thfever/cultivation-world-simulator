#!/usr/bin/env python3
"""
Compare msgids across .po files in all enabled locales.

Outputs a plan showing:
- Which .po files exist in which locales
- For each file present in multiple locales: which msgids differ (present in some but not all)
- Summary statistics
"""

import sys
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import polib
except ImportError:
    print("Error: polib is required. Please install it using 'pip install polib'")
    sys.exit(1)

from tools.i18n.locale_registry import get_locale_codes, get_project_root

LOCALES = get_locale_codes()


def extract_msgids(filepath: Path) -> set[str]:
    """Extract all non-empty msgids from a .po file."""
    if not filepath.exists():
        return set()
    po = polib.pofile(str(filepath))
    return {entry.msgid for entry in po if entry.msgid}


def collect_po_files(root: Path) -> dict[str, dict[str, Path]]:
    """
    Collect all .po files grouped by relative path.
    Returns: {rel_path: {locale: Path}}
    """
    result: dict[str, dict[str, Path]] = defaultdict(dict)
    locales_dir = root / "static" / "locales"

    for locale in LOCALES:
        locale_dir = locales_dir / locale
        if not locale_dir.exists():
            continue
        for po_file in locale_dir.rglob("*.po"):
            rel = po_file.relative_to(locale_dir)
            rel_key = str(rel).replace("\\", "/")
            result[rel_key][locale] = po_file

    return dict(result)


def main() -> None:
    root = get_project_root()
    files_by_rel = collect_po_files(root)

    # 1. File-level differences
    files_in_all = []
    files_partial = []
    files_single = []

    for rel_path, locale_paths in sorted(files_by_rel.items()):
        locales_present = set(locale_paths.keys())
        if len(locales_present) == len(LOCALES):
            files_in_all.append((rel_path, locale_paths))
        elif len(locales_present) > 1:
            files_partial.append((rel_path, locale_paths))
        else:
            files_single.append((rel_path, locale_paths))

    # 2. Msgid-level differences (for files present in multiple locales)
    msgid_diffs: list[tuple[str, dict[str, set[str]]]] = []

    for rel_path, locale_paths in files_in_all + files_partial:
        msgids_by_locale: dict[str, set[str]] = {}
        for locale, path in locale_paths.items():
            msgids_by_locale[locale] = extract_msgids(path)

        all_msgids = set()
        for s in msgids_by_locale.values():
            all_msgids |= s

        if not all_msgids:
            continue

        # Check if any msgid differs across locales
        differing: dict[str, set[str]] = {}
        for msgid in all_msgids:
            present_in = {loc for loc, ids in msgids_by_locale.items() if msgid in ids}
            if len(present_in) < len(locale_paths):
                missing_in = set(locale_paths.keys()) - present_in
                key = ", ".join(sorted(missing_in))
                differing.setdefault(key, set()).add(msgid)

        if differing:
            msgid_diffs.append((rel_path, differing))

    # 3. Output report
    lines = [
        f"# Msgid Comparison Across Locales ({', '.join(LOCALES)})",
        "",
        "## 1. File Coverage Summary",
        "",
        f"- Files in all {len(LOCALES)} locales: {len(files_in_all)}",
        f"- Files in 2 locales only: {len(files_partial)}",
        f"- Files in 1 locale only: {len(files_single)}",
        "",
    ]

    if files_partial:
        lines.append("### Files missing in some locales")
        for rel_path, locale_paths in files_partial:
            present = ", ".join(sorted(locale_paths.keys()))
            missing = ", ".join(sorted(set(LOCALES) - set(locale_paths.keys())))
            lines.append(f"- `{rel_path}`: present in [{present}], missing in [{missing}]")
        lines.append("")

    if files_single:
        lines.append("### Files in only one locale")
        for rel_path, locale_paths in files_single:
            loc = list(locale_paths.keys())[0]
            lines.append(f"- `{rel_path}`: only in {loc}")
        lines.append("")

    lines.append("## 2. Msgid Differences (within files present in multiple locales)")
    lines.append("")

    if not msgid_diffs:
        lines.append("No msgid differences found. All msgids are consistent across locales.")
    else:
        lines.append(f"Found {len(msgid_diffs)} file(s) with differing msgids.")
        lines.append("")

        for rel_path, differing in msgid_diffs:
            lines.append(f"### `{rel_path}`")
            for missing_locales, msgids in sorted(differing.items()):
                lines.append(f"- **Missing in:** {missing_locales} ({len(msgids)} msgid(s))")
                for msgid in sorted(msgids):
                    preview = msgid.replace("\n", " ").strip()
                    if len(preview) > 60:
                        preview = preview[:57] + "..."
                    lines.append(f"  - `{preview}`")
            lines.append("")

    lines.append("## 3. Action Plan")
    lines.append("")
    lines.append("To align msgids across locales:")
    lines.append("")
    if files_partial or files_single:
        lines.append("1. **Add missing .po files**: Create the missing locale files for files listed in section 1.")
    if msgid_diffs:
        lines.append(
            "2. **Add missing msgids**: For each msgid listed in section 2, add the entry to the locale(s) where it is missing."
        )
        lines.append(
            "   - Copy the msgid and add an appropriate msgstr (or empty msgstr for placeholder)."
        )
    if not files_partial and not files_single and not msgid_diffs:
        lines.append("- No action needed. All locales are in sync.")
    lines.append("")

    report = "\n".join(lines)
    print(report)

    # Also write to file
    out_path = root / "msgid_comparison_plan.md"
    out_path.write_text(report, encoding="utf-8")
    print(f"\nReport written to: {out_path}")


if __name__ == "__main__":
    main()
