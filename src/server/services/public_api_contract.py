from __future__ import annotations

from typing import Any

from fastapi import HTTPException


def ok_response(data: Any) -> dict[str, Any]:
    return {"ok": True, "data": data}


def raise_public_error(
    *,
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> None:
    raise HTTPException(
        status_code=status_code,
        detail={
            "code": code,
            "message": message,
            "details": details or {},
        },
    )
