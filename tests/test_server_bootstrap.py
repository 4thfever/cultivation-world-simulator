from __future__ import annotations

import os
import sys

from src.server.bootstrap import (
    is_browser_auto_open_disabled,
    prepare_browser_target,
    resolve_runtime_paths,
    resolve_server_binding,
)
from src.server.encoding_runtime import (
    build_utf8_subprocess_env,
    configure_process_encoding,
    patch_standard_streams,
)


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


def test_resolve_server_binding_auto_avoids_port_when_not_explicit(monkeypatch):
    monkeypatch.delenv("SERVER_PORT", raising=False)
    monkeypatch.setenv("SERVER_HOST", "127.0.0.1")
    monkeypatch.setattr("src.server.bootstrap.get_free_port", lambda start_port, max_port=65535: 8007)

    assert resolve_server_binding() == ("127.0.0.1", 8007)


def test_resolve_server_binding_does_not_auto_shift_explicit_port(monkeypatch):
    monkeypatch.setenv("SERVER_PORT", "9009")
    monkeypatch.setattr("src.server.bootstrap.get_free_port", lambda *_args, **_kwargs: 8010)

    assert resolve_server_binding() == ("127.0.0.1", 9009)


def test_browser_auto_open_disabled_env(monkeypatch):
    monkeypatch.setenv("CWS_NO_BROWSER", "true")

    assert is_browser_auto_open_disabled() is True


def test_prepare_browser_target_keeps_backend_url_when_not_dev(monkeypatch):
    monkeypatch.delenv("VITE_PORT", raising=False)

    assert prepare_browser_target(is_dev_mode=False, host="127.0.0.1", port=8002) == "http://127.0.0.1:8002"


def test_prepare_browser_target_sets_vite_port_in_dev(monkeypatch):
    monkeypatch.setattr("src.server.bootstrap.get_free_port", lambda _start_port: 5179)
    monkeypatch.delenv("VITE_PORT", raising=False)

    target = prepare_browser_target(is_dev_mode=True, host="127.0.0.1", port=8002)

    assert target == "http://localhost:5179"
    assert os.environ["VITE_PORT"] == "5179"


def test_utf8_subprocess_env_preserves_explicit_overrides():
    env = build_utf8_subprocess_env(
        base_env={"PYTHONUTF8": "0", "EXISTING": "yes"},
        overrides={"SERVER_PORT": "54321"},
    )

    assert env["PYTHONUTF8"] == "0"
    assert env["PYTHONIOENCODING"] == "utf-8"
    assert env["SERVER_PORT"] == "54321"
    assert env["EXISTING"] == "yes"


def test_configure_process_encoding_sets_utf8_env(monkeypatch):
    monkeypatch.delenv("PYTHONUTF8", raising=False)
    monkeypatch.delenv("PYTHONIOENCODING", raising=False)

    configure_process_encoding()

    assert os.environ["PYTHONUTF8"] == "1"
    assert os.environ["PYTHONIOENCODING"] == "utf-8"


def test_patch_standard_streams_installs_dummy_for_missing_stdout(monkeypatch):
    original_stdout = sys.stdout
    monkeypatch.setattr(sys, "stdout", None)

    patch_standard_streams()

    assert sys.stdout is not None
    assert sys.stdout.encoding == "utf-8"
    assert sys.stdout.write("中文 output") == 0
    monkeypatch.setattr(sys, "stdout", original_stdout)


def test_start_frontend_dev_server_passes_utf8_env(monkeypatch, tmp_path):
    from src.server.dev_runtime import start_frontend_dev_server

    web_dir = tmp_path / "web"
    web_dir.mkdir()
    calls = []

    class DummyProcess:
        pass

    def fake_popen(*args, **kwargs):
        calls.append((args, kwargs))
        return DummyProcess()

    monkeypatch.setattr("src.server.dev_runtime.platform.system", lambda: "Linux")
    monkeypatch.setattr("src.server.dev_runtime.subprocess.Popen", fake_popen)
    monkeypatch.delenv("PYTHONUTF8", raising=False)
    monkeypatch.delenv("PYTHONIOENCODING", raising=False)

    process = start_frontend_dev_server(project_root=str(tmp_path))

    assert isinstance(process, DummyProcess)
    assert calls
    env = calls[0][1]["env"]
    assert calls[0][1]["cwd"] == str(web_dir)
    assert env["PYTHONUTF8"] == "1"
    assert env["PYTHONIOENCODING"] == "utf-8"
