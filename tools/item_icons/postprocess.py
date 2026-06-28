from __future__ import annotations

import argparse
from collections import deque
from pathlib import Path

from PIL import Image

DEFAULT_KEY = (255, 0, 255)


def split_contact_sheet(
    input_path: str | Path,
    output_dir: str | Path,
    *,
    columns: int,
    rows: int,
    prefix: str,
) -> list[Path]:
    source = Image.open(input_path).convert("RGBA")
    width, height = source.size
    cell_width = width // columns
    cell_height = height // rows
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    paths: list[Path] = []
    for row in range(rows):
        for col in range(columns):
            index = row * columns + col
            box = (
                col * cell_width,
                row * cell_height,
                (col + 1) * cell_width,
                (row + 1) * cell_height,
            )
            tile = source.crop(box)
            path = output / f"{prefix}_{index + 1:02d}.png"
            tile.save(path)
            paths.append(path)
    return paths


def chroma_key_to_alpha(
    input_path: str | Path,
    output_path: str | Path,
    *,
    key_rgb: tuple[int, int, int] = DEFAULT_KEY,
    threshold: int = 18,
) -> Path:
    image = Image.open(input_path).convert("RGBA")
    pixels = image.load()
    kr, kg, kb = key_rgb
    for y in range(image.height):
        for x in range(image.width):
            r, g, b, a = pixels[x, y]
            distance = abs(r - kr) + abs(g - kg) + abs(b - kb)
            if distance <= threshold:
                pixels[x, y] = (r, g, b, 0)
            elif g > 180 and r < 80 and b < 80:
                pixels[x, y] = (r, g, b, min(a, 32))

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)
    return output


def _color_distance(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])


def _sample_border_background(image: Image.Image) -> tuple[int, int, int]:
    rgb = image.convert("RGB")
    samples: list[tuple[int, int, int]] = []
    last_x = rgb.width - 1
    last_y = rgb.height - 1
    for x in range(rgb.width):
        samples.append(rgb.getpixel((x, 0)))
        samples.append(rgb.getpixel((x, last_y)))
    for y in range(rgb.height):
        samples.append(rgb.getpixel((0, y)))
        samples.append(rgb.getpixel((last_x, y)))

    def median_channel(index: int) -> int:
        values = sorted(pixel[index] for pixel in samples)
        return values[len(values) // 2]

    return (median_channel(0), median_channel(1), median_channel(2))


def _is_key_like(
    rgb: tuple[int, int, int],
    *,
    key_rgb: tuple[int, int, int],
    sampled_bg: tuple[int, int, int],
    key_threshold: int,
    sampled_threshold: int,
) -> bool:
    r, g, b = rgb
    kr, kg, kb = key_rgb
    if _color_distance(rgb, key_rgb) <= key_threshold:
        return True
    if _color_distance(rgb, sampled_bg) <= sampled_threshold:
        return True
    # Generated sheets often turn a requested chroma background into a darker
    # family of the same hue. Treat strongly chromatic magenta/green variants
    # as removable, but only when they are found from the outer background.
    if kr > 200 and kb > 200 and kg < 80:
        return r > 95 and b > 95 and g < max(r, b) * 0.55
    if kg > 200 and kr < 80 and kb < 80:
        return g > 95 and r < g * 0.55 and b < g * 0.55
    return False


def _remove_background_from_edges(
    image: Image.Image,
    *,
    key_rgb: tuple[int, int, int],
    key_threshold: int,
    sampled_threshold: int,
) -> Image.Image:
    result = image.convert("RGBA")
    pixels = result.load()
    sampled_bg = _sample_border_background(result)
    width, height = result.size
    queue: deque[tuple[int, int]] = deque()
    seen = set()

    for x in range(width):
        queue.append((x, 0))
        queue.append((x, height - 1))
    for y in range(height):
        queue.append((0, y))
        queue.append((width - 1, y))

    while queue:
        x, y = queue.popleft()
        if (x, y) in seen or x < 0 or y < 0 or x >= width or y >= height:
            continue
        seen.add((x, y))
        r, g, b, a = pixels[x, y]
        if a == 0:
            removable = True
        else:
            removable = _is_key_like(
                (r, g, b),
                key_rgb=key_rgb,
                sampled_bg=sampled_bg,
                key_threshold=key_threshold,
                sampled_threshold=sampled_threshold,
            )
        if not removable:
            continue
        pixels[x, y] = (r, g, b, 0)
        queue.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))

    return result


def _remove_small_alpha_components(image: Image.Image, *, min_area: int) -> Image.Image:
    result = image.convert("RGBA")
    pixels = result.load()
    width, height = result.size
    seen: set[tuple[int, int]] = set()

    for y in range(height):
        for x in range(width):
            if (x, y) in seen or pixels[x, y][3] == 0:
                continue
            component: list[tuple[int, int]] = []
            queue: deque[tuple[int, int]] = deque([(x, y)])
            while queue:
                cx, cy = queue.popleft()
                if (cx, cy) in seen or cx < 0 or cy < 0 or cx >= width or cy >= height:
                    continue
                seen.add((cx, cy))
                if pixels[cx, cy][3] == 0:
                    continue
                component.append((cx, cy))
                queue.extend(((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)))
            if len(component) < min_area:
                for px, py in component:
                    r, g, b, _ = pixels[px, py]
                    pixels[px, py] = (r, g, b, 0)

    return result


