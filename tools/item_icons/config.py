from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parent
DEFAULT_ENV_PATH = TOOL_DIR / ".env"


@dataclass(frozen=True)
class ItemIconConfig:
    api_key: str
    base_url: str = "https://api2.tabcode.cc/openai/draw/v1"
    model: str = "gpt-image-2"
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


def load_config(env_path: str | Path = DEFAULT_ENV_PATH) -> ItemIconConfig:
    env_values = _parse_env_file(Path(env_path))

    def get(name: str, default: str = "") -> str:
        return (os.environ.get(name) or env_values.get(name) or default).strip()

    api_key = get("ITEM_ICON_API_KEY")
    if not api_key:
        raise RuntimeError(
            "请在 tools/item_icons/.env 或环境变量中设置 ITEM_ICON_API_KEY"
        )

    return ItemIconConfig(
        api_key=api_key,
        base_url=get("ITEM_ICON_API_BASE_URL", ItemIconConfig.base_url).rstrip("/"),
        model=get("ITEM_ICON_API_MODEL", ItemIconConfig.model),
        size=get("ITEM_ICON_API_SIZE", ItemIconConfig.size),
    )
