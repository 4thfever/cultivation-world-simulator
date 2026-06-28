from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from tools.item_icons.postprocess import (
    clean_chroma_background,
    pixelate_icon,
    split_contact_sheet,
    suppress_chroma_spill,
)
from tools.item_icons.prompts import CHROMA_KEY, IconPromptItem, build_contact_sheet_prompt
from tools.item_icons.utils.fal_client import FalApiError, FalImageConfig, generate_to_file

ROOT = Path(__file__).resolve().parents[2]
TOOL_DIR = Path(__file__).resolve().parent


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    cleaned = value.strip().lstrip("#")
    if len(cleaned) != 6:
        return (255, 0, 255)
    return (int(cleaned[0:2], 16), int(cleaned[2:4], 16), int(cleaned[4:6], 16))


PREVIEW_ITEMS = [
    IconPromptItem("weapon_preview_sword", "weapon", "练气剑", "市井铁匠铺打造的铁剑，勉强能用。", "simple iron sword"),
    IconPromptItem("elixir_preview_breakthrough", "elixir", "练气破境丹", "凝聚灵气，辅助突破瓶颈的丹药。", "round jade pill"),
    IconPromptItem("auxiliary_preview_banner", "auxiliary", "万魂幡", "阴气森森的魂幡。", "dark soul banner"),
    IconPromptItem("technique_preview_gold_body", "technique", "混元金身", "佛门护教神功，浑身坚若金石。", "golden scripture manual"),
    IconPromptItem("goldfinger_preview_fortune", "goldfinger", "气运之子", "被天地眷顾，机缘主动靠近。", "lucky celestial token"),
    IconPromptItem("fallback_weapon", "fallback", "兵器兜底", "通用武器图标。", "generic weapon"),
    IconPromptItem("fallback_elixir", "fallback", "丹药兜底", "通用丹药图标。", "generic pill bottle"),
    IconPromptItem("fallback_technique", "fallback", "功法兜底", "通用功法秘籍图标。", "generic cultivation book"),
    IconPromptItem("fallback_unknown", "fallback", "未知物品兜底", "通用未知物品图标。", "mysterious item pouch"),
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate one fal preview contact sheet and processed pixel icons.")
    parser.add_argument("--out-dir", default="tools/item_icons/preview")
    parser.add_argument("--prefix", default="preview_sheet_001")
    args = parser.parse_args()

    out_dir = ROOT / args.out_dir
    raw_dir = out_dir / "raw"
    split_dir = out_dir / "split"
    alpha_dir = out_dir / "alpha"
    despill_dir = out_dir / "despill"
    pixel_dir = out_dir / "pixel"
    raw_path = raw_dir / f"{args.prefix}.png"

    prompt = build_contact_sheet_prompt(PREVIEW_ITEMS, columns=3)
    config = _load_fal_config()

    try:
        result = generate_to_file(prompt, raw_path, config=config)
    except FalApiError as exc:
        meta = {
            "ok": False,
            "status_code": exc.status_code,
            "error": str(exc),
            "model": config.model,
            "quality": config.quality,
        }
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"{args.prefix}.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(meta, ensure_ascii=False))
        raise SystemExit(1) from exc

    split_paths = split_contact_sheet(raw_path, split_dir, columns=3, rows=3, prefix=args.prefix)
    processed: list[dict[str, str]] = []
    for item, split_path in zip(PREVIEW_ITEMS, split_paths):
        alpha_path = alpha_dir / f"{item.item_id}.png"
        despill_path = despill_dir / f"{item.item_id}.png"
        pixel_path = pixel_dir / f"{item.item_id}.png"
        clean_chroma_background(split_path, alpha_path)
        suppress_chroma_spill(alpha_path, despill_path, spill_rgb=_hex_to_rgb(CHROMA_KEY))
        pixelate_icon(despill_path, pixel_path)
        processed.append(
            {
                "item_id": item.item_id,
                "category": item.category,
                "name": item.name,
                "split": str(split_path),
                "alpha": str(alpha_path),
                "despill": str(despill_path),
                "pixel": str(pixel_path),
            }
        )

    meta = {
        "ok": True,
        "model": config.model,
        "quality": config.quality,
        "raw": str(raw_path),
        "request_id": result.get("request_id"),
        "image_url": result.get("image_url"),
        "processed": processed,
        "prompt": prompt,
    }
    (out_dir / f"{args.prefix}.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({k: meta[k] for k in ("ok", "model", "quality", "raw")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
