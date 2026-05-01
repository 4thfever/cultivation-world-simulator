from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from tqdm import tqdm

from tools.img_gen.postprocess_common import image_files, process_avatar_image


def postprocess_avatars(
    input_dir: str | Path,
    output_dir: str | Path,
    *,
    crop_fraction: float = 1 / 16,
    white_threshold: int = 240,
    resize_to: tuple[int, int] | None = (512, 512),
    rename_by_index: bool = False,
) -> list[Path]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    saved: list[Path] = []
    for index, input_path in enumerate(tqdm(image_files(input_dir), desc="Processing avatars"), start=1):
        target_name = f"{index}_avatar.png" if rename_by_index else input_path.name
        target = output_path / target_name
        process_avatar_image(
            input_path,
            crop_fraction=crop_fraction,
            white_threshold=white_threshold,
            resize_to=resize_to,
            output=target,
        )
        saved.append(target)
    return saved


def main() -> None:
    parser = argparse.ArgumentParser(description="Crop, resize, and remove avatar white backgrounds.")
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--crop-fraction", type=float, default=1 / 16)
    parser.add_argument("--white-threshold", type=int, default=240)
    parser.add_argument(
        "--rename-by-index",
        action="store_true",
        help="Use legacy sequential names like 1_avatar.png instead of preserving input names.",
    )
    args = parser.parse_args()

    postprocess_avatars(
        args.input_dir,
        args.output_dir,
        crop_fraction=args.crop_fraction,
        white_threshold=args.white_threshold,
        rename_by_index=args.rename_by_index,
    )


if __name__ == "__main__":
    main()
