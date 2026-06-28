from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.item_icons.client import ImageApiError
from tools.item_icons.client import save_generated_image
from tools.item_icons.config import load_config
from tools.item_icons.prompts import build_connectivity_prompt


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify Tabcode image API connectivity.")
    parser.add_argument("--out", default="tools/item_icons/connectivity.png")
    parser.add_argument("--meta-out", default="tools/item_icons/connectivity.json")
    args = parser.parse_args()

    config = load_config()
    try:
        output = save_generated_image(
            build_connectivity_prompt(),
            args.out,
            config=config,
            max_retries=0,
        )
    except ImageApiError as exc:
        meta = {
            "ok": False,
            "base_url": config.base_url,
            "model": config.model,
            "size": config.size,
            "status_code": exc.status_code,
            "error": str(exc),
        }
        Path(args.meta_out).write_text(
            json.dumps(meta, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(json.dumps(meta, ensure_ascii=False))
        raise SystemExit(1) from exc
    else:
        meta = {
            "ok": True,
            "base_url": config.base_url,
            "model": config.model,
            "size": config.size,
            "output": str(output),
        }
    Path(args.meta_out).write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False))


if __name__ == "__main__":
    main()