def clean_chroma_background(
    input_path: str | Path,
    output_path: str | Path,
    *,
    key_rgb: tuple[int, int, int] = DEFAULT_KEY,
    key_threshold: int = 90,
    sampled_threshold: int = 80,
    min_component_area: int = 24,
) -> Path:
    image = Image.open(input_path).convert("RGBA")
    cleaned = _remove_background_from_edges(
        image,
        key_rgb=key_rgb,
        key_threshold=key_threshold,
        sampled_threshold=sampled_threshold,
    )
    cleaned = _remove_small_alpha_components(cleaned, min_area=min_component_area)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    cleaned.save(output)
    return output


def suppress_chroma_spill(
    input_path: str | Path,
    output_path: str | Path,
    *,
    spill_rgb: tuple[int, int, int] = (0, 255, 0),
    dominance: float = 1.45,
    minimum_channel: int = 80,
) -> Path:
    image = Image.open(input_path).convert("RGBA")
    pixels = image.load()
    sr, sg, sb = spill_rgb
    target_green = sg >= sr and sg >= sb
    target_magenta = sr >= sg and sb >= sg

    for y in range(image.height):
        for x in range(image.width):
            r, g, b, a = pixels[x, y]
            if a == 0:
                continue
            if target_green:
                spill = g >= minimum_channel and g > max(r, b) * dominance
                if spill:
                    # Keep the pixel opaque but neutralize chroma-key tint into a
                    # dark edge color. This avoids punching holes in item details.
                    edge = max(8, min(80, int((r + b) * 0.35)))
                    pixels[x, y] = (edge, edge, edge, a)
            elif target_magenta:
                spill = (
                    r >= minimum_channel
                    and b >= minimum_channel
                    and min(r, b) > g * dominance
                )
                if spill:
                    edge = max(8, min(96, int(g * 0.8)))
                    pixels[x, y] = (edge, edge, edge, a)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)
    return output


def pixelate_icon(
    input_path: str | Path,
    output_path: str | Path,
    *,
    working_size: int = 64,
    output_size: int = 128,
) -> Path:
    image = Image.open(input_path).convert("RGBA")
    image.thumbnail((working_size, working_size), Image.Resampling.NEAREST)
    canvas = Image.new("RGBA", (working_size, working_size), (0, 0, 0, 0))
    x = (working_size - image.width) // 2
    y = (working_size - image.height) // 2
    canvas.alpha_composite(image, (x, y))
    result = canvas.resize((output_size, output_size), Image.Resampling.NEAREST)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    result.save(output)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Split and process item icon contact sheets.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    split_parser = subparsers.add_parser("split")
    split_parser.add_argument("input")
    split_parser.add_argument("output_dir")
    split_parser.add_argument("--columns", type=int, required=True)
    split_parser.add_argument("--rows", type=int, required=True)
    split_parser.add_argument("--prefix", default="icon")

    key_parser = subparsers.add_parser("key")
    key_parser.add_argument("input")
    key_parser.add_argument("output")
    key_parser.add_argument("--threshold", type=int, default=18)

    clean_parser = subparsers.add_parser("clean")
    clean_parser.add_argument("input")
    clean_parser.add_argument("output")
    clean_parser.add_argument("--key-threshold", type=int, default=90)
    clean_parser.add_argument("--sampled-threshold", type=int, default=80)
    clean_parser.add_argument("--min-component-area", type=int, default=24)

    spill_parser = subparsers.add_parser("despill")
    spill_parser.add_argument("input")
    spill_parser.add_argument("output")
    spill_parser.add_argument("--dominance", type=float, default=1.45)
    spill_parser.add_argument("--minimum-channel", type=int, default=80)

    pixel_parser = subparsers.add_parser("pixelate")
    pixel_parser.add_argument("input")
    pixel_parser.add_argument("output")
    pixel_parser.add_argument("--working-size", type=int, default=64)
    pixel_parser.add_argument("--output-size", type=int, default=128)

    args = parser.parse_args()
    if args.command == "split":
        split_contact_sheet(
            args.input,
            args.output_dir,
            columns=args.columns,
            rows=args.rows,
            prefix=args.prefix,
        )
    elif args.command == "key":
        chroma_key_to_alpha(args.input, args.output, threshold=args.threshold)
    elif args.command == "clean":
        clean_chroma_background(
            args.input,
            args.output,
            key_threshold=args.key_threshold,
            sampled_threshold=args.sampled_threshold,
            min_component_area=args.min_component_area,
        )
    elif args.command == "despill":
        suppress_chroma_spill(
            args.input,
            args.output,
            dominance=args.dominance,
            minimum_channel=args.minimum_channel,
        )
    elif args.command == "pixelate":
        pixelate_icon(
            args.input,
            args.output,
            working_size=args.working_size,
            output_size=args.output_size,
        )


if __name__ == "__main__":
    main()
