from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path

from tools.item_icons.build_manifest import build_manifest
from tools.item_icons.generate_preview_sheet import _hex_to_rgb
from tools.item_icons.postprocess import clean_chroma_background, pixelate_icon, split_contact_sheet, suppress_chroma_spill
from tools.item_icons.prompts import CHROMA_KEY, IconPromptItem, build_contact_sheet_prompt
from tools.item_icons.utils.fal_client import FalApiError, FalImageConfig, generate_to_file

ROOT = Path(__file__).resolve().parents[2]
INCLUDED_CATEGORIES = ("weapon", "elixir", "auxiliary", "technique", "goldfinger")
ECOLOGY_CATEGORIES = ("animal", "plant", "lode", "material")
FALLBACK_ITEMS = [
    {
        "icon_key": "fallback_weapon",
        "category": "fallback",
        "id": "weapon",
        "name": "兵器兜底",
        "desc": "通用武器图标。",
        "meta": "generic weapon",
    },
    {
        "icon_key": "fallback_elixir",
        "category": "fallback",
        "id": "elixir",
        "name": "丹药兜底",
        "desc": "通用丹药图标。",
        "meta": "generic pill bottle",
    },
    {
        "icon_key": "fallback_auxiliary",
        "category": "fallback",
        "id": "auxiliary",
        "name": "辅助装备兜底",
        "desc": "通用法器或辅助装备图标。",
        "meta": "generic magic artifact",
    },
    {
        "icon_key": "fallback_technique",
        "category": "fallback",
        "id": "technique",
        "name": "功法兜底",
        "desc": "通用功法秘籍图标。",
        "meta": "generic cultivation manual",
    },
    {
        "icon_key": "fallback_goldfinger",
        "category": "fallback",
        "id": "goldfinger",
        "name": "外挂兜底",
        "desc": "通用天赋外挂图标。",
        "meta": "generic celestial token",
    },
    {
        "icon_key": "fallback_unknown",
        "category": "fallback",
        "id": "unknown",
        "name": "未知物品兜底",
        "desc": "通用未知物品图标。",
        "meta": "mysterious item pouch",
    },
]
ECOLOGY_FALLBACK_ITEMS = [
    {
        "icon_key": "fallback_animal",
        "category": "fallback",
        "id": "animal",
        "name": "动物兜底",
        "desc": "通用灵兽或妖兽图标。",
        "meta": "generic spirit beast",
    },
    {
        "icon_key": "fallback_plant",
        "category": "fallback",
        "id": "plant",
        "name": "植物兜底",
        "desc": "通用灵草灵植图标。",
        "meta": "generic spiritual herb",
    },
    {
        "icon_key": "fallback_lode",
        "category": "fallback",
        "id": "lode",
        "name": "矿脉兜底",
        "desc": "通用矿脉矿石图标。",
        "meta": "generic ore vein",
    },
    {
        "icon_key": "fallback_material",
        "category": "fallback",
        "id": "material",
        "name": "材料兜底",
        "desc": "通用掉落材料图标。",
        "meta": "generic crafting material",
    },
]


def _load_fal_config() -> FalImageConfig:
    api_key = os.environ.get("FAL_KEY") or os.environ.get("ITEM_ICON_FAL_KEY")
    if not api_key:
        raise RuntimeError("请通过 FAL_KEY 或 ITEM_ICON_FAL_KEY 设置 fal API key")
    return FalImageConfig(
        api_key=api_key,
        model=os.environ.get("ITEM_ICON_FAL_MODEL", "openai/gpt-image-2"),
        image_size=os.environ.get("ITEM_ICON_FAL_IMAGE_SIZE", "square_hd"),
        quality=os.environ.get("ITEM_ICON_FAL_QUALITY", "low"),
        output_format=os.environ.get("ITEM_ICON_FAL_OUTPUT_FORMAT", "png"),
    )


def _to_prompt_item(row: dict[str, str]) -> IconPromptItem:
    return IconPromptItem(
        item_id=row["icon_key"],
        category=row["category"],
        name=row["name"],
        desc=row.get("desc", ""),
        meta=row.get("meta", ""),
    )


