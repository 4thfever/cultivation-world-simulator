from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parent
DEFAULT_ENV_PATH = TOOL_DIR / "image_api.env"
LEGACY_ENV_PATH = TOOL_DIR / "tabcode.env"


@dataclass(frozen=True)
class ImageGenConfig:
    api_key: str
    base_url: str = "https://api.bltcy.ai/v1"
    model: str = "gpt-image-2-all"
    size: str = "1024x1024"


def _parse_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_config(env_path: str | Path = DEFAULT_ENV_PATH) -> ImageGenConfig:
    env_file = Path(env_path)
    env_values = _parse_env_file(env_file)
    if env_file == DEFAULT_ENV_PATH and not env_values:
        env_values = _parse_env_file(LEGACY_ENV_PATH)

    def get(name: str, default: str = "", legacy_name: str | None = None) -> str:
        value = os.environ.get(name)
        if value is None and legacy_name is not None:
            value = os.environ.get(legacy_name)
        if value is None:
            value = env_values.get(name)
        if value is None and legacy_name is not None:
            value = env_values.get(legacy_name)
        return (value or default).strip()

    api_key = get("IMAGE_API_KEY", legacy_name="TABCODE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "请在 tools/img_gen/image_api.env 或环境变量中设置 IMAGE_API_KEY"
        )

    return ImageGenConfig(
        api_key=api_key,
        base_url=get("IMAGE_API_BASE_URL", ImageGenConfig.base_url, "TABCODE_BASE_URL"),
        model=get("IMAGE_API_MODEL", ImageGenConfig.model, "TABCODE_IMAGE_MODEL"),
        size=get("IMAGE_API_SIZE", ImageGenConfig.size, "TABCODE_IMAGE_SIZE"),
    )
