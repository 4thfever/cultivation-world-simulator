from dataclasses import dataclass

from tools.map_presets.quality_audit import (
    audit_landmarks,
    audit_region_components,
    audit_tile_components,
    audit_water_region,
    collect_components,
    format_issues,
)
from tools.map_presets.validate_presets import SOFT_QUALITY_CODES


@dataclass(frozen=True)
class DummyLandmark:
    x: int
    y: int
    asset: str = "city_301"


def _codes(issues):
    return {issue.code for issue in issues}


def test_collect_components_reports_sizes_and_bboxes():
    components = collect_components({(0, 0), (1, 0), (4, 4)})

    assert [component.size for component in components] == [2, 1]
    assert components[0].bbox == (0, 0, 1, 0)
    assert components[1].bbox == (4, 4, 4, 4)


def test_audit_water_region_flags_disconnected_river_on_classic_map():
    rows = [
        [106, 106, 101, 105],
        [101, 101, 101, 105],
        [106, 106, 101, 105],
    ]

    issues = audit_water_region("classic", rows)

    assert "disconnected_water_region" in _codes(issues)


def test_audit_water_region_flags_missing_sea_outlet():
    rows = [
        [106, 106, 101],
        [101, 106, 101],
        [101, 101, 101],
    ]

    issues = audit_water_region("mountain_frontier", rows)

    assert "water_region_no_sea_outlet" in _codes(issues)


def test_audit_tile_components_flags_tiny_water_and_sea_specks():
    rows = [
        ["water", "plain", "sea"],
        ["plain", "plain", "plain"],
        ["sea", "plain", "water"],
    ]

    issues = audit_tile_components("test_map", rows, small_component_limit=1)

    assert "tiny_water_component" in _codes(issues)
    assert "tiny_sea_component" in _codes(issues)


def test_audit_region_components_flags_fragments_blockiness_and_straight_edges():
    rows = [
        [101, 101, 101, 101, 101, 101],
        [101, 101, 101, 101, 101, 101],
        [101, 101, 101, 101, 101, 101],
        [102, 102, 102, 102, 102, 102],
        [102, 102, 102, 102, 102, 102],
        [101, 102, 102, 102, 102, 101],
    ]

    issues = audit_region_components(
        "test_map",
        rows,
        small_component_limit=1,
        blocky_area_threshold=6,
        blocky_fill_threshold=0.75,
        straight_edge_threshold=4,
    )

    assert "small_region_fragments" in _codes(issues)
    assert "blocky_region" in _codes(issues)
    assert "long_straight_boundary" in _codes(issues)


def test_audit_landmarks_flags_poor_fit_and_near_boundary():
    rows = [
        [301, 101, 101],
        [101, 101, 101],
        [101, 101, 101],
    ]
    landmarks = {301: DummyLandmark(0, 0)}

    issues = audit_landmarks("test_map", rows, landmarks, edge_distance_threshold=1)

    assert "landmark_poor_fit" in _codes(issues)
    assert "landmark_near_boundary" in _codes(issues)


def test_format_issues_includes_codes_and_map_ids():
    issues = audit_water_region("classic", [[106], [101], [106]])
    formatted = format_issues(issues)

    assert "classic" in formatted
    assert "disconnected_water_region" in formatted


def test_validate_presets_keeps_only_landmark_edge_warning_soft():
    assert SOFT_QUALITY_CODES == {"landmark_near_boundary"}