def _chunks(items: list[dict[str, str]], size: int) -> list[list[dict[str, str]]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def _read_simple_config(category: str) -> list[dict[str, str]]:
    import csv

    path = ROOT / "static" / "game_configs" / f"{category}.csv"
    rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            item_id = str(row.get("id") or "").strip()
            name = str(row.get("name") or "").strip()
            if not item_id or not name or name == "名称":
                continue
            desc = str(row.get("desc") or "").strip()
            stage_id = str(row.get("stage_id") or "").strip()
            rows.append(
                {
                    "icon_key": f"{category}_{item_id}",
                    "category": category,
                    "id": item_id,
                    "name": name,
                    "desc": desc,
                    "meta": f"stage {stage_id}" if stage_id else "",
                    "asset_path": f"icons/items/{category}_{item_id}.png",
                }
            )
    return rows


def _selected_manifest(include_material: bool, ecology_only: bool) -> list[dict[str, str]]:
    if ecology_only:
        items: list[dict[str, str]] = []
        for category in ECOLOGY_CATEGORIES:
            items.extend(_read_simple_config(category))
        items.extend(ECOLOGY_FALLBACK_ITEMS)
        return items

    categories = set(INCLUDED_CATEGORIES)
    if include_material:
        categories.add("material")
    items = [item for item in build_manifest() if item["category"] in categories]
    items.extend(FALLBACK_ITEMS)
    return items


def _load_done_batches(path: Path) -> set[str]:
    if not path.exists():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return set()
    return {str(batch.get("batch_id")) for batch in data.get("batches", []) if batch.get("ok")}


def _append_batch_meta(path: Path, batch_meta: dict[str, object]) -> None:
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {"batches": []}
    else:
        data = {"batches": []}
    data.setdefault("batches", []).append(batch_meta)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _process_batch(
    *,
    batch: list[dict[str, str]],
    batch_id: str,
    columns: int,
    rows: int,
    out_dir: Path,
    config: FalImageConfig,
    dry_run: bool,
) -> dict[str, object]:
    batch_rows = math.ceil(len(batch) / columns)
    raw_path = out_dir / "raw" / f"{batch_id}.png"
    split_dir = out_dir / "split" / batch_id
    alpha_dir = out_dir / "alpha" / batch_id
    despill_dir = out_dir / "despill" / batch_id
    pixel_dir = out_dir / "pixel"
    prompt = build_contact_sheet_prompt([_to_prompt_item(item) for item in batch], columns=columns)

    if dry_run:
        return {"ok": True, "batch_id": batch_id, "dry_run": True, "items": batch, "prompt": prompt}

    result = generate_to_file(prompt, raw_path, config=config)
    split_paths = split_contact_sheet(raw_path, split_dir, columns=columns, rows=batch_rows, prefix=batch_id)
    processed: list[dict[str, str]] = []
    spill_rgb = _hex_to_rgb(CHROMA_KEY)
    for item, split_path in zip(batch, split_paths):
        icon_key = item["icon_key"]
        alpha_path = alpha_dir / f"{icon_key}.png"
        despill_path = despill_dir / f"{icon_key}.png"
        pixel_path = pixel_dir / f"{icon_key}.png"
        clean_chroma_background(split_path, alpha_path)
        suppress_chroma_spill(alpha_path, despill_path, spill_rgb=spill_rgb, dominance=1.25, minimum_channel=55)
        pixelate_icon(despill_path, pixel_path)
        processed.append(
            {
                "icon_key": icon_key,
                "category": item["category"],
                "name": item["name"],
                "split": str(split_path),
                "alpha": str(alpha_path),
                "despill": str(despill_path),
                "pixel": str(pixel_path),
            }
        )
    return {
        "ok": True,
        "batch_id": batch_id,
        "request_id": result.get("request_id"),
        "image_url": result.get("image_url"),
        "raw": str(raw_path),
        "items": processed,
        "prompt": prompt,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate all configured item icons with fal gpt-image-2.")
    parser.add_argument("--out-dir", default="tools/item_icons/generated")
    parser.add_argument("--batch-size", type=int, default=9)
    parser.add_argument("--columns", type=int, default=3)
    parser.add_argument("--include-material", action="store_true")
    parser.add_argument("--ecology-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    out_dir = ROOT / args.out_dir
    meta_path = out_dir / "generation_manifest.json"
    items = _selected_manifest(args.include_material, args.ecology_only)
    batches = _chunks(items, args.batch_size)
    rows = math.ceil(args.batch_size / args.columns)
    config = _load_fal_config()
    done_batches = _load_done_batches(meta_path) if args.resume else set()

    summary = {
        "total_items": len(items),
        "total_batches": len(batches),
        "batch_size": args.batch_size,
        "columns": args.columns,
        "rows": rows,
        "categories": ECOLOGY_CATEGORIES if args.ecology_only else INCLUDED_CATEGORIES + (("material",) if args.include_material else ()),
        "fallback_count": len(ECOLOGY_FALLBACK_ITEMS) if args.ecology_only else len(FALLBACK_ITEMS),
    }
    (out_dir / "summary.json").parent.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False))

    for index, batch in enumerate(batches, start=1):
        batch_id = f"batch_{index:03d}"
        if batch_id in done_batches:
            print(f"skip {batch_id}")
            continue
        print(f"start {batch_id}: {len(batch)} items")
        try:
            batch_meta = _process_batch(
                batch=batch,
                batch_id=batch_id,
                columns=args.columns,
                rows=rows,
                out_dir=out_dir,
                config=config,
                dry_run=args.dry_run,
            )
        except FalApiError as exc:
            batch_meta = {
                "ok": False,
                "batch_id": batch_id,
                "status_code": exc.status_code,
                "error": str(exc),
                "items": batch,
            }
            _append_batch_meta(meta_path, batch_meta)
            print(json.dumps(batch_meta, ensure_ascii=False))
            raise SystemExit(1) from exc
        _append_batch_meta(meta_path, batch_meta)
        print(f"done {batch_id}")


if __name__ == "__main__":
    main()
