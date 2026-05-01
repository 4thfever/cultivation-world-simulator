from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from tools.img_gen.client import generate_image_bytes
from tools.img_gen.prompts_yaoguai_avatars import (
    SPECIES_NAMES,
    YAOGUAI_REALM_SLUGS,
    yaoguai_avatar_prompt_records,
)


def generate_yaoguai_avatars(
    *,
    output_dir: str | Path = "tools/img_gen/tmp/yaoguai_avatars",
    species_slugs: list[str] | None = None,
    genders: list[str] | None = None,
    realm_slugs: list[str] | None = None,
    limit: int | None = None,
) -> list[Path]:
    records = yaoguai_avatar_prompt_records(
        species_slugs=species_slugs,
        genders=genders,
        realm_slugs=realm_slugs,
    )
    if limit is not None:
        records = [record for record in records if record.index <= limit]

    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    saved: list[Path] = []
    manifest: list[dict[str, str | int]] = []
    for record in records:
        output_path = target_dir / record.species_slug / record.gender / f"{record.filename_stem}.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(generate_image_bytes(record.prompt))
        print(f"图片已保存: {output_path}")
        saved.append(output_path)
        manifest.append(
            {
                "species_slug": record.species_slug,
                "species_name": record.species_name,
                "gender": record.gender,
                "index": record.index,
                "realm_slug": record.realm_slug,
                "realm_name": record.realm_name,
                "file": str(output_path.relative_to(target_dir)).replace("\\", "/"),
                "prompt": record.prompt,
            }
        )

    (target_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return saved


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate yaoguai avatar portraits with Tabcode.")
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
    parser.add_argument(
        "--realm",
        action="append",
        choices=YAOGUAI_REALM_SLUGS,
        help="Realm slug. Repeat to select multiple. Empty means all realms.",
    )
    parser.add_argument("--output-dir", default="tools/img_gen/tmp/yaoguai_avatars")
    parser.add_argument("--limit", type=int, help="Limit appearance indexes per species and gender.")
    args = parser.parse_args()

    generate_yaoguai_avatars(
        output_dir=args.output_dir,
        species_slugs=args.species,
        genders=args.gender,
        realm_slugs=args.realm,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
