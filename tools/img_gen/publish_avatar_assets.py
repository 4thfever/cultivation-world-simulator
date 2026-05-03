from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR = ROOT / "assets"

HUMAN_SOURCE = ROOT / "tools" / "img_gen" / "tmp" / "avatars"
YAO_SOURCE = ROOT / "tools" / "img_gen" / "tmp" / "yaoguai_avatars"
PROCESSED_HUMAN_SOURCE = ROOT / "tools" / "img_gen" / "tmp" / "processed_avatars"
PROCESSED_YAO_SOURCE = ROOT / "tools" / "img_gen" / "tmp" / "processed_yaoguai_avatars"

HUMAN_TARGET = ASSETS_DIR / "avatars"
YAO_TARGET = ASSETS_DIR / "yao"

REALMS = ("qi_refining", "foundation", "golden_core", "nascent_soul")
HUMAN_GENDERS = ("female", "male")
YAO_SPECIES = ("fox", "wolf", "bird", "snake", "turtle")
YAO_EXPECTED_INDICES_PER_SPECIES_GENDER = 9

HUMAN_RE = re.compile(r"^(female|male)_(\d{3})_(qi_refining|foundation|golden_core|nascent_soul)\.png$")
YAO_RE = re.compile(
    r"^(fox|wolf|bird|snake|turtle)_(female|male)_(\d{2})_(qi_refining|foundation|golden_core|nascent_soul)\.png$"
)


def _reset_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def _copy_humans(source_dir: Path) -> int:
    if not source_dir.exists():
        raise FileNotFoundError(f"Human avatar source does not exist: {source_dir}")

    count = 0
    seen: set[tuple[str, str, str]] = set()
    for source in source_dir.rglob("*.png"):
        match = HUMAN_RE.match(source.name)
        if not match:
            raise ValueError(f"Unexpected human avatar filename: {source.name}")
        gender, index, realm = match.groups()
        target = HUMAN_TARGET / gender / index / f"{realm}.png"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        seen.add((gender, index, realm))
        count += 1

    for gender in HUMAN_GENDERS:
        indices = sorted({index for g, index, _ in seen if g == gender})
        if len(indices) != 48:
            raise ValueError(f"Expected 48 {gender} avatar indices, got {len(indices)}")
        for index in indices:
            missing = [realm for realm in REALMS if (gender, index, realm) not in seen]
            if missing:
                raise ValueError(f"Missing {gender}/{index} realms: {missing}")

    return count


def _copy_yao(source_dir: Path) -> int:
    if not source_dir.exists():
        raise FileNotFoundError(f"Yao avatar source does not exist: {source_dir}")

    count = 0
    seen: set[tuple[str, str, str, str]] = set()
    for source in source_dir.rglob("*.png"):
        match = YAO_RE.match(source.name)
        if not match:
            raise ValueError(f"Unexpected yao avatar filename: {source.name}")
        species, gender, index, realm = match.groups()
        target = YAO_TARGET / species / gender / index / f"{realm}.png"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        seen.add((species, gender, index, realm))
        count += 1

    for species in YAO_SPECIES:
        for gender in HUMAN_GENDERS:
            indices = sorted({index for s, g, index, _ in seen if s == species and g == gender})
            if len(indices) != YAO_EXPECTED_INDICES_PER_SPECIES_GENDER:
                raise ValueError(
                    f"Expected {YAO_EXPECTED_INDICES_PER_SPECIES_GENDER} "
                    f"{species}/{gender} avatar indices, got {len(indices)}"
                )
            for index in indices:
                missing = [realm for realm in REALMS if (species, gender, index, realm) not in seen]
                if missing:
                    raise ValueError(f"Missing {species}/{gender}/{index} realms: {missing}")

    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish generated avatar images into game assets.")
    parser.add_argument(
        "--use-processed",
        action="store_true",
        help="Publish postprocessed transparent images from tmp/processed_* directories.",
    )
    args = parser.parse_args()

    human_source = PROCESSED_HUMAN_SOURCE if args.use_processed else HUMAN_SOURCE
    yao_source = PROCESSED_YAO_SOURCE if args.use_processed else YAO_SOURCE

    _reset_dir(HUMAN_TARGET)
    _reset_dir(YAO_TARGET)

    human_count = _copy_humans(human_source)
    yao_count = _copy_yao(yao_source)

    for old_dir in (ASSETS_DIR / "females", ASSETS_DIR / "males"):
        if old_dir.exists():
            shutil.rmtree(old_dir)

    print(f"Published {human_count} human avatar images from {human_source} to {HUMAN_TARGET}")
    print(f"Published {yao_count} yao avatar images from {yao_source} to {YAO_TARGET}")
    print("Removed old assets/females and assets/males directories when present")


if __name__ == "__main__":
    main()
