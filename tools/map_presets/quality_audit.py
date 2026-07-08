from __future__ import annotations

import argparse
import json
import sys
from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.run.map_presets import get_map_preset, list_map_presets  # noqa: E402
from src.run.map_source import derive_tile_rows_from_region_rows, read_map_source  # noqa: E402


Coord = tuple[int, int]

WATER_REGION_ID = 106
SEA_REGION_ID = 105
DEFAULT_SMALL_COMPONENT_LIMIT = 3
DEFAULT_BLOCKY_AREA_THRESHOLD = 80
DEFAULT_BLOCKY_FILL_THRESHOLD = 0.78
DEFAULT_STRAIGHT_EDGE_THRESHOLD = 10
DEFAULT_LANDMARK_EDGE_DISTANCE = 0
MOUNTAIN_IDENTITY_TILES = {"mountain", "snow_mountain", "volcano", "cave", "ruin", "tundra"}


@dataclass(frozen=True)
class Component:
    size: int
    bbox: tuple[int, int, int, int]
    coords: tuple[Coord, ...]

    @property
    def width(self) -> int:
        return self.bbox[2] - self.bbox[0] + 1

    @property
    def height(self) -> int:
        return self.bbox[3] - self.bbox[1] + 1


@dataclass(frozen=True)
class AuditIssue:
    map_id: str
    code: str
    message: str
    severity: str = "warning"
    region_id: int | None = None
    value: int | float | str | None = None
    threshold: int | float | str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def region_type(region_id: int) -> str:
    if 100 <= region_id < 200:
        return "normal"
    if 200 <= region_id < 300:
        return "cultivate"
    if 300 <= region_id < 400:
        return "city"
    if 400 <= region_id < 500:
        return "sect"
    return "unknown"


def collect_components(coords: Iterable[Coord]) -> list[Component]:
    remaining = set(coords)
    components: list[Component] = []
    while remaining:
        start = remaining.pop()
        queue: deque[Coord] = deque([start])
        component_coords = [start]
        while queue:
            x, y = queue.popleft()
            for neighbor in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
                    component_coords.append(neighbor)
        xs = [x for x, _ in component_coords]
        ys = [y for _, y in component_coords]
        components.append(
            Component(
                size=len(component_coords),
                bbox=(min(xs), min(ys), max(xs), max(ys)),
                coords=tuple(component_coords),
            )
        )
    return sorted(components, key=lambda item: item.size, reverse=True)


def coords_by_region(region_rows: list[list[int]]) -> dict[int, set[Coord]]:
    by_region: dict[int, set[Coord]] = {}
    for y, row in enumerate(region_rows):
        for x, region_id in enumerate(row):
            rid = int(region_id)
            if rid == -1:
                continue
            by_region.setdefault(rid, set()).add((x, y))
    return by_region


def coords_by_tile(tile_rows: list[list[str]], tile_names: set[str]) -> set[Coord]:
    normalized = {name.lower() for name in tile_names}
    return {
        (x, y)
        for y, row in enumerate(tile_rows)
        for x, tile_name in enumerate(row)
        if tile_name.lower() in normalized
    }


def coords_by_tile_predicate(tile_rows: list[list[str]], predicate) -> set[Coord]:
    return {
        (x, y)
        for y, row in enumerate(tile_rows)
        for x, tile_name in enumerate(row)
        if predicate(tile_name.lower())
    }


def tile_fraction(tile_rows: list[list[str]], tile_names: set[str]) -> float:
    height = len(tile_rows)
    width = len(tile_rows[0]) if height else 0
    total = width * height
    if total <= 0:
        return 0.0
    coords = coords_by_tile(tile_rows, tile_names)
    return len(coords) / total


def component_fill_ratio(component: Component) -> float:
    bbox_area = component.width * component.height
    if bbox_area <= 0:
        return 0.0
    return component.size / bbox_area


def boundary_distance(coords: set[Coord], target: Coord) -> int:
    if target not in coords:
        return 0
    queue: deque[tuple[Coord, int]] = deque([(target, 0)])
    visited = {target}
    while queue:
        (x, y), distance = queue.popleft()
        for neighbor in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if neighbor not in coords:
                return distance
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, distance + 1))
    return 0


