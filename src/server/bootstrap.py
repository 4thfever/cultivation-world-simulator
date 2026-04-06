from __future__ import annotations

import os
import socket


def resolve_runtime_paths(*, server_file: str, is_frozen: bool, executable: str | None = None, meipass: str | None = None) -> tuple[str, str]:
    """Resolve web dist and assets paths for dev and packaged runtime."""
    if is_frozen:
        if not executable or not meipass:
            raise ValueError("Frozen runtime requires executable and meipass")
        exe_dir = os.path.dirname(executable)
        web_dist_path = os.path.join(exe_dir, "web_static")
        assets_path = os.path.join(meipass, "assets")
    else:
        base_path = os.path.join(os.path.dirname(server_file), "..", "..")
        web_dist_path = os.path.join(base_path, "web", "dist")
        assets_path = os.path.join(base_path, "assets")

    return os.path.abspath(web_dist_path), os.path.abspath(assets_path)


def resolve_server_binding() -> tuple[str, int]:
    host = os.environ.get("SERVER_HOST") or "127.0.0.1"
    port = int(os.environ.get("SERVER_PORT") or 8002)
    return host, port


def get_free_port(start_port: int, max_port: int = 65535) -> int:
    for port in range(start_port, max_port + 1):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(("", port))
            sock.close()
            return port
        except OSError:
            pass
    return start_port


def prepare_browser_target(*, is_dev_mode: bool, host: str, port: int) -> str:
    target_url = f"http://{host}:{port}"
    if not is_dev_mode:
        return target_url

    free_port = get_free_port(5173)
    os.environ["VITE_PORT"] = str(free_port)
    print(f"[Debug] Detected free port for Vite: {free_port}")
    target_url = f"http://localhost:{free_port}"
    print(f"[Debug] Target URL set to: {target_url}")
    return target_url
