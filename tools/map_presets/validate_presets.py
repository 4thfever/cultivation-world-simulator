from __future__ import annotations

import csv
import sys
from collections import deque
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.classes.environment.tile import TileType  # noqa: E402
from src.run.load_map import load_cultivation_world_map  # noqa: E402
from src.run.map_presets import list_map_presets  # noqa: E402


CONFIG_DIR = PROJECT_ROOT / "static" / "game_configs"


def _read_csv(path: Path) -> list[list[str]]:
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.reader(f))


def _metadata_region_ids() -> set[str]:
    ids: set[str] = set()
    for filename in ["normal_region.csv", "city_region.csv", "cultivate_region.csv", "sect_region.csv"]:
        with open(CONFIG_DIR / filename, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                rid = str(row.get("id", "")).strip()
                if rid.isdigit():
                    ids.add(rid)
    return ids


def _component_count(coords: set[tuple[int, int]]) -> int:
    remaining = set(coords)
    count = 0
    while remaining:
        count += 1
        start = remaining.pop()
        queue: deque[tuple[int, int]] = deque([start])
        while queue:
            x, y = queue.popleft()
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if (nx, ny) in remaining:
                    remaining.remove((nx, ny))
                    queue.append((nx, ny))
    return count


def _validate_large_tile_slices(preset_id: str, tile_rows: list[list[str]]) -> None:
    groups: dict[str, dict[str, tuple[int, int]]] = {}
    for y, row in enumerate(tile_rows):
        for x, tile_name in enumerate(row):
            if "_" not in tile_name:
                continue
            if not any(tile_name.startswith(prefix) for prefix in ("city_", "sect_", "cave_", "ruin_")):
                continue
            base, idx = tile_name.rsplit("_", 1)
            if idx not in {"0", "1", "2", "3"}:
                continue
            groups.setdefault(base, {})[idx] = (x, y)

    for base, parts in groups.items():
        if set(parts) != {"0", "1", "2", "3"}:
            raise AssertionError(f"{preset_id}: large tile {base} is missing slices")
        x0, y0 = parts["0"]
        expected = {
            "0": (x0, y0),
            "1": (x0 + 1, y0),
            "2": (x0, y0 + 1),
            "3": (x0 + 1, y0 + 1),
        }
        if parts != expected:
            raise AssertionError(f"{preset_id}: large tile {base} slices are not a 2x2 block")


def validate() -> None:
    presets = list_map_presets()
    if not presets:
        raise AssertionError("No map presets found")

    known_region_ids = _metadata_region_ids()
    expected_region_ids: set[str] | None = None

    for preset in presets:
        if preset.path is None:
            raise AssertionError(f"Preset has no path: {preset.id}")

        tile_rows = _read_csv(preset.path / "tile_map.csv")
        region_rows = _read_csv(preset.path / "region_map.csv")
        if len(tile_rows) != len(region_rows):
            raise AssertionError(f"{preset.id}: tile/region row count mismatch")
        if not tile_rows:
            raise AssertionError(f"{preset.id}: empty tile map")

        width = len(tile_rows[0])
        if any(len(row) != width for row in tile_rows):
            raise AssertionError(f"{preset.id}: inconsistent tile row width")
        if any(len(row) != width for row in region_rows):
            raise AssertionError(f"{preset.id}: inconsistent region row width")
        _validate_large_tile_slices(preset.id, tile_rows)

        region_ids: set[str] = set()
        coords_by_region: dict[str, set[tuple[int, int]]] = {}
        for y, (tile_row, region_row) in enumerate(zip(tile_rows, region_rows)):
            for x, tile_name in enumerate(tile_row):
                if "_" not in tile_name:
                    try:
                        TileType(tile_name.lower())
                    except ValueError as exc:
                        raise AssertionError(f"{preset.id}: unknown tile type {tile_name}") from exc
                rid = str(region_row[x]).strip()
                if rid == "-1":
                    continue
                if rid not in known_region_ids:
                    raise AssertionError(f"{preset.id}: unknown region id {rid}")
                region_ids.add(rid)
                coords_by_region.setdefault(rid, set()).add((x, y))

        if expected_region_ids is None:
            expected_region_ids = region_ids
        elif region_ids != expected_region_ids:
            missing = sorted(expected_region_ids - region_ids)
            extra = sorted(region_ids - expected_region_ids)
            raise AssertionError(f"{preset.id}: region coverage mismatch, missing={missing}, extra={extra}")

        for rid, coords in coords_by_region.items():
            if not coords:
                raise AssertionError(f"{preset.id}: region {rid} has no coords")
            if _component_count(coords) > 8:
                raise AssertionError(f"{preset.id}: region {rid} is too fragmented")

        game_map = load_cultivation_world_map(preset.id)
        if game_map.width != width or game_map.height != len(tile_rows):
            raise AssertionError(f"{preset.id}: loaded size mismatch")
        for region in game_map.regions.values():
            if not game_map.is_in_bounds(*region.center_loc):
                raise AssertionError(f"{preset.id}: region {region.id} center out of bounds")

        print(f"OK {preset.id}: {width}x{len(tile_rows)}, regions={len(region_ids)}")


if __name__ == "__main__":
    validate()
