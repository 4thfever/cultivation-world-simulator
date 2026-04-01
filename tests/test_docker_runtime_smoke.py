import json
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def run_compose(*args: str, timeout: int = 300) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["docker", "compose", *args],
        cwd=get_project_root(),
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def http_json(url: str, method: str = "GET", payload: dict | None = None) -> dict:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url=url, method=method, data=data, headers=headers)
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def wait_until_backend_ready(timeout_seconds: int = 120) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            payload = http_json("http://localhost:8002/api/state")
            if isinstance(payload, dict) and "status" in payload:
                return
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            pass
        time.sleep(2)
    raise AssertionError("Backend /api/state did not become ready in time.")


@pytest.mark.docker
@pytest.mark.skipif(shutil.which("docker") is None, reason="docker not found in PATH")
def test_docker_compose_persists_settings_after_recreate():
    try:
        run_compose("up", "-d", "--build", timeout=900)
        wait_until_backend_ready()

        updated = http_json(
            "http://localhost:8002/api/settings",
            method="PATCH",
            payload={"simulation": {"auto_save_enabled": True}},
        )
        assert updated["simulation"]["auto_save_enabled"] is True

        run_compose("down", timeout=180)
        run_compose("up", "-d", timeout=600)
        wait_until_backend_ready()

        after_recreate = http_json("http://localhost:8002/api/settings")
        assert after_recreate["simulation"]["auto_save_enabled"] is True
    finally:
        subprocess.run(
            ["docker", "compose", "down"],
            cwd=get_project_root(),
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
