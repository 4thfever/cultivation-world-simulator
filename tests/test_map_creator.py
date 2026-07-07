import json

import pytest


pytest.importorskip("flask")

from tools.map_creator import main as map_creator


def _write_map(root, map_id, *, width=84, height=60, region_id=101):
    preset_dir = root / map_id
    preset_dir.mkdir(parents=True)
    payload = {
        "schema_version": 2,
        "id": map_id,
        "version": 7,
        "width": width,
        "height": height,
        "wilderness_tile": "plain",
        "region_rows": [[region_id for _ in range(width)] for _ in range(height)],
        "landmarks": {"301": {"x": 1, "y": 2, "asset": "city_301"}},
        "region_overrides": {"101": {"name": "测试平原"}},
    }
    (preset_dir / "map.json").write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )
    return payload


def test_map_creator_save_payload_preserves_existing_size_and_metadata(tmp_path, monkeypatch):
    maps_dir = tmp_path / "maps"
    _write_map(maps_dir, "island_seas", width=84, height=60)
    monkeypatch.setattr(map_creator, "MAPS_DIR", str(maps_dir))

    payload = map_creator.build_map_payload(
        {
            "mapId": "island_seas",
            "grid": [
                {"x": 0, "y": 0, "r": 102},
                {"x": 83, "y": 59, "r": 105},
                {"x": 84, "y": 60, "r": 999},
            ],
            "wildernessTile": "sea",
        }
    )

    assert payload["id"] == "island_seas"
    assert payload["version"] == 7
    assert payload["width"] == 84
    assert payload["height"] == 60
    assert len(payload["region_rows"]) == 60
    assert all(len(row) == 84 for row in payload["region_rows"])
    assert payload["region_rows"][0][0] == 102
    assert payload["region_rows"][59][83] == 105
    assert payload["landmarks"] == {"301": {"x": 1, "y": 2, "asset": "city_301"}}
    assert payload["region_overrides"] == {"101": {"name": "测试平原"}}
    assert payload["wilderness_tile"] == "sea"


def test_map_creator_save_payload_uses_request_size_for_known_map(tmp_path, monkeypatch):
    maps_dir = tmp_path / "maps"
    _write_map(maps_dir, "classic", width=84, height=60)
    monkeypatch.setattr(map_creator, "MAPS_DIR", str(maps_dir))

    payload = map_creator.build_map_payload(
        {
            "mapId": "classic",
            "width": 12,
            "height": 8,
            "grid": [{"x": 11, "y": 7, "r": 118}],
            "landmarks": {},
            "regionOverrides": {},
        }
    )

    assert payload["width"] == 12
    assert payload["height"] == 8
    assert len(payload["region_rows"]) == 8
    assert all(len(row) == 12 for row in payload["region_rows"])
    assert payload["region_rows"][7][11] == 118


def test_map_creator_rejects_unknown_map_without_explicit_create(tmp_path, monkeypatch):
    monkeypatch.setattr(map_creator, "MAPS_DIR", str(tmp_path / "maps"))

    with pytest.raises(ValueError, match="Unknown map preset"):
        map_creator.build_map_payload({"mapId": "new_world", "grid": []})


def test_map_creator_loads_requested_map_id(tmp_path, monkeypatch):
    maps_dir = tmp_path / "maps"
    _write_map(maps_dir, "classic", width=84, height=60, region_id=101)
    _write_map(maps_dir, "mountain_frontier", width=10, height=6, region_id=107)
    monkeypatch.setattr(map_creator, "MAPS_DIR", str(maps_dir))
    monkeypatch.setattr(
        map_creator,
        "load_region_tile_bindings",
        lambda: {107: {"tile": "mountain", "landmarkAsset": None}},
    )

    loaded = map_creator.load_map_data("mountain_frontier")

    assert loaded["mapId"] == "mountain_frontier"
    assert loaded["width"] == 10
    assert loaded["height"] == 6
    assert loaded["cells"]["0,0"] == {"t": "mountain", "r": 107}


def test_map_creator_rejects_path_like_map_id():
    with pytest.raises(ValueError, match="Invalid map id"):
        map_creator.normalize_map_id("../classic")