def count_region_touch_edges(region_rows: list[list[int]], a: int, b: int) -> int:
    height = len(region_rows)
    width = len(region_rows[0]) if height else 0
    edges = 0
    for y, row in enumerate(region_rows):
        for x, region_id in enumerate(row):
            if x + 1 < width and {int(region_id), int(row[x + 1])} == {a, b}:
                edges += 1
            if y + 1 < height and {int(region_id), int(region_rows[y + 1][x])} == {a, b}:
                edges += 1
    return edges


def longest_straight_boundary_run(
    region_rows: list[list[int]],
    region_id: int,
    *,
    include_map_edge: bool = False,
) -> int:
    height = len(region_rows)
    width = len(region_rows[0]) if height else 0
    max_run = 0

    for y in range(height + 1):
        run = 0
        if not include_map_edge and y in {0, height}:
            continue
        for x in range(width):
            up = int(region_rows[y - 1][x]) if y > 0 else None
            down = int(region_rows[y][x]) if y < height else None
            is_boundary = (up == region_id) != (down == region_id)
            run = run + 1 if is_boundary else 0
            max_run = max(max_run, run)

    for x in range(width + 1):
        run = 0
        if not include_map_edge and x in {0, width}:
            continue
        for y in range(height):
            left = int(region_rows[y][x - 1]) if x > 0 else None
            right = int(region_rows[y][x]) if x < width else None
            is_boundary = (left == region_id) != (right == region_id)
            run = run + 1 if is_boundary else 0
            max_run = max(max_run, run)

    return max_run


def audit_region_components(
    map_id: str,
    region_rows: list[list[int]],
    *,
    small_component_limit: int = DEFAULT_SMALL_COMPONENT_LIMIT,
    blocky_area_threshold: int = DEFAULT_BLOCKY_AREA_THRESHOLD,
    blocky_fill_threshold: float = DEFAULT_BLOCKY_FILL_THRESHOLD,
    straight_edge_threshold: int = DEFAULT_STRAIGHT_EDGE_THRESHOLD,
) -> list[AuditIssue]:
    issues: list[AuditIssue] = []
    for region_id, coords in sorted(coords_by_region(region_rows).items()):
        components = collect_components(coords)
        small_components = [component for component in components[1:] if component.size <= small_component_limit]
        if small_components:
            issues.append(
                AuditIssue(
                    map_id=map_id,
                    code="small_region_fragments",
                    region_id=region_id,
                    value=len(small_components),
                    threshold=small_component_limit,
                    message=(
                        f"region {region_id} has {len(small_components)} tiny detached component(s); "
                        "merge them or give them clear geographic meaning"
                    ),
                )
            )

        main_component = components[0]
        fill_ratio = component_fill_ratio(main_component)
        if (
            region_type(region_id) == "normal"
            and main_component.size >= blocky_area_threshold
            and fill_ratio >= blocky_fill_threshold
        ):
            issues.append(
                AuditIssue(
                    map_id=map_id,
                    code="blocky_region",
                    region_id=region_id,
                    value=round(fill_ratio, 3),
                    threshold=blocky_fill_threshold,
                    message=(
                        f"region {region_id} main component fills {fill_ratio:.1%} of its bounding box; "
                        "add coves, foothills, river bends, or edge interlocks"
                    ),
                )
            )

        straight_run = longest_straight_boundary_run(region_rows, region_id)
        if region_type(region_id) == "normal" and straight_run >= straight_edge_threshold:
            issues.append(
                AuditIssue(
                    map_id=map_id,
                    code="long_straight_boundary",
                    region_id=region_id,
                    value=straight_run,
                    threshold=straight_edge_threshold,
                    message=(
                        f"region {region_id} has a straight boundary run of {straight_run}; "
                        "break it up unless it is an intentional map edge"
                    ),
                )
            )
    return issues


def audit_tile_components(
    map_id: str,
    tile_rows: list[list[str]],
    *,
    small_component_limit: int = DEFAULT_SMALL_COMPONENT_LIMIT,
) -> list[AuditIssue]:
    issues: list[AuditIssue] = []
    for tile_name in ("water", "sea"):
        components = collect_components(coords_by_tile(tile_rows, {tile_name}))
        tiny = [component for component in components if component.size <= small_component_limit]
        if tiny:
            issues.append(
                AuditIssue(
                    map_id=map_id,
                    code=f"tiny_{tile_name}_component",
                    value=len(tiny),
                    threshold=small_component_limit,
                    message=(
                        f"{tile_name} has {len(tiny)} tiny component(s); "
                        "remove isolated specks or reshape them as coves, islands, or channels"
                    ),
                )
            )
    return issues


