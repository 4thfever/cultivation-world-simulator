from __future__ import annotations

from fastapi import HTTPException


def set_world_phenomenon(runtime, *, phenomenon_id: int, celestial_phenomena_by_id) -> dict[str, str]:
    world = runtime.get("world")
    if not world:
        raise HTTPException(status_code=503, detail="World not initialized")

    phenomenon = celestial_phenomena_by_id.get(phenomenon_id)
    if not phenomenon:
        raise HTTPException(status_code=404, detail="Phenomenon not found")

    world.current_phenomenon = phenomenon
    try:
        world.phenomenon_start_year = int(world.month_stamp.get_year())
    except Exception:
        pass

    return {"status": "ok", "message": f"Phenomenon set to {phenomenon.name}"}
