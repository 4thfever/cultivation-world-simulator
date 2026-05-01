from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from tqdm import tqdm

from tools.img_gen.postprocess_common import image_files, process_sect_image
from tools.img_gen.prompts_sects import SECT_PROMPTS


def postprocess_sects(
    input_dir: str | Path = "tools/img_gen/tmp/sects",
    output_dir: str | Path = "tools/img_gen/tmp/processed_sects",
    *,
    crop_fraction: float = 1 / 16,
    resize_to: tuple[int, int] | None = (512, 512),
) -> list[Path]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    sect_names = [name for name, _ in SECT_PROMPTS]

    saved: list[Path] = []
    for index, input_path in enumerate(tqdm(image_files(input_dir), desc="Processing sects")):
        output_name = f"{sect_names[index]}.png" if index < len(sect_names) else input_path.name
        target = output_path / output_name
        process_sect_image(
            input_path,
            crop_fraction=crop_fraction,
            resize_to=resize_to,
            output=target,
        )
        saved.append(target)
    return saved


def main() -> None:
    parser = argparse.ArgumentParser(description="Crop and resize sect scene images.")
    parser.add_argument("--input-dir", default="tools/img_gen/tmp/sects")
    parser.add_argument("--output-dir", default="tools/img_gen/tmp/processed_sects")
    parser.add_argument("--crop-fraction", type=float, default=1 / 16)
    args = parser.parse_args()

    postprocess_sects(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        crop_fraction=args.crop_fraction,
    )


if __name__ == "__main__":
    main()
