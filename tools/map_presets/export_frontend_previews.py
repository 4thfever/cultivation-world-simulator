from __future__ import annotations

import csv
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.run.map_presets import list_map_presets  # noqa: E402


COLORS = {
    "plain": "#84b770",
    "water": "#4084bc",
    "sea": "#245492",
    "mountain": "#787874",
    "forest": "#3d844e",
    "city": "#be9c5c",
    "desert": "#d7bc70",
    "rainforest": "#2b7848",
    "glacier": "#aadae4",
    "snow_mountain": "#d6dee0",
    "volcano": "#7e423a",
    "grassland": "#94c25d",
    "swamp": "#5b754e",
    "cave": "#64584c",
    "ruin": "#847468",
    "farm": "#aea862",
    "sect": "#a060ac",
    "island": "#9cb868",
    "bamboo": "#56965c",
    "gobi": "#bc9b68",
    "tundra": "#90a694",
    "marsh": "#587a62",
}


def _read_csv(path: Path) -> list[list[str]]:
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.reader(f))


def _tile_key(tile_name: str) -> str:
    if "_" in tile_name:
        if tile_name.startswith("city_"):
            return "city"
        if tile_name.startswith("sect_"):
            return "sect"
        if tile_name.startswith("cave_"):
            return "cave"
        if tile_name.startswith("ruin_"):
            return "ruin"
    return tile_name.lower()


def _marker(tile_name: str) -> str | None:
    if tile_name.startswith("city_"):
        return "city"
    if tile_name.startswith("sect_"):
        return "sect"
    if tile_name.startswith("cave_") or tile_name.startswith("ruin_"):
        return "cultivate"
    return None


def _marker_color(kind: str) -> str:
    return {
        "city": "#d7aa4d",
        "sect": "#bd6fda",
        "cultivate": "#8c6a52",
    }.get(kind, "#ffffff")


def build_svg(tile_rows: list[list[str]], region_rows: list[list[str]]) -> str:
    rows = len(tile_rows)
    cols = len(tile_rows[0]) if rows else 0
    cell = 2
    width = cols * cell
    height = rows * cell

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" preserveAspectRatio="none">',
        '<rect width="100%" height="100%" fill="#1f2933"/>',
    ]

    # Horizontal runs keep the SVG small enough while preserving the real map.
    for y, row in enumerate(tile_rows):
        x = 0
        while x < cols:
            key = _tile_key(row[x])
            x2 = x + 1
            while x2 < cols and _tile_key(row[x2]) == key:
                x2 += 1
            color = COLORS.get(key, "#b45ab4")
            parts.append(
                f'<rect x="{x * cell}" y="{y * cell}" width="{(x2 - x) * cell}" height="{cell}" fill="{color}"/>'
            )
            x = x2

    boundary_color = "#25251f"
    boundary_opacity = "0.55"
    for y, row in enumerate(region_rows):
        for x, rid in enumerate(row):
            px = x * cell
            py = y * cell
            if x > 0 and region_rows[y][x - 1] != rid:
                parts.append(
                    f'<path d="M{px} {py}V{py + cell}" stroke="{boundary_color}" stroke-opacity="{boundary_opacity}" stroke-width="0.55"/>'
                )
            if y > 0 and region_rows[y - 1][x] != rid:
                parts.append(
                    f'<path d="M{px} {py}H{px + cell}" stroke="{boundary_color}" stroke-opacity="{boundary_opacity}" stroke-width="0.55"/>'
                )

    marker_seen: set[str] = set()
    for y, row in enumerate(tile_rows):
        for x, tile_name in enumerate(row):
            kind = _marker(tile_name)
            if kind is None:
                continue
            # Large tile slices are 2x2; mark only the first slice of each object.
            marker_id = tile_name.rsplit("_", 1)[0]
            if marker_id in marker_seen:
                continue
            marker_seen.add(marker_id)
            cx = x * cell + cell
            cy = y * cell + cell
            parts.append(
                f'<circle cx="{cx}" cy="{cy}" r="1.9" fill="{_marker_color(kind)}" stroke="#1b1b18" stroke-width="0.45"/>'
            )

    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def export_previews() -> None:
    output_dir = PROJECT_ROOT / "web" / "src" / "assets" / "map-previews"
    output_dir.mkdir(parents=True, exist_ok=True)

    for preset in list_map_presets():
        if preset.path is None:
            continue
        tile_rows = _read_csv(preset.path / "tile_map.csv")
        region_rows = _read_csv(preset.path / "region_map.csv")
        output = output_dir / f"{preset.id}.svg"
        output.write_text(build_svg(tile_rows, region_rows), encoding="utf-8")
        print(output)


if __name__ == "__main__":
    export_previews()
