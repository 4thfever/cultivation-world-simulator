from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from typing import Any


UTF8_ENV_DEFAULTS = {
    "PYTHONUTF8": "1",
    "PYTHONIOENCODING": "utf-8",
}


class DummyTextStream:
    """Minimal stream used by windowed packaged builds where stdio can be None."""

    encoding = "utf-8"
    errors = "replace"

    def write(self, *_args: Any, **_kwargs: Any) -> int:
        return 0

    def flush(self, *_args: Any, **_kwargs: Any) -> None:
        return None

    def isatty(self) -> bool:
        return False


def apply_utf8_environment() -> None:
    """Keep child Python processes in UTF-8 mode unless the caller overrides it."""
    for key, value in UTF8_ENV_DEFAULTS.items():
        os.environ.setdefault(key, value)


def build_utf8_subprocess_env(
    base_env: Mapping[str, str] | None = None,
    overrides: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Return an environment suitable for launching packaged Python helpers."""
    env = dict(base_env or os.environ)
    for key, value in UTF8_ENV_DEFAULTS.items():
        env.setdefault(key, value)
    if overrides:
        env.update(overrides)
    return env


def patch_standard_streams() -> None:
    """Make stdout/stderr safe for non-UTF-8 locales and no-console builds."""
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is None:
            setattr(sys, stream_name, DummyTextStream())
            continue

        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def configure_process_encoding() -> None:
    apply_utf8_environment()
    patch_standard_streams()
