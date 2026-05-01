from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from tools.img_gen.client import generate_image_bytes
from tools.img_gen.io_utils import open_preview, save_png


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate one preview image with Tabcode.")
    parser.add_argument("--prompt", default="a cat sitting on a wooden table")
    parser.add_argument("--output-dir", default="tools/img_gen/tmp/preview")
    parser.add_argument("--open", action="store_true", help="Open the generated image.")
    args = parser.parse_args()

    output_path = save_png(
        generate_image_bytes(args.prompt),
        args.output_dir,
        prefix="tabcode_preview",
    )
    if args.open:
        open_preview(output_path)


if __name__ == "__main__":
    main()
