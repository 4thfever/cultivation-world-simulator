from __future__ import annotations

import base64
import json
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

from tools.item_icons.config import ItemIconConfig, load_config

T = TypeVar("T")
RETRY_STATUS_CODES = {408, 409, 429, 500, 502, 503, 504}


class ImageApiError(RuntimeError):
    def __init__(self, status_code: int | None, message: str):
        self.status_code = status_code
        super().__init__(message)


def _with_retries(
    operation: Callable[[], T],
    *,
    max_retries: int = 3,
    retry_delay: float = 5.0,
) -> T:
    attempt = 0
    while True:
        try:
            return operation()
        except ImageApiError as exc:
            retryable = exc.status_code in RETRY_STATUS_CODES if exc.status_code else True
            if attempt >= max_retries or not retryable:
                raise
            delay = retry_delay * (2**attempt)
            print(f"图像 API 请求失败，{delay:.1f}s 后重试 ({attempt + 1}/{max_retries})")
            time.sleep(delay)
            attempt += 1


def _read_error_body(error: urllib.error.HTTPError) -> str:
    try:
        payload = error.read().decode("utf-8", errors="replace")
    except Exception:
        payload = ""
    if not payload:
        return error.reason or f"HTTP {error.code}"
    try:
        body = json.loads(payload)
    except json.JSONDecodeError:
        return payload
    detail = body.get("error", body)
    if isinstance(detail, dict):
        return str(detail.get("message") or detail)
    return str(detail)


def generate_image_b64(
    prompt: str,
    *,
    config: ItemIconConfig | None = None,
    model: str | None = None,
    size: str | None = None,
    n: int = 1,
    max_retries: int = 3,
    retry_delay: float = 5.0,
) -> str:
    resolved = config or load_config()
    endpoint = f"{resolved.base_url}/images/generations"
    payload: dict[str, Any] = {
        "model": model or resolved.model,
        "prompt": prompt,
        "n": n,
        "size": size or resolved.size,
    }

    def request_generation() -> str:
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {resolved.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise ImageApiError(exc.code, _read_error_body(exc)) from exc
        except urllib.error.URLError as exc:
            raise ImageApiError(None, str(exc.reason)) from exc

        data = body.get("data")
        if not data:
            raise ImageApiError(None, "响应中没有 data 图片数组")
        image_b64 = data[0].get("b64_json") or data[0].get("b64")
        if not image_b64:
            raise ImageApiError(None, "响应中没有 b64_json 图片数据")
        return str(image_b64)

    return _with_retries(
        request_generation,
        max_retries=max_retries,
        retry_delay=retry_delay,
    )


def generate_image_bytes(
    prompt: str,
    *,
    config: ItemIconConfig | None = None,
    model: str | None = None,
    size: str | None = None,
    max_retries: int = 3,
    retry_delay: float = 5.0,
) -> bytes:
    image_b64 = generate_image_b64(
        prompt,
        config=config,
        model=model,
        size=size,
        max_retries=max_retries,
        retry_delay=retry_delay,
    )
    return base64.b64decode(image_b64)


def save_generated_image(
    prompt: str,
    output_path: str | Path,
    *,
    config: ItemIconConfig | None = None,
    model: str | None = None,
    size: str | None = None,
    max_retries: int = 3,
    retry_delay: float = 5.0,
) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(
        generate_image_bytes(
            prompt,
            config=config,
            model=model,
            size=size,
            max_retries=max_retries,
            retry_delay=retry_delay,
        )
    )
    return output
