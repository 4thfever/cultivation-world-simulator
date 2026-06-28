from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class FalImageConfig:
    api_key: str
    model: str = "openai/gpt-image-2"
    image_size: str | dict[str, int] = "square_hd"
    quality: str = "low"
    output_format: str = "png"
    queue_base_url: str = "https://queue.fal.run"


class FalApiError(RuntimeError):
    def __init__(self, status_code: int | None, message: str):
        self.status_code = status_code
        super().__init__(message)


def _load_json_response(request: urllib.request.Request, *, timeout: int = 180) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        try:
            payload = exc.read().decode("utf-8", errors="replace")
        except Exception:
            payload = ""
        message = payload or exc.reason or f"HTTP {exc.code}"
        raise FalApiError(exc.code, message) from exc
    except urllib.error.URLError as exc:
        raise FalApiError(None, str(exc.reason)) from exc

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise FalApiError(None, f"fal returned non-JSON response: {raw[:200]}") from exc


def _request_json(
    url: str,
    *,
    api_key: str,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    timeout: int = 180,
) -> dict[str, Any]:
    data = None
    headers = {"Authorization": f"Key {api_key}"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    return _load_json_response(request, timeout=timeout)


def submit_generation(prompt: str, *, config: FalImageConfig) -> dict[str, Any]:
    endpoint = f"{config.queue_base_url.rstrip('/')}/{config.model}"
    payload = {
        "prompt": prompt,
        "image_size": config.image_size,
        "quality": config.quality,
        "num_images": 1,
        "output_format": config.output_format,
    }
    return _request_json(endpoint, api_key=config.api_key, method="POST", payload=payload)


def wait_for_result(
    submit_response: dict[str, Any],
    *,
    api_key: str,
    poll_interval: float = 4.0,
    timeout_seconds: int = 600,
) -> dict[str, Any]:
    status_url = str(submit_response.get("status_url") or "")
    response_url = str(submit_response.get("response_url") or "")
    if not status_url or not response_url:
        if "images" in submit_response:
            return submit_response
        raise FalApiError(None, f"fal submit response missing status/response URLs: {submit_response}")

    deadline = time.time() + timeout_seconds
    last_status = ""
    while time.time() < deadline:
        status = _request_json(f"{status_url}?logs=1", api_key=api_key)
        current = str(status.get("status") or "")
        if current != last_status:
            print(f"fal status: {current or 'UNKNOWN'}")
            last_status = current
        if current == "COMPLETED":
            if status.get("error"):
                raise FalApiError(None, str(status.get("error")))
            return _request_json(response_url, api_key=api_key)
        time.sleep(poll_interval)

    raise FalApiError(None, "fal request timed out before completion")


def download_image(url: str, output_path: str | Path, *, timeout: int = 180) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "cultivation-world-simulator-tools/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            output.write_bytes(response.read())
    except urllib.error.URLError as exc:
        raise FalApiError(None, str(exc.reason)) from exc
    return output


def generate_to_file(prompt: str, output_path: str | Path, *, config: FalImageConfig) -> dict[str, Any]:
    submitted = submit_generation(prompt, config=config)
    result = wait_for_result(submitted, api_key=config.api_key)
    images = result.get("images") or []
    if not images:
        raise FalApiError(None, f"fal result has no images: {result}")
    image_url = str(images[0].get("url") or "")
    if not image_url:
        raise FalApiError(None, f"fal image result missing URL: {images[0]}")
    saved = download_image(image_url, output_path)
    return {
        "request_id": submitted.get("request_id"),
        "image_url": image_url,
        "output": str(saved),
        "result": result,
    }
