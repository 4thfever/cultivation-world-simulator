from __future__ import annotations

from src.server.services.public_api_contract import raise_public_error


def cleanup_events(
    runtime,
    *,
    keep_major: bool = True,
    before_month_stamp: int | None = None,
) -> dict[str, int]:
    world = runtime.get("world")
    if world is None:
        raise_public_error(
            status_code=503,
            code="WORLD_NOT_READY",
            message="World not initialized",
        )

    event_manager = getattr(world, "event_manager", None)
    if event_manager is None:
        raise_public_error(
            status_code=503,
            code="EVENTS_NOT_READY",
            message="Event manager not initialized",
        )

    deleted = event_manager.cleanup(
        keep_major=keep_major,
        before_month_stamp=before_month_stamp,
    )
    return {"deleted": deleted}
