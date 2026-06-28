from __future__ import annotations

from dataclasses import dataclass

CHROMA_KEY = "#ff00ff"


@dataclass(frozen=True)
class IconPromptItem:
    item_id: str
    category: str
    name: str
    desc: str
    meta: str = ""


def build_contact_sheet_prompt(items: list[IconPromptItem], *, columns: int = 4) -> str:
    rows = (len(items) + columns - 1) // columns
    numbered = "\n".join(
        f"{index + 1}. {item.category}: {item.name} - {item.desc} {item.meta}".strip()
        for index, item in enumerate(items)
    )
    return f"""Create a single pixel-art RPG item icon contact sheet for later transparent-background extraction.

Canvas/layout:
- Exactly {columns} columns by {rows} rows, one centered icon per cell.
- Keep every icon fully inside its cell with generous padding.
- No labels, no numbers, no UI frame, no watermark, no text.
- Use one perfectly flat solid {CHROMA_KEY} chroma-key background across the whole image.
- The background must be mathematically plain: no dithering, no pixel speckles, no texture, no gradients, no vignette, no floor plane.
- Do not use {CHROMA_KEY}, purple-magenta outlines, or pink particles anywhere inside the items.
- Keep item glow, particles, smoke, and magic aura inside the item silhouette; do not scatter decorative pixels into the background.

Style:
- 32-bit fantasy cultivation RPG pixel art.
- Clear silhouette, readable at 64x64, crisp hard edges.
- Slight top-left highlight, subtle item detail, no cast shadow, no ambient shadow.
- Transparent-ready asset style, isolated objects only.
- Each icon should look like a standalone inventory item sprite, not a scene.

Items in reading order:
{numbered}
"""


def build_connectivity_prompt() -> str:
    return """Create one small pixel-art fantasy cultivation RPG item icon: a simple jade spirit stone.
Use a perfectly flat solid #ff00ff chroma-key background, no shadows, no text, no watermark.
The item should be centered, crisp, readable at 64x64, with generous padding."""
