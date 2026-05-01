from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from tqdm import tqdm

from tools.img_gen.postprocess_common import process_avatar_image

ALLOWED_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


def nested_image_files(input_dir: str | Path) -> list[Path]:
    input_path = Path(input_dir)
    return [
        path
        for path in sorted(input_path.rglob("*"))
        if path.is_file()
        and path.suffix.lower() in ALLOWED_SUFFIXES
        and path.name != "manifest.json"
    ]


def postprocess_yaoguai_avatars(
    input_dir: str | Path = "tools/img_gen/tmp/yaoguai_avatars",
    output_dir: str | Path = "tools/img_gen/tmp/processed_yaoguai_avatars",
    *,
    crop_fraction: float = 1 / 16,
    white_threshold: int = 240,
    resize_to: tuple[int, int] | None = (512, 512),
) -> list[Path]:
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    saved: list[Path] = []
    for source in tqdm(nested_image_files(input_path), desc="Processing yaoguai avatars"):
        relative = source.relative_to(input_path)
        target = output_path / relative.with_suffix(".png")
        target.parent.mkdir(parents=True, exist_ok=True)
        process_avatar_image(
            source,
            crop_fraction=crop_fraction,
            white_threshold=white_threshold,
            resize_to=resize_to,
            output=target,
        )
        saved.append(target)
    return saved


def main() -> None:
    parser = argparse.ArgumentParser(description="Postprocess yaoguai avatar portraits.")
    parser.add_argument("--input-dir", default="tools/img_gen/tmp/yaoguai_avatars")
    parser.add_argument("--output-dir", default="tools/img_gen/tmp/processed_yaoguai_avatars")
    parser.add_argument("--crop-fraction", type=float, default=1 / 16)
    parser.add_argument("--white-threshold", type=int, default=240)
    args = parser.parse_args()

    postprocess_yaoguai_avatars(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        crop_fraction=args.crop_fraction,
        white_threshold=args.white_threshold,
    )


if __name__ == "__main__":
    main()
