from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from tqdm import tqdm

from tools.img_gen.client import generate_image_bytes
from tools.img_gen.prompts_yaoguai_avatars import (
    SPECIES_NAMES,
    yaoguai_avatar_prompt_records,
)

BASE_REALM_SLUG = "qi_refining"


def generate_yaoguai_avatars(
    *,
    output_dir: str | Path = "tools/img_gen/tmp/yaoguai_avatars",
    species_slugs: list[str] | None = None,
    genders: list[str] | None = None,
    limit: int | None = None,
    overwrite: bool = False,
    max_retries: int = 3,
    retry_delay: float = 5.0,
) -> list[Path]:
    records = yaoguai_avatar_prompt_records(
        species_slugs=species_slugs,
        genders=genders,
        realm_slugs=[BASE_REALM_SLUG],
    )
    if limit is not None:
        records = [record for record in records if record.index <= limit]

    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    saved: list[Path] = []
    manifest: list[dict[str, str | int]] = []
    failures: list[dict[str, str | int]] = []
    for record in tqdm(records, desc="Generating yaoguai qi-refining avatars"):
        output_path = target_dir / record.species_slug / record.gender / f"{record.filename_stem}.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if output_path.exists() and not overwrite:
            tqdm.write(f"已存在，跳过: {output_path}")
            continue
        try:
            image_bytes = generate_image_bytes(
                record.prompt,
                max_retries=max_retries,
                retry_delay=retry_delay,
            )
        except Exception as exc:
            tqdm.write(f"生成失败，跳过: {output_path} ({type(exc).__name__}: {exc})")
            failures.append(
                {
                    "species_slug": record.species_slug,
                    "species_name": record.species_name,
                    "gender": record.gender,
                    "index": record.index,
                    "realm_slug": record.realm_slug,
                    "realm_name": record.realm_name,
                    "file": str(output_path.relative_to(target_dir)).replace("\\", "/"),
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "prompt": record.prompt,
                }
            )
            continue
        output_path.write_bytes(image_bytes)
        saved.append(output_path)
        manifest.append(
            {
                "species_slug": record.species_slug,
                "species_name": record.species_name,
                "gender": record.gender,
                "index": record.index,
                "stage": "base_generation",
                "realm_slug": record.realm_slug,
                "realm_name": record.realm_name,
                "file": str(output_path.relative_to(target_dir)).replace("\\", "/"),
                "prompt": record.prompt,
            }
        )

    if manifest:
        (target_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    if failures:
        (target_dir / "generation_failures.json").write_text(
            json.dumps(failures, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return saved


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate qi-refining yaoguai avatar portraits with an OpenAI-compatible image API.")
    parser.add_argument(
        "--species",
        action="append",
        choices=list(SPECIES_NAMES),
        help="Species slug. Repeat to select multiple. Empty means all species.",
    )
    parser.add_argument(
        "--gender",
        action="append",
        choices=["female", "male"],
        help="Gender. Repeat to select both. Empty means both genders.",
    )
    parser.add_argument("--output-dir", default="tools/img_gen/tmp/yaoguai_avatars")
    parser.add_argument("--limit", type=int, help="Limit appearance indexes per species and gender.")
    parser.add_argument("--overwrite", action="store_true", help="Regenerate existing files.")
    parser.add_argument("--max-retries", type=int, default=3, help="Retries per image for transient API errors.")
    parser.add_argument("--retry-delay", type=float, default=5.0, help="Initial retry delay seconds.")
    args = parser.parse_args()

    generate_yaoguai_avatars(
        output_dir=args.output_dir,
        species_slugs=args.species,
        genders=args.gender,
        limit=args.limit,
        overwrite=args.overwrite,
        max_retries=args.max_retries,
        retry_delay=args.retry_delay,
    )


if __name__ == "__main__":
    main()