def audit_water_region(
    map_id: str,
    region_rows: list[list[int]],
) -> list[AuditIssue]:
    water_coords = coords_by_region(region_rows).get(WATER_REGION_ID, set())
    if not water_coords:
        return [
            AuditIssue(
                map_id=map_id,
                code="missing_water_region",
                region_id=WATER_REGION_ID,
                message="water region 106 is missing from the map",
            )
        ]

    issues: list[AuditIssue] = []
    components = collect_components(water_coords)
    if map_id in {"classic", "mountain_frontier"} and len(components) != 1:
        issues.append(
            AuditIssue(
                map_id=map_id,
                code="disconnected_water_region",
                region_id=WATER_REGION_ID,
                value=len(components),
                threshold=1,
                message=(
                    f"region 106 has {len(components)} components; "
                    "classic and mountain_frontier should read as one continuous river"
                ),
            )
        )

    if map_id in {"classic", "mountain_frontier"}:
        sea_touch_edges = count_region_touch_edges(region_rows, WATER_REGION_ID, SEA_REGION_ID)
        if sea_touch_edges == 0:
            issues.append(
                AuditIssue(
                    map_id=map_id,
                    code="water_region_no_sea_outlet",
                    region_id=WATER_REGION_ID,
                    value=0,
                    threshold=">0",
                    message="region 106 does not touch region 105; add a clear river mouth or sea outlet",
                )
            )
    return issues


def audit_map_identity(map_id: str, source, tile_rows: list[list[str]]) -> list[AuditIssue]:
    issues: list[AuditIssue] = []
    sea_fraction = tile_fraction(tile_rows, {"sea"})
    water_fraction = tile_fraction(tile_rows, {"water"})
    mountain_fraction = tile_fraction(tile_rows, MOUNTAIN_IDENTITY_TILES)
    land_components = collect_components(
        coords_by_tile_predicate(tile_rows, lambda tile_name: tile_name not in {"sea", "water"})
    )
    land_component_count = len(land_components)

    if map_id == "classic":
        if str(source.wilderness_tile).lower() == "sea":
            issues.append(
                AuditIssue(
                    map_id=map_id,
                    code="map_identity_drift",
                    value=source.wilderness_tile,
                    threshold="not sea",
                    message="classic should remain a continental map, not a sea-wilderness archipelago",
                )
            )
        if not 0.12 <= sea_fraction <= 0.35:
            issues.append(
                AuditIssue(
                    map_id=map_id,
                    code="map_identity_drift",
                    value=round(sea_fraction, 3),
                    threshold="0.12..0.35",
                    message="classic should keep an eastern sea without becoming an island map",
                )
            )
        if water_fraction < 0.02:
            issues.append(
                AuditIssue(
                    map_id=map_id,
                    code="map_identity_drift",
                    value=round(water_fraction, 3),
                    threshold=">=0.02",
                    message="classic should keep a readable main river as part of its central continent identity",
                )
            )

    if map_id == "island_seas":
        if str(source.wilderness_tile).lower() != "sea":
            issues.append(
                AuditIssue(
                    map_id=map_id,
                    code="map_identity_drift",
                    value=source.wilderness_tile,
                    threshold="sea",
                    message="island_seas should keep open sea wilderness as its base",
                )
            )
        if sea_fraction < 0.50:
            issues.append(
                AuditIssue(
                    map_id=map_id,
                    code="map_identity_drift",
                    value=round(sea_fraction, 3),
                    threshold=">=0.50",
                    message="island_seas should remain an open archipelago with sea as the dominant visual mass",
                )
            )
        if land_component_count < 8:
            issues.append(
                AuditIssue(
                    map_id=map_id,
                    code="map_identity_drift",
                    value=land_component_count,
                    threshold=">=8",
                    message="island_seas should keep multiple separate islands instead of merging into one continent",
                )
            )

    if map_id == "mountain_frontier":
        if str(source.wilderness_tile).lower() == "sea":
            issues.append(
                AuditIssue(
                    map_id=map_id,
                    code="map_identity_drift",
                    value=source.wilderness_tile,
                    threshold="not sea",
                    message="mountain_frontier should remain a land frontier, not a sea-wilderness map",
                )
            )
        if mountain_fraction < 0.25:
            issues.append(
                AuditIssue(
                    map_id=map_id,
                    code="map_identity_drift",
                    value=round(mountain_fraction, 3),
                    threshold=">=0.25",
                    message="mountain_frontier should keep mountain, snow, volcanic, cave, ruin, and tundra terrain as its dominant identity",
                )
            )
        if water_fraction < 0.025:
            issues.append(
                AuditIssue(
                    map_id=map_id,
                    code="map_identity_drift",
                    value=round(water_fraction, 3),
                    threshold=">=0.025",
                    message="mountain_frontier should keep a visible gorge river through the mountain belt",
                )
            )

    return issues


