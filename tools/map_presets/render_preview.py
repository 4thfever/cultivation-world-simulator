from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.run.map_presets import get_map_preset, list_map_presets  # noqa: E402
from src.run.map_source import derive_tile_rows_from_region_rows, read_map_source  # noqa: E402


COLORS = {
    "plain": (132, 183, 112),
    "water": (64, 132, 188),
    "sea": (36, 84, 146),
    "mountain": (120, 120, 116),
    "forest": (61, 132, 78),
    "city": (190, 156, 92),
    "desert": (215, 188, 112),
    "rainforest": (43, 120, 72),
    "glacier": (170, 218, 228),
    "snow_mountain": (214, 222, 224),
    "volcano": (126, 66, 58),
    "grassland": (148, 194, 93),
    "swamp": (91, 117, 78),
    "farm": (174, 168, 98),
    "island": (156, 184, 104),
    "bamboo": (86, 150, 92),
    "gobi": (188, 155, 104),
    "tundra": (144, 166, 148),
}


def render_preview(map_id: str, *, cell_size: int = 10) -> Path:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise SystemExit("Pillow is required for map previews. Install pillow or run tests without preview rendering.") from exc

    preset = get_map_preset(map_id)
    if preset.path is None:
        raise SystemExit(f"Preset path not found: {map_id}")

    source = read_map_source(preset.path / "map.json")
    tile_rows = derive_tile_rows_from_region_rows(
        source.region_rows,
        wilderness_tile=source.wilderness_tile,
    )
    rows = source.height
    cols = source.width

    top_bar = 28
    image = Image.new("RGB", (cols * cell_size, rows * cell_size + top_bar), (28, 31, 34))
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("arial.ttf", 11)
    except Exception:
        font = ImageFont.load_default()

    draw.text((6, 7), f"{preset.id} / {preset.name} / {cols}x{rows}", fill=(235, 235, 226), font=font)

    for y, row in enumerate(tile_rows):
        for x, tile_name in enumerate(row):
            color = COLORS.get(tile_name.lower(), (180, 90, 180))
            px = x * cell_size
            py = y * cell_size + top_bar
            draw.rectangle((px, py, px + cell_size - 1, py + cell_size - 1), fill=color)

    for y, row in enumerate(source.region_rows):
        for x, rid in enumerate(row):
            px = x * cell_size
            py = y * cell_size + top_bar
            if x > 0 and source.region_rows[y][x - 1] != rid:
                draw.line((px, py, px, py + cell_size), fill=(38, 38, 34))
            if y > 0 and source.region_rows[y - 1][x] != rid:
                draw.line((px, py, px + cell_size, py), fill=(38, 38, 34))

    centers: dict[int, tuple[int, int, int]] = {}
    sums: dict[int, tuple[int, int, int]] = {}
    for y, row in enumerate(source.region_rows):
        for x, rid in enumerate(row):
            if rid == -1:
                continue
            sx, sy, count = sums.get(rid, (0, 0, 0))
            sums[rid] = (sx + x, sy + y, count + 1)
    for rid, (sx, sy, count) in sums.items():
        centers[rid] = (sx // count, sy // count, count)

    for rid, (x, y, count) in centers.items():
        if count < 3:
            continue
        px = x * cell_size + 1
        py = y * cell_size + top_bar + 1
        draw.text((px, py), str(rid), fill=(18, 18, 16), font=font)

    for rid, landmark in source.landmarks.items():
        px = landmark.x * cell_size
        py = landmark.y * cell_size + top_bar
        draw.rectangle(
            (px, py, px + cell_size * 2 - 1, py + cell_size * 2 - 1),
            outline=(255, 245, 120),
            width=2,
        )
        draw.text((px + 1, py + 1), str(rid), fill=(255, 245, 120), font=font)

    output_dir = PROJECT_ROOT / "tmp" / "map_previews"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"{map_id}.png"
    image.save(output)
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--map-id", default="")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    if args.all or not args.map_id:
        for preset in list_map_presets():
            print(render_preview(preset.id))
    else:
        print(render_preview(args.map_id))


if __name__ == "__main__":
    main()
