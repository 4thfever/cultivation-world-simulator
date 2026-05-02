from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from tools.img_gen.client import generate_image_bytes
from tools.img_gen.io_utils import save_png
from tools.img_gen.prompts_tiles import TILE_PROMPTS


def generate_tiles(
    names: list[str],
    *,
    output_dir: str | Path = "tools/img_gen/tmp/tiles",
) -> list[Path]:
    selected = names or sorted(TILE_PROMPTS)
    unknown = [name for name in selected if name not in TILE_PROMPTS]
    if unknown:
        raise ValueError(f"未知 tile prompt: {', '.join(unknown)}")

    saved: list[Path] = []
    for name in selected:
        image = generate_image_bytes(TILE_PROMPTS[name])
        saved.append(save_png(image, output_dir, prefix=name))
    return saved


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate 3x3 tile sprite sheets with an OpenAI-compatible image API.")
    parser.add_argument("names", nargs="*", help="Tile names. Empty means all prompts.")
    parser.add_argument("--output-dir", default="tools/img_gen/tmp/tiles")
    args = parser.parse_args()

    generate_tiles(args.names, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
