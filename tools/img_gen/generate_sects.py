from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from tools.img_gen.client import generate_image_bytes
from tools.img_gen.io_utils import save_png
from tools.img_gen.prompts_sects import sect_prompts


def generate_sects(
    *,
    output_dir: str | Path = "tools/img_gen/tmp/sects",
    limit: int | None = None,
) -> list[Path]:
    prompts = sect_prompts()
    if limit is not None:
        prompts = prompts[:limit]

    saved: list[Path] = []
    for name, prompt in prompts:
        image = generate_image_bytes(prompt)
        saved.append(save_png(image, output_dir, prefix=name))
    return saved


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate sect scene images with an OpenAI-compatible image API.")
    parser.add_argument("--output-dir", default="tools/img_gen/tmp/sects")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    generate_sects(output_dir=args.output_dir, limit=args.limit)


if __name__ == "__main__":
    main()
