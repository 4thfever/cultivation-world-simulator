from __future__ import annotations

import os

from src.config import get_settings_service
from src.sim import get_events_db_path, list_saves, save_game


def trigger_auto_save(*, world, sim, sects_by_id) -> None:
    """Create the next auto save and keep only the latest configured snapshots."""
    playthrough_id = getattr(world, "playthrough_id", "")
    max_auto_saves = get_settings_service().get_settings().simulation.max_auto_saves

    auto_saves = [
        (path, meta)
        for path, meta in list_saves()
        if meta.get("is_auto_save", False) and meta.get("playthrough_id", "") == playthrough_id
    ]

    while len(auto_saves) >= max_auto_saves:
        oldest_path, _oldest_meta = auto_saves.pop()
        if not oldest_path.exists():
            continue
        try:
            os.remove(oldest_path)
            db_path = get_events_db_path(oldest_path)
            if db_path.exists():
                os.remove(db_path)
            print(f"[Auto-Save] Removed old auto save: {oldest_path.name}")
        except Exception as exc:
            print(f"[Auto-Save] Failed to remove old auto save: {exc}")

    existed_sects = getattr(world, "existed_sects", []) or list(sects_by_id.values())
    save_game(world, sim, existed_sects, is_auto_save=True)
