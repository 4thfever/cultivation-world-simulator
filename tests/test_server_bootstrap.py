from __future__ import annotations

import os

from src.server.bootstrap import prepare_browser_target, resolve_runtime_paths, resolve_server_binding


def test_resolve_runtime_paths_for_dev_mode():
    web_dist_path, assets_path = resolve_runtime_paths(
        server_file=r"e:\projects\cultivation-world-simulator\src\server\main.py",
        is_frozen=False,
    )

    assert web_dist_path.endswith(os.path.join("web", "dist"))
    assert assets_path.endswith("assets")


def test_resolve_runtime_paths_for_frozen_mode(tmp_path):
    app_dir = tmp_path / "app"
    executable = app_dir / "cultivation-world-simulator.exe"
    meipass = app_dir / "_internal"

    web_dist_path, assets_path = resolve_runtime_paths(
        server_file="ignored",
        is_frozen=True,
        executable=str(executable),
        meipass=str(meipass),
    )

    assert web_dist_path == os.path.abspath(str(app_dir / "web_static"))
    assert assets_path == os.path.abspath(str(meipass / "assets"))


def test_resolve_server_binding_uses_env_values(monkeypatch):
    monkeypatch.setenv("SERVER_HOST", "0.0.0.0")
    monkeypatch.setenv("SERVER_PORT", "9001")

    assert resolve_server_binding() == ("0.0.0.0", 9001)


def test_prepare_browser_target_keeps_backend_url_when_not_dev(monkeypatch):
    monkeypatch.delenv("VITE_PORT", raising=False)

    assert prepare_browser_target(is_dev_mode=False, host="127.0.0.1", port=8002) == "http://127.0.0.1:8002"


def test_prepare_browser_target_sets_vite_port_in_dev(monkeypatch):
    monkeypatch.setattr("src.server.bootstrap.get_free_port", lambda _start_port: 5179)
    monkeypatch.delenv("VITE_PORT", raising=False)

    target = prepare_browser_target(is_dev_mode=True, host="127.0.0.1", port=8002)

    assert target == "http://localhost:5179"
    assert os.environ["VITE_PORT"] == "5179"
