from __future__ import annotations

import os
import webbrowser
from datetime import datetime
from pathlib import Path


def timestamped_png_path(output_dir: str | Path, prefix: str = "") -> Path:
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    stem = datetime.now().strftime("%Y%m%d_%H%M%S")
    if prefix:
        stem = f"{prefix}_{stem}"
    return path / f"{stem}.png"


def save_png(data: bytes, output_dir: str | Path, *, prefix: str = "") -> Path:
    output_path = timestamped_png_path(output_dir, prefix=prefix)
    output_path.write_bytes(data)
    print(f"图片已保存: {output_path}")
    return output_path


def open_preview(path: str | Path) -> None:
    resolved = Path(path).resolve()
    if os.name == "nt":
        os.startfile(str(resolved))
    else:
        webbrowser.open(resolved.as_uri())
