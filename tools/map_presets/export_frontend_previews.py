from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.run.map_presets import list_map_presets  # noqa: E402
from src.run.map_source import derive_tile_rows_from_region_rows, read_map_source  # noqa: E402


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


def _marker_color(kind: str) -> str:
    return {
        "city": "#d7aa4d",
        "sect": "#bd6fda",
        "cultivate": "#8c6a52",
    }.get(kind, "#ffffff")


def _marker_kind(asset: str) -> str:
    if asset.startswith("city_"):
        return "city"
    if asset.startswith("sect_"):
        return "sect"
    return "cultivate"


def build_svg(tile_rows: list[list[str]], region_rows: list[list[int]], landmarks: dict[int, object]) -> str:
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
            key = row[x].lower()
            x2 = x + 1
            while x2 < cols and row[x2].lower() == key:
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

    for landmark in landmarks.values():
        kind = _marker_kind(landmark.asset)
        cx = landmark.x * cell + cell
        cy = landmark.y * cell + cell
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
        source = read_map_source(preset.path / "map.json")
        tile_rows = derive_tile_rows_from_region_rows(source.region_rows, wilderness_tile=source.wilderness_tile)
        output = output_dir / f"{preset.id}.svg"
        output.write_text(build_svg(tile_rows, source.region_rows, source.landmarks), encoding="utf-8")
        print(output)


if __name__ == "__main__":
    export_previews()
