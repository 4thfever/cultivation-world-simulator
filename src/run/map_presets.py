from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.utils.config import CONFIG
from src.i18n import t


DEFAULT_MAP_ID = "classic"
MAPS_DIR = CONFIG.paths.game_configs / "maps"


@dataclass(frozen=True)
class MapPreset:
    id: str
    name: str
    desc: str
    size_label: str = ""
    version: int = 1
    is_default: bool = False
    path: Path | None = None
    name_id: str = ""
    desc_id: str = ""
    size_label_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": t(self.name_id) if self.name_id else self.name,
            "desc": t(self.desc_id) if self.desc_id else self.desc,
            "size_label": t(self.size_label_id) if self.size_label_id else self.size_label,
            "version": self.version,
            "is_default": self.is_default,
        }

    @property
    def localized_name(self) -> str:
        return t(self.name_id) if self.name_id else self.name

    @property
    def localized_desc(self) -> str:
        return t(self.desc_id) if self.desc_id else self.desc


def _read_meta(preset_dir: Path) -> MapPreset:
    meta_path = preset_dir / "meta.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"Map preset meta not found: {meta_path}")

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    preset_id = str(meta.get("id") or preset_dir.name)
    if preset_id != preset_dir.name:
        raise ValueError(f"Map preset id mismatch: {preset_id} != {preset_dir.name}")

    return MapPreset(
        id=preset_id,
        name=str(meta.get("name") or preset_id),
        desc=str(meta.get("desc") or ""),
        size_label=str(meta.get("size_label") or ""),
        version=int(meta.get("version", 1) or 1),
        is_default=bool(meta.get("is_default", preset_id == DEFAULT_MAP_ID)),
        path=preset_dir,
        name_id=str(meta.get("name_id") or ""),
        desc_id=str(meta.get("desc_id") or ""),
        size_label_id=str(meta.get("size_label_id") or ""),
    )


def list_map_presets() -> list[MapPreset]:
    if not MAPS_DIR.exists():
        return []

    presets: list[MapPreset] = []
    for preset_dir in sorted(p for p in MAPS_DIR.iterdir() if p.is_dir()):
        presets.append(_read_meta(preset_dir))

    presets.sort(key=lambda p: (not p.is_default, p.id))
    return presets


def get_map_preset(map_id: str | None = None) -> MapPreset:
    target_id = map_id or DEFAULT_MAP_ID
    presets = {preset.id: preset for preset in list_map_presets()}
    if target_id in presets:
        return presets[target_id]

    raise ValueError(f"Unknown map preset: {target_id}")


def resolve_map_source_file(map_id: str | None = None) -> tuple[MapPreset, Path]:
    preset = get_map_preset(map_id)
    preset_path = preset.path or (MAPS_DIR / preset.id)
    source_path = preset_path / "map.json"
    if not source_path.exists():
        raise FileNotFoundError(f"Map source file not found for preset {preset.id}: {source_path}")
    return preset, source_path


def get_map_presets_query() -> dict[str, list[dict[str, Any]]]:
    return {"maps": [preset.to_dict() for preset in list_map_presets()]}
