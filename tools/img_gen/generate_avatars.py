from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from tools.img_gen.client import generate_image_bytes
from tools.img_gen.prompts_avatars import AVATAR_REALMS, avatar_realm_prompt_records


def generate_avatars(
    gender: str,
    *,
    output_dir: str | Path | None = None,
    limit: int | None = None,
    realm_slugs: list[str] | None = None,
) -> list[Path]:
    records = avatar_realm_prompt_records(gender, realm_slugs=realm_slugs)
    if limit is not None:
        records = [record for record in records if record.index <= limit]

    target_dir = Path(output_dir) if output_dir else Path("tools/img_gen/tmp/avatars") / gender
    target_dir.mkdir(parents=True, exist_ok=True)

    saved: list[Path] = []
    manifest: list[dict[str, str | int]] = []
    for record in records:
        output_path = target_dir / f"{record.filename_stem}.png"
        output_path.write_bytes(generate_image_bytes(record.prompt))
        print(f"图片已保存: {output_path}")
        saved.append(output_path)
        manifest.append(
            {
                "gender": record.gender,
                "index": record.index,
                "realm_slug": record.realm_slug,
                "realm_name": record.realm_name,
                "file": output_path.name,
                "prompt": record.prompt,
            }
        )

    (target_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return saved


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate avatar portraits with Tabcode.")
    parser.add_argument("--gender", choices=["male", "female"], required=True)
    parser.add_argument("--output-dir")
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--realm",
        action="append",
        choices=[realm_slug for realm_slug, _, _ in AVATAR_REALMS],
        help="Realm slug to generate. Repeat to select multiple. Empty means all realms.",
    )
    args = parser.parse_args()

    generate_avatars(
        args.gender,
        output_dir=args.output_dir,
        limit=args.limit,
        realm_slugs=args.realm,
    )


if __name__ == "__main__":
    main()
