from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "static" / "game_configs"

CATEGORY_FILES = {
    "weapon": CONFIG_DIR / "weapon.csv",
    "elixir": CONFIG_DIR / "elixir.csv",
    "auxiliary": CONFIG_DIR / "auxiliary.csv",
    "technique": CONFIG_DIR / "technique.csv",
    "goldfinger": CONFIG_DIR / "goldfinger.csv",
    "material": CONFIG_DIR / "material.csv",
}


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    return [
        row
        for row in rows
        if any((value or "").strip() for value in row.values())
        and str(row.get("name", "")).strip() != "名称"
    ]


def _row_id(row: dict[str, str]) -> str:
    return (row.get("item_id") or row.get("id") or row.get("key") or "").strip()


def build_manifest() -> list[dict[str, str]]:
    manifest: list[dict[str, str]] = []
    for category, path in CATEGORY_FILES.items():
        for row in _read_rows(path):
            item_id = _row_id(row)
            name = str(row.get("name", "")).strip()
            if not item_id or not name:
                continue
            desc = str(row.get("desc", "")).strip()
            meta_parts = [
                row.get("weapon_type", ""),
                row.get("grade", ""),
                row.get("realm", ""),
                row.get("type", ""),
                row.get("rarity", ""),
                row.get("technique_root", ""),
                row.get("stage_id", ""),
            ]
            manifest.append(
                {
                    "icon_key": f"{category}_{item_id}",
                    "category": category,
                    "id": item_id,
                    "name": name,
                    "desc": desc,
                    "meta": " ".join(part for part in meta_parts if part),
                    "asset_path": f"icons/items/{category}_{item_id}.png",
                }
            )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build item icon manifest from game config CSVs.")
    parser.add_argument("--out", default="tools/item_icons/manifest.generated.json")
    args = parser.parse_args()

    manifest = build_manifest()
    output = ROOT / args.out
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(manifest)} items to {output}")


if __name__ == "__main__":
    main()
