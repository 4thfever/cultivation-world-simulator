from __future__ import annotations

from fastapi import HTTPException
from src.i18n import t


def set_world_phenomenon(runtime, *, phenomenon_id: int, celestial_phenomena_by_id) -> dict[str, str]:
    world = runtime.get("world")
    if not world:
        raise HTTPException(status_code=503, detail=t("World not initialized"))

    phenomenon = celestial_phenomena_by_id.get(phenomenon_id)
    if not phenomenon:
        raise HTTPException(status_code=404, detail=t("Phenomenon not found"))

    world.current_phenomenon = phenomenon
    try:
        world.phenomenon_start_year = int(world.month_stamp.get_year())
    except Exception:
        pass

    return {"status": "ok", "message": t("Phenomenon set to {phenomenon_name}", phenomenon_name=phenomenon.name)}
