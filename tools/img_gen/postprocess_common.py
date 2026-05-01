from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import Optional, Union

import numpy as np
from PIL import Image

PathLike = Union[str, Path]


def remove_white_background(
    source: PathLike | Image.Image,
    white_threshold: int = 240,
    output: Optional[PathLike] = None,
) -> Image.Image:
    if isinstance(source, (str, Path)):
        with Image.open(source) as loaded:
            image = loaded.convert("RGB")
    else:
        image = source.convert("RGB")

    width, height = image.size
    if width == 0 or height == 0:
        result = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        if output is not None:
            result.save(output)
        return result

    img_array = np.array(image)
    background_mask = np.zeros((height, width), dtype=bool)
    visited = np.zeros((height, width), dtype=bool)
    queue = deque()

    def is_white(y: int, x: int) -> bool:
        pixel = img_array[y, x]
        return (
            pixel[0] >= white_threshold
            and pixel[1] >= white_threshold
            and pixel[2] >= white_threshold
        )

    for x in range(width):
        if is_white(0, x):
            queue.append((0, x))
            visited[0, x] = True
            background_mask[0, x] = True
        if is_white(height - 1, x):
            queue.append((height - 1, x))
            visited[height - 1, x] = True
            background_mask[height - 1, x] = True

    for y in range(1, height - 1):
        if is_white(y, 0):
            queue.append((y, 0))
            visited[y, 0] = True
            background_mask[y, 0] = True
        if is_white(y, width - 1):
            queue.append((y, width - 1))
            visited[y, width - 1] = True
            background_mask[y, width - 1] = True

    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    while queue:
        y, x = queue.popleft()
        for dy, dx in directions:
            ny, nx = y + dy, x + dx
            if 0 <= ny < height and 0 <= nx < width and not visited[ny, nx]:
                if is_white(ny, nx):
                    visited[ny, nx] = True
                    background_mask[ny, nx] = True
                    queue.append((ny, nx))

    result_array = np.zeros((height, width, 4), dtype=np.uint8)
    result_array[:, :, :3] = img_array
    result_array[:, :, 3] = np.where(background_mask, 0, 255)
    result = Image.fromarray(result_array, mode="RGBA")

    if output is not None:
        result.save(output)

    return result


def crop_inner_region(
    source: PathLike | Image.Image,
    fraction: float = 1 / 16,
    output: Optional[PathLike] = None,
) -> Image.Image:
    if isinstance(source, (str, Path)):
        with Image.open(source) as loaded:
            image = loaded.convert("RGBA")
    else:
        image = source.copy()

    width, height = image.size
    if width == 0 or height == 0:
        return image

    fraction = max(0.0, min(fraction, 0.5))
    dx = int(round(width * fraction))
    dy = int(round(height * fraction))

    left = min(dx, width // 2)
    upper = min(dy, height // 2)
    right = max(width - dx, left)
    lower = max(height - dy, upper)
    cropped = image.crop((left, upper, right, lower))

    if output is not None:
        cropped.save(output)

    return cropped


def process_avatar_image(
    source: PathLike | Image.Image,
    *,
    crop_fraction: float = 1 / 16,
    white_threshold: int = 240,
    resize_to: Optional[tuple[int, int]] = (512, 512),
    output: Optional[PathLike] = None,
) -> Image.Image:
    cleaned = remove_white_background(
        crop_inner_region(source, fraction=crop_fraction),
        white_threshold=white_threshold,
    )

    if resize_to is not None:
        cleaned = cleaned.resize(resize_to, Image.Resampling.LANCZOS)

    if output is not None:
        cleaned.save(output)

    return cleaned


def process_sect_image(
    source: PathLike | Image.Image,
    *,
    crop_fraction: float = 1 / 16,
    resize_to: Optional[tuple[int, int]] = (512, 512),
    output: Optional[PathLike] = None,
) -> Image.Image:
    cropped = crop_inner_region(source, fraction=crop_fraction)
    if resize_to is not None:
        cropped = cropped.resize(resize_to, Image.Resampling.LANCZOS)

    if output is not None:
        cropped.save(output)

    return cropped


def image_files(input_dir: PathLike) -> list[Path]:
    allowed_suffixes = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
    input_path = Path(input_dir)
    return [
        path
        for path in sorted(input_path.iterdir())
        if path.is_file() and path.suffix.lower() in allowed_suffixes
    ]
