from __future__ import annotations

from typing import Any

from src.classes.environment.map import Map
from src.classes.environment.tile import TileType
from src.run.load_map import build_map_from_rows, build_map_from_source
from src.run.map_presets import DEFAULT_MAP_ID
from src.run.map_source import MapLandmark, MapSource


MAP_SNAPSHOT_SCHEMA_VERSION = 2


def serialize_map_snapshot(game_map: Map) -> dict[str, Any]:
    region_rows: list[list[int]] = []

    for y in range(game_map.height):
        region_row: list[int] = []
        for x in range(game_map.width):
            tile = game_map.get_tile(x, y)
            region_row.append(int(tile.region.id) if tile.region is not None else -1)
        region_rows.append(region_row)

    return {
        "schema_version": MAP_SNAPSHOT_SCHEMA_VERSION,
        "preset_id": getattr(game_map, "map_id", DEFAULT_MAP_ID),
        "preset_version": int(getattr(game_map, "preset_version", 1) or 1),
        "width": int(game_map.width),
        "height": int(game_map.height),
        "wilderness_tile": str(getattr(game_map, "wilderness_tile", "plain") or "plain"),
        "region_rows": region_rows,
        "landmarks": getattr(game_map, "landmarks", {}) or {},
        "region_tile_overrides": {},
    }


def _validate_matrix_shape(rows: Any, *, width: int, height: int, field_name: str) -> list[list[Any]]:
    if not isinstance(rows, list) or len(rows) != height:
        raise ValueError(f"Invalid {field_name} height")

    normalized: list[list[Any]] = []
    for row in rows:
        if not isinstance(row, list) or len(row) != width:
            raise ValueError(f"Invalid {field_name} width")
        normalized.append(row)
    return normalized


def load_map_from_snapshot(snapshot: dict[str, Any]) -> Map:
    schema_version = int(snapshot.get("schema_version", 0) or 0)
    if schema_version == 1:
        return _load_v1_map_from_snapshot(snapshot)
    if schema_version != MAP_SNAPSHOT_SCHEMA_VERSION:
        raise ValueError(f"Unsupported map snapshot schema version: {schema_version}")

    width = int(snapshot.get("width", 0) or 0)
    height = int(snapshot.get("height", 0) or 0)
    if width <= 0 or height <= 0:
        raise ValueError("Invalid map snapshot size")

    region_rows = _validate_matrix_shape(
        snapshot.get("region_rows"),
        width=width,
        height=height,
        field_name="region_rows",
    )

    normalized_region_rows: list[list[int]] = []
    for region_row in region_rows:
        normalized_region_row: list[int] = []
        for region_id in region_row:
            normalized_region_row.append(int(region_id))
        normalized_region_rows.append(normalized_region_row)

    preset_id = str(snapshot.get("preset_id") or DEFAULT_MAP_ID)
    landmarks: dict[int, MapLandmark] = {}
    raw_landmarks = snapshot.get("landmarks") or {}
    if isinstance(raw_landmarks, dict):
        for raw_region_id, value in raw_landmarks.items():
            if not isinstance(value, dict):
                continue
            landmarks[int(raw_region_id)] = MapLandmark(
                x=int(value.get("x", 0)),
                y=int(value.get("y", 0)),
                asset=str(value.get("asset") or ""),
            )

    source = MapSource(
        map_id=preset_id,
        version=int(snapshot.get("preset_version", 1) or 1),
        width=width,
        height=height,
        wilderness_tile=str(snapshot.get("wilderness_tile") or "plain"),
        region_rows=normalized_region_rows,
        landmarks=landmarks,
    )
    return build_map_from_source(
        source,
        map_id=preset_id,
        map_name=str(snapshot.get("map_name") or ""),
        preset_version=int(snapshot.get("preset_version", 1) or 1),
    )


def _load_v1_map_from_snapshot(snapshot: dict[str, Any]) -> Map:
    width = int(snapshot.get("width", 0) or 0)
    height = int(snapshot.get("height", 0) or 0)
    if width <= 0 or height <= 0:
        raise ValueError("Invalid map snapshot size")

    tile_rows = _validate_matrix_shape(
        snapshot.get("tile_rows"),
        width=width,
        height=height,
        field_name="tile_rows",
    )
    region_rows = _validate_matrix_shape(
        snapshot.get("region_rows"),
        width=width,
        height=height,
        field_name="region_rows",
    )

    normalized_tile_rows: list[list[str]] = []
    normalized_region_rows: list[list[int]] = []
    for tile_row, region_row in zip(tile_rows, region_rows):
        normalized_tile_row: list[str] = []
        normalized_region_row: list[int] = []
        for tile_name, region_id in zip(tile_row, region_row):
            tile_value = str(tile_name).lower()
            try:
                TileType(tile_value)
            except ValueError as exc:
                raise ValueError(f"Unknown tile type in map snapshot: {tile_name}") from exc
            normalized_tile_row.append(tile_value)
            normalized_region_row.append(int(region_id))
        normalized_tile_rows.append(normalized_tile_row)
        normalized_region_rows.append(normalized_region_row)

    preset_id = str(snapshot.get("preset_id") or DEFAULT_MAP_ID)
    return build_map_from_rows(
        normalized_tile_rows,
        normalized_region_rows,
        map_id=preset_id,
        map_name=str(snapshot.get("map_name") or ""),
        preset_version=int(snapshot.get("preset_version", 1) or 1),
    )
