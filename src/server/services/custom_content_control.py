from __future__ import annotations

from typing import Any, Callable


async def generate_custom_content(
    *,
    category: str,
    realm: str | None,
    user_prompt: str,
    generate_custom_goldfinger_draft: Callable[[str], Any],
    generate_custom_content_draft: Callable[[str, Any, str], Any],
    realm_from_str: Callable[[str], Any],
) -> dict[str, Any]:
    if category == "goldfinger":
        draft = await generate_custom_goldfinger_draft(user_prompt)
    else:
        draft = await generate_custom_content_draft(
            category,
            realm_from_str(realm) if realm else None,
            user_prompt,
        )
    return {"status": "ok", "draft": draft}


def create_custom_content(
    *,
    category: str,
    draft: dict[str, Any],
    create_custom_goldfinger_from_draft: Callable[[dict[str, Any]], Any],
    create_custom_content_from_draft: Callable[[str, dict[str, Any]], Any],
) -> dict[str, Any]:
    if category == "goldfinger":
        item = create_custom_goldfinger_from_draft(draft)
    else:
        item = create_custom_content_from_draft(category, draft)
    return {"status": "ok", "item": item}
