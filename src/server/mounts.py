from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


def mount_static_apps(
    app: FastAPI,
    *,
    assets_path: str,
    web_dist_path: str,
    is_dev_mode: bool,
) -> None:
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")
    else:
        print(f"Warning: Assets path not found: {assets_path}")

    if is_dev_mode:
        print("Dev Mode: Skipping static file mount for '/' (using Vite dev server instead)")
        return

    if os.path.exists(web_dist_path):
        print(f"Serving Web UI from: {web_dist_path}")
        app.mount("/", StaticFiles(directory=web_dist_path, html=True), name="web_dist")
    else:
        print(f"Warning: Web dist path not found: {web_dist_path}.")
