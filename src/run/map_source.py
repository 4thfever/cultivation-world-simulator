from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.classes.environment.tile import TileType
from src.utils.df import game_configs, get_int, get_str


MAP_SOURCE_SCHEMA_VERSION = 2
DEFAULT_WILDERNESS_TILE = "plain"


@dataclass(frozen=True)
class MapLandmark:
    x: int
    y: int
    asset: str

    def to_dict(self) -> dict[str, Any]:
        return {"x": self.x, "y": self.y, "asset": self.asset}


@dataclass(frozen=True)
class RegionTileBinding:
    region_id: int
    tile: str
    landmark_asset: str | None = None


@dataclass(frozen=True)
class MapSource:
    map_id: str
    version: int
    width: int
    height: int
    wilderness_tile: str
    region_rows: list[list[int]]
    landmarks: dict[int, MapLandmark]


def _validate_tile(tile_name: str, *, field_name: str = "tile") -> str:
    value = str(tile_name).strip().lower()
    try:
        TileType(value)
    except ValueError as exc:
        raise ValueError(f"Unknown {field_name}: {tile_name}") from exc
    return value


def _validate_region_rows(rows: Any, *, width: int, height: int) -> list[list[int]]:
    if not isinstance(rows, list) or len(rows) != height:
        raise ValueError("Invalid region_rows height")

    normalized: list[list[int]] = []
    for row in rows:
        if not isinstance(row, list) or len(row) != width:
            raise ValueError("Invalid region_rows width")
        normalized.append([int(value) for value in row])
    return normalized


def _parse_landmarks(raw: Any, *, width: int, height: int) -> dict[int, MapLandmark]:
    if raw in (None, ""):
        return {}
    if not isinstance(raw, dict):
        raise ValueError("Invalid landmarks")

    landmarks: dict[int, MapLandmark] = {}
    for raw_region_id, value in raw.items():
        if not isinstance(value, dict):
            raise ValueError(f"Invalid landmark for region {raw_region_id}")
        region_id = int(raw_region_id)
        x = int(value.get("x"))
        y = int(value.get("y"))
        asset = str(value.get("asset") or "").strip()
        if not asset:
            raise ValueError(f"Missing landmark asset for region {region_id}")
        if x < 0 or y < 0 or x >= width or y >= height:
            raise ValueError(f"Landmark out of bounds for region {region_id}: {(x, y)}")
        landmarks[region_id] = MapLandmark(x=x, y=y, asset=asset)
    return landmarks


def read_map_source(path: Path) -> MapSource:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    schema_version = int(data.get("schema_version", 0) or 0)
    if schema_version != MAP_SOURCE_SCHEMA_VERSION:
        raise ValueError(f"Unsupported map source schema version: {schema_version}")

    width = int(data.get("width", 0) or 0)
    height = int(data.get("height", 0) or 0)
    if width <= 0 or height <= 0:
        raise ValueError("Invalid map source size")

    region_rows = _validate_region_rows(data.get("region_rows"), width=width, height=height)
    wilderness_tile = _validate_tile(data.get("wilderness_tile") or DEFAULT_WILDERNESS_TILE, field_name="wilderness_tile")

    return MapSource(
        map_id=str(data.get("id") or path.parent.name),
        version=int(data.get("version", 1) or 1),
        width=width,
        height=height,
        wilderness_tile=wilderness_tile,
        region_rows=region_rows,
        landmarks=_parse_landmarks(data.get("landmarks"), width=width, height=height),
    )


def map_source_to_dict(source: MapSource) -> dict[str, Any]:
    return {
        "schema_version": MAP_SOURCE_SCHEMA_VERSION,
        "id": source.map_id,
        "version": source.version,
        "width": source.width,
        "height": source.height,
        "wilderness_tile": source.wilderness_tile,
        "region_rows": source.region_rows,
        "landmarks": {
            str(region_id): landmark.to_dict()
            for region_id, landmark in sorted(source.landmarks.items())
        },
    }


def _region_type_by_id(region_id: int) -> str:
    if 100 <= region_id < 200:
        return "normal"
    if 200 <= region_id < 300:
        return "cultivate"
    if 300 <= region_id < 400:
        return "city"
    if 400 <= region_id < 500:
        return "sect"
    return "unknown"


def _sect_id_for_region(region_id: int) -> int:
    for row in game_configs.get("sect_region", []):
        if get_int(row, "id") == region_id:
            return get_int(row, "sect_id")
    return region_id - 400


def _cultivate_sub_type(region_id: int) -> str:
    for row in game_configs.get("cultivate_region", []):
        if get_int(row, "id") == region_id:
            return get_str(row, "sub_type") or "cave"
    return "cave"


def load_region_tile_bindings() -> dict[int, RegionTileBinding]:
    bindings: dict[int, RegionTileBinding] = {}
    for row in game_configs.get("region_tile", []):
        region_id = get_int(row, "region_id")
        if region_id <= 0:
            continue
        tile = _validate_tile(get_str(row, "tile"), field_name=f"region_tile[{region_id}].tile")
        landmark_asset = get_str(row, "landmark_asset") or None
        bindings[region_id] = RegionTileBinding(
            region_id=region_id,
            tile=tile,
            landmark_asset=landmark_asset,
        )
    return bindings


def resolve_region_tile_binding(
    region_id: int,
    explicit_bindings: dict[int, RegionTileBinding] | None = None,
) -> RegionTileBinding:
    bindings = explicit_bindings if explicit_bindings is not None else load_region_tile_bindings()
    if region_id in bindings:
        return bindings[region_id]

    region_type = _region_type_by_id(region_id)
    if region_type == "city":
        return RegionTileBinding(region_id=region_id, tile="city", landmark_asset=f"city_{region_id}")
    if region_type == "sect":
        return RegionTileBinding(region_id=region_id, tile="mountain", landmark_asset=f"sect_{_sect_id_for_region(region_id)}")
    if region_type == "cultivate":
        return RegionTileBinding(region_id=region_id, tile="mountain", landmark_asset=_cultivate_sub_type(region_id))
    raise ValueError(f"Missing region tile binding for region {region_id}")


def derive_tile_rows_from_region_rows(
    region_rows: list[list[int]],
    *,
    wilderness_tile: str = DEFAULT_WILDERNESS_TILE,
    bindings: dict[int, RegionTileBinding] | None = None,
) -> list[list[str]]:
    explicit_bindings = bindings if bindings is not None else load_region_tile_bindings()
    wilderness = _validate_tile(wilderness_tile, field_name="wilderness_tile")
    tile_rows: list[list[str]] = []

    for region_row in region_rows:
        tile_row: list[str] = []
        for region_id in region_row:
            rid = int(region_id)
            if rid == -1:
                tile_row.append(wilderness)
            else:
                tile_row.append(resolve_region_tile_binding(rid, explicit_bindings).tile)
        tile_rows.append(tile_row)
    return tile_rows


def collect_region_coords(region_rows: list[list[int]]) -> dict[int, list[tuple[int, int]]]:
    region_coords: dict[int, list[tuple[int, int]]] = {}
    for y, row in enumerate(region_rows):
        for x, value in enumerate(row):
            region_id = int(value)
            if region_id == -1:
                continue
            region_coords.setdefault(region_id, []).append((x, y))
    return region_coords
