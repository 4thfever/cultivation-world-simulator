from __future__ import annotations

import base64

from openai import OpenAI

from tools.img_gen.config import ImageGenConfig, load_config


def create_client(config: ImageGenConfig | None = None) -> OpenAI:
    resolved = config or load_config()
    return OpenAI(base_url=resolved.base_url, api_key=resolved.api_key)


def generate_image_b64(
    prompt: str,
    *,
    config: ImageGenConfig | None = None,
    model: str | None = None,
    size: str | None = None,
    n: int = 1,
) -> str:
    resolved = config or load_config()
    client = create_client(resolved)
    response = client.images.generate(
        model=model or resolved.model,
        prompt=prompt,
        n=n,
        size=size or resolved.size,
    )

    if not getattr(response, "data", None):
        raise RuntimeError("未在响应中找到图片数据")

    first = response.data[0]
    image_b64 = getattr(first, "b64_json", None) or getattr(first, "b64", None)
    if not image_b64:
        raise RuntimeError("未在响应中找到图片 base64 数据")

    return image_b64


def generate_image_bytes(
    prompt: str,
    *,
    config: ImageGenConfig | None = None,
    model: str | None = None,
    size: str | None = None,
) -> bytes:
    return base64.b64decode(
        generate_image_b64(prompt, config=config, model=model, size=size)
    )
