from __future__ import annotations

import os
import platform
import subprocess


def start_frontend_dev_server(*, project_root: str):
    """Start the Vite dev server in dev mode and return the spawned process."""
    web_dir = os.path.join(project_root, "web")
    print(f"Starting frontend dev server (npm run dev) at: {web_dir}")

    vite_port = os.environ.get("VITE_PORT", "5173")
    if platform.system() == "Windows":
        cmd = f"npx vite --port {vite_port} --strictPort"
        return subprocess.Popen(cmd, cwd=web_dir, shell=True)
    return subprocess.Popen(
        ["npx", "vite", "--port", vite_port, "--strictPort"],
        cwd=web_dir,
        shell=False,
    )


def stop_frontend_dev_server(process) -> None:
    """Terminate the spawned Vite dev server process."""
    if not process:
        return

    print("Closing frontend dev server...")
    try:
        if platform.system() == "Windows":
            subprocess.call(["taskkill", "/F", "/T", "/PID", str(process.pid)])
        else:
            process.terminate()
    except Exception as exc:
        print(f"Error closing frontend server: {exc}")
