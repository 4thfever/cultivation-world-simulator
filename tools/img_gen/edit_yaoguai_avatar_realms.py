from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from tqdm import tqdm

from tools.img_gen.client import edit_image_bytes
from tools.img_gen.prompts_yaoguai_avatars import (
    SPECIES_NAMES,
    YAOGUAI_REALM_SLUGS,
    yaoguai_avatar_prompt_records,
)

BASE_REALM_SLUG = "qi_refining"
TARGET_REALM_SLUGS = ["foundation", "golden_core", "nascent_soul"]

REALM_EDIT_STYLES = {
    "筑基": (
        "筑基的升级强度为中等：衣服、首饰和附件在原有色调体系下变得更整洁、更稳定、更精致，"
        "妖族纹样更清晰但不要过度华丽，体现根基稳固。"
    ),
    "金丹": (
        "金丹的升级强度为明显：衣服、首饰和附件在原有色调体系下变得更强大、更华丽、更有凝练质感，"
        "妖族纹样、饰物材质和瞳孔高光可以更醒目。"
    ),
    "元婴": (
        "元婴的升级强度为最高但更空灵：衣服、首饰和附件在原有色调体系下变得更仙气、更通透、更华贵，"
        "妖族纹样更优雅，材质更轻盈精美，整体强大但不厚重。"
    ),
}


def build_yaoguai_edit_prompt(
    *,
    appearance_prompt: str,
    realm_prompt: str,
    realm_name: str,
) -> str:
    return (
        f"基于输入妖族头像升级为{realm_name}阶段，变化幅度约55%，需要明显强于原图。"
        "只需保持能认出是同一个妖族角色：输入图的像素风格、低细节程度、Q版二次元漫画风、脸型和五官大致比例、发型轮廓、发色、核心妖族种族特征、正面头像构图、纯白背景。"
        "允许明显改变：表情、气质、年龄感、衣领服饰、发饰或耳饰复杂度、饰物材质、眼神强度、瞳孔高光、原有妖族纹样、贴身微光。"
        "必须做出显著可见变化：眼神、服饰层次、饰物精致度、妖族纹样或贴身光效至少四项明显升级。"
        f"{REALM_EDIT_STYLES.get(realm_name, '')}"
        "可以让妖族纹样更清晰、饰物材质更高级、衣领更华丽、贴身光效更强，但光效必须靠近角色本体。"
        "不要只是轻微调色；需要一眼看出境界提升和妖力增强。"
        "不要改变性别，不要改变核心种族特征，不要添加背景、边框、场景、光环、翅膀展开或大面积特效。"
        "禁止改成写实风、高清插画风、厚涂风或过度精细风，必须仍然是像素头像。"
        f"外貌参考：{appearance_prompt}"
        f"境界变化：{realm_prompt}"
    )


def edit_yaoguai_avatar_realms(
    *,
    input_dir: str | Path = "tools/img_gen/tmp/yaoguai_avatars",
    output_dir: str | Path | None = None,
    species_slugs: list[str] | None = None,
    genders: list[str] | None = None,
    realm_slugs: list[str] | None = None,
    limit: int | None = None,
    overwrite: bool = False,
    max_retries: int = 3,
    retry_delay: float = 5.0,
) -> list[Path]:
    source_dir = Path(input_dir)
    target_dir = Path(output_dir) if output_dir else source_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    selected_realms = realm_slugs or TARGET_REALM_SLUGS
    records = yaoguai_avatar_prompt_records(
        species_slugs=species_slugs,
        genders=genders,
        realm_slugs=selected_realms,
    )
    if limit is not None:
        records = [record for record in records if record.index <= limit]

    saved: list[Path] = []
    manifest: list[dict[str, str | int]] = []
    failures: list[dict[str, str | int]] = []
    for record in tqdm(records, desc="Editing yaoguai avatar realms"):
        source_name = f"{record.species_slug}_{record.gender}_{record.index:02d}_{BASE_REALM_SLUG}.png"
        relative_parent = Path(record.species_slug) / record.gender
        source_path = source_dir / relative_parent / source_name
        if not source_path.exists():
            tqdm.write(f"缺少练气原图，跳过: {source_path}")
            continue

        output_path = target_dir / relative_parent / f"{record.filename_stem}.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if output_path.exists() and not overwrite:
            tqdm.write(f"已存在，跳过: {output_path}")
            continue

        edit_prompt = build_yaoguai_edit_prompt(
            appearance_prompt=record.appearance_prompt,
            realm_prompt=record.realm_prompt,
            realm_name=record.realm_name,
        )
        try:
            image_bytes = edit_image_bytes(
                source_path,
                edit_prompt,
                max_retries=max_retries,
                retry_delay=retry_delay,
            )
        except Exception as exc:
            tqdm.write(f"编辑失败，跳过: {output_path} ({type(exc).__name__}: {exc})")
            failures.append(
                {
                    "stage": "realm_edit",
                    "species_slug": record.species_slug,
                    "species_name": record.species_name,
                    "gender": record.gender,
                    "index": record.index,
                    "source_file": str((relative_parent / source_name)).replace("\\", "/"),
                    "realm_slug": record.realm_slug,
                    "realm_name": record.realm_name,
                    "file": str(output_path.relative_to(target_dir)).replace("\\", "/"),
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "prompt": edit_prompt,
                }
            )
            continue
        output_path.write_bytes(image_bytes)
        saved.append(output_path)
        manifest.append(
            {
                "stage": "realm_edit",
                "species_slug": record.species_slug,
                "species_name": record.species_name,
                "gender": record.gender,
                "index": record.index,
                "source_file": str((relative_parent / source_name)).replace("\\", "/"),
                "realm_slug": record.realm_slug,
                "realm_name": record.realm_name,
                "file": str(output_path.relative_to(target_dir)).replace("\\", "/"),
                "prompt": edit_prompt,
            }
        )

    if manifest:
        (target_dir / "realm_edit_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    if failures:
        (target_dir / "realm_edit_failures.json").write_text(
            json.dumps(failures, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return saved


def main() -> None:
    parser = argparse.ArgumentParser(description="Edit qi-refining yaoguai avatars into higher realms.")
    parser.add_argument("--input-dir", default="tools/img_gen/tmp/yaoguai_avatars")
    parser.add_argument("--output-dir")
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
        choices=[slug for slug in YAOGUAI_REALM_SLUGS if slug != BASE_REALM_SLUG],
        help="Target realm slug. Repeat to select multiple. Empty means foundation/golden_core/nascent_soul.",
    )
    parser.add_argument("--limit", type=int, help="Limit appearance indexes per species and gender.")
    parser.add_argument("--overwrite", action="store_true", help="Regenerate existing files.")
    parser.add_argument("--max-retries", type=int, default=3, help="Retries per image for transient API errors.")
    parser.add_argument("--retry-delay", type=float, default=5.0, help="Initial retry delay seconds.")
    args = parser.parse_args()

    edit_yaoguai_avatar_realms(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        species_slugs=args.species,
        genders=args.gender,
        realm_slugs=args.realm,
        limit=args.limit,
        overwrite=args.overwrite,
        max_retries=args.max_retries,
        retry_delay=args.retry_delay,
    )


if __name__ == "__main__":
    main()