def audit_landmarks(
    map_id: str,
    region_rows: list[list[int]],
    landmarks: dict[int, object],
    *,
    edge_distance_threshold: int = DEFAULT_LANDMARK_EDGE_DISTANCE,
) -> list[AuditIssue]:
    issues: list[AuditIssue] = []
    by_region = coords_by_region(region_rows)
    height = len(region_rows)
    width = len(region_rows[0]) if height else 0
    for region_id, landmark in sorted(landmarks.items()):
        coords = by_region.get(int(region_id), set())
        anchor = (int(landmark.x), int(landmark.y))
        if not coords or anchor not in coords:
            continue

        covered = [
            (anchor[0], anchor[1]),
            (anchor[0] + 1, anchor[1]),
            (anchor[0], anchor[1] + 1),
            (anchor[0] + 1, anchor[1] + 1),
        ]
        in_region = sum(1 for coord in covered if coord in coords)
        in_bounds = sum(1 for x, y in covered if 0 <= x < width and 0 <= y < height)
        if in_bounds < 4 or in_region < 3:
            issues.append(
                AuditIssue(
                    map_id=map_id,
                    code="landmark_poor_fit",
                    region_id=int(region_id),
                    value=in_region,
                    threshold=3,
                    message=(
                        f"landmark for region {region_id} only covers {in_region}/4 tiles in its region; "
                        "move the landmark or enlarge its local region"
                    ),
                )
            )

        distance = boundary_distance(coords, anchor)
        if distance <= edge_distance_threshold:
            issues.append(
                AuditIssue(
                    map_id=map_id,
                    code="landmark_near_boundary",
                    region_id=int(region_id),
                    value=distance,
                    threshold=edge_distance_threshold,
                    message=(
                        f"landmark for region {region_id} is {distance} tile(s) from the region edge; "
                        "consider moving it inward if the visual marker feels cramped"
                    ),
                )
            )
    return issues


def audit_map_source(map_id: str, source) -> list[AuditIssue]:
    tile_rows = derive_tile_rows_from_region_rows(
        source.region_rows,
        wilderness_tile=source.wilderness_tile,
    )
    issues: list[AuditIssue] = []
    issues.extend(audit_region_components(map_id, source.region_rows))
    issues.extend(audit_tile_components(map_id, tile_rows))
    issues.extend(audit_water_region(map_id, source.region_rows))
    issues.extend(audit_map_identity(map_id, source, tile_rows))
    issues.extend(audit_landmarks(map_id, source.region_rows, source.landmarks))
    return issues


def audit_presets(map_ids: list[str] | None = None) -> list[AuditIssue]:
    if map_ids:
        presets = [get_map_preset(map_id) for map_id in map_ids]
    else:
        presets = list_map_presets()

    issues: list[AuditIssue] = []
    for preset in presets:
        if preset.path is None:
            continue
        source = read_map_source(preset.path / "map.json")
        issues.extend(audit_map_source(preset.id, source))
    return issues


def format_issues(issues: list[AuditIssue]) -> str:
    if not issues:
        return "No map quality warnings."
    lines = [f"Map quality warnings: {len(issues)}"]
    for issue in issues:
        region = f" region={issue.region_id}" if issue.region_id is not None else ""
        metric = ""
        if issue.value is not None:
            metric = f" value={issue.value}"
        if issue.threshold is not None:
            metric = f"{metric} threshold={issue.threshold}"
        lines.append(f"- [{issue.map_id}] {issue.code}{region}{metric}: {issue.message}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit official map preset visual quality.")
    parser.add_argument("--map-id", action="append", default=None, help="Map id to audit. Can be repeated.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when warnings are found.")
    args = parser.parse_args()

    issues = audit_presets(args.map_id)
    if args.json:
        print(json.dumps([issue.to_dict() for issue in issues], ensure_ascii=False, indent=2))
    else:
        print(format_issues(issues))
    if args.strict and issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
