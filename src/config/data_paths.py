from __future__ import annotations

import hashlib
import os
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


APP_NAME = "CultivationWorldSimulator"
DEV_APP_NAME = "CultivationWorldSimulator-dev"


@dataclass(frozen=True)
class DataPaths:
    root: Path
    settings_file: Path
    secrets_file: Path
    saves_dir: Path
    logs_dir: Path
    cache_dir: Path
    incompatible_dir: Path

    def ensure_dirs(self) -> "DataPaths":
        self.root.mkdir(parents=True, exist_ok=True)
        self.saves_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.incompatible_dir.mkdir(parents=True, exist_ok=True)
        return self


def _workspace_hash() -> str:
    raw = os.environ.get("CWS_WORKSPACE_HASH")
    if raw:
        return raw

    cwd = Path.cwd().resolve()
    digest = hashlib.md5(str(cwd).encode("utf-8")).hexdigest()
    return digest[:8]


def _default_data_root() -> Path:
    explicit = os.environ.get("CWS_DATA_DIR")
    if explicit:
        return Path(explicit).expanduser().resolve()

    app_name = APP_NAME if getattr(sys, "frozen", False) else DEV_APP_NAME

    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))

    root = base / app_name
    if app_name == DEV_APP_NAME:
        root = root / _workspace_hash()
    return root


@lru_cache(maxsize=1)
def get_data_paths() -> DataPaths:
    root = _default_data_root()
    return DataPaths(
        root=root,
        settings_file=root / "settings.json",
        secrets_file=root / "secrets.json",
        saves_dir=root / "saves",
        logs_dir=root / "logs",
        cache_dir=root / "cache",
        incompatible_dir=root / "incompatible",
    ).ensure_dirs()


def reset_data_paths_cache() -> None:
    get_data_paths.cache_clear()
