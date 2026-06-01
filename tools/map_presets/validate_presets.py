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
from src.run.map_source import (  # noqa: E402
    derive_tile_rows_from_region_rows,
    load_region_tile_bindings,
    read_map_source,
)


CONFIG_DIR = PROJECT_ROOT / "static" / "game_configs"
NORMAL_FRAGMENT_LIMIT = 8


def _metadata_region_ids() -> set[int]:
    ids: set[int] = set()
    for filename in ["normal_region.csv", "city_region.csv", "cultivate_region.csv", "sect_region.csv"]:
        with open(CONFIG_DIR / filename, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                rid = str(row.get("id", "")).strip()
                if rid.isdigit():
                    ids.add(int(rid))
    return ids


def _region_type(region_id: int) -> str:
    if 100 <= region_id < 200:
        return "normal"
    if 200 <= region_id < 300:
        return "cultivate"
    if 300 <= region_id < 400:
        return "city"
    if 400 <= region_id < 500:
        return "sect"
    return "unknown"


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


def _count_pair_edges(tile_rows: list[list[str]], pair: set[str]) -> int:
    height = len(tile_rows)
    width = len(tile_rows[0]) if height else 0
    count = 0
    for y, row in enumerate(tile_rows):
        for x, tile_name in enumerate(row):
            if x + 1 < width and {tile_name, row[x + 1]} == pair:
                count += 1
            if y + 1 < height and {tile_name, tile_rows[y + 1][x]} == pair:
                count += 1
    return count


def _count_checkerboards(tile_rows: list[list[str]], pair: set[str]) -> int:
    height = len(tile_rows)
    width = len(tile_rows[0]) if height else 0
    count = 0
    for y in range(height - 1):
        for x in range(width - 1):
            top_left = tile_rows[y][x]
            top_right = tile_rows[y][x + 1]
            bottom_left = tile_rows[y + 1][x]
            bottom_right = tile_rows[y + 1][x + 1]
            if (
                {top_left, top_right, bottom_left, bottom_right} == pair
                and top_left == bottom_right
                and top_right == bottom_left
            ):
                count += 1
    return count


def _max_edge_run(tile_rows: list[list[str]], x: int = 0) -> int:
    max_run = 0
    current_tile = None
    current_run = 0
    for row in tile_rows:
        tile_name = row[x]
        if tile_name == current_tile:
            current_run += 1
        else:
            max_run = max(max_run, current_run)
            current_tile = tile_name
            current_run = 1
    return max(max_run, current_run)


def _validate_visual_shape(preset_id: str, tile_rows: list[list[str]]) -> None:
    if preset_id == "island_seas":
        island_plain_edges = _count_pair_edges(tile_rows, {"island", "plain"})
        if island_plain_edges > 200:
            raise AssertionError(f"{preset_id}: island/plain terrain is too noisy ({island_plain_edges} edges)")
        checkerboards = _count_checkerboards(tile_rows, {"island", "plain"})
        if checkerboards:
            raise AssertionError(f"{preset_id}: island/plain checkerboard noise found ({checkerboards} blocks)")

    if preset_id == "mountain_frontier":
        max_left_edge_run = _max_edge_run(tile_rows, x=0)
        if max_left_edge_run > 20:
            raise AssertionError(f"{preset_id}: left map edge is too visually flat ({max_left_edge_run} tiles)")


def _validate_landmarks(preset_id: str, source, coords_by_region: dict[int, set[tuple[int, int]]]) -> None:
    for region_id, landmark in source.landmarks.items():
        if region_id not in coords_by_region:
            raise AssertionError(f"{preset_id}: landmark for missing region {region_id}")
        if (landmark.x, landmark.y) not in coords_by_region[region_id]:
            raise AssertionError(f"{preset_id}: landmark anchor is outside region {region_id}")
        if landmark.x + 1 >= source.width or landmark.y + 1 >= source.height:
            raise AssertionError(f"{preset_id}: landmark {region_id} 2x2 block is out of bounds")


def validate() -> None:
    presets = list_map_presets()
    if not presets:
        raise AssertionError("No map presets found")

    known_region_ids = _metadata_region_ids()
    explicit_bindings = load_region_tile_bindings()
    normal_region_ids = {rid for rid in known_region_ids if _region_type(rid) == "normal"}
    missing_normal_bindings = sorted(normal_region_ids - set(explicit_bindings))
    if missing_normal_bindings:
        raise AssertionError(f"Missing normal region tile bindings: {missing_normal_bindings}")

    expected_region_ids: set[int] | None = None

    for preset in presets:
        if preset.path is None:
            raise AssertionError(f"Preset has no path: {preset.id}")

        source = read_map_source(preset.path / "map.json")
        if source.map_id != preset.id:
            raise AssertionError(f"{preset.id}: map source id mismatch: {source.map_id}")
        if not source.region_rows:
            raise AssertionError(f"{preset.id}: empty region map")

        try:
            TileType(source.wilderness_tile)
        except ValueError as exc:
            raise AssertionError(f"{preset.id}: unknown wilderness tile {source.wilderness_tile}") from exc

        tile_rows = derive_tile_rows_from_region_rows(
            source.region_rows,
            wilderness_tile=source.wilderness_tile,
            bindings=explicit_bindings,
        )
        _validate_visual_shape(preset.id, tile_rows)

        region_ids: set[int] = set()
        coords_by_region: dict[int, set[tuple[int, int]]] = {}
        for y, row in enumerate(source.region_rows):
            for x, rid in enumerate(row):
                if rid == -1:
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
            component_count = _component_count(coords)
            if _region_type(rid) in {"city", "sect", "cultivate"} and component_count != 1:
                raise AssertionError(f"{preset.id}: region {rid} must be contiguous, components={component_count}")
            if _region_type(rid) == "normal" and component_count > NORMAL_FRAGMENT_LIMIT:
                raise AssertionError(f"{preset.id}: region {rid} is too fragmented, components={component_count}")

        _validate_landmarks(preset.id, source, coords_by_region)

        game_map = load_cultivation_world_map(preset.id)
        if game_map.width != source.width or game_map.height != source.height:
            raise AssertionError(f"{preset.id}: loaded size mismatch")
        for region in game_map.regions.values():
            if not game_map.is_in_bounds(*region.center_loc):
                raise AssertionError(f"{preset.id}: region {region.id} center out of bounds")

        print(f"OK {preset.id}: {source.width}x{source.height}, regions={len(region_ids)}")


if __name__ == "__main__":
    validate()
