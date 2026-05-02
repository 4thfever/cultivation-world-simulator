---
name: img-gen-avatar
description: Use when working on tools/img_gen avatar image generation, OpenAI-compatible image API config, human or yaoguai portrait prompts, qi-refining base generation, image-to-image realm edits, white-background postprocessing, manifests, or prompt rules that preserve pixel-art identity while changing cultivation realms.
---

# Img Gen Avatar

## Core Files

- Read `tools/img_gen/README.md` for runnable commands.
- Read `tools/img_gen/DESIGN.md` before changing prompt structure, realm edit behavior, file naming, or postprocessing assumptions.
- Keep real API keys only in ignored `tools/img_gen/image_api.env` or environment variables. Never commit keys.

## Workflow Rules

Use the two-stage avatar workflow:

1. Generate only qi-refining base portraits with text-to-image.
2. Generate foundation, golden core, and nascent soul portraits with image edits based directly on the qi-refining image.

Do not use chained edits such as qi-refining -> foundation -> golden core -> nascent soul. Do not generate four-grid images.

Default scripts must remain serial, skip existing files unless `--overwrite` is provided, show `tqdm` progress, and write manifests/failure JSON files.

## Prompt Rules

Describe visible appearance only. Avoid invisible identity/background labels such as丹修、咒修、宗门、背景设定.

For text-to-image base prompts, keep:

- pixel-art style
- low detail
- Q-style 2D anime portrait
- front-facing head-and-shoulders composition
- clean pure white background
- no texture, shadow, gradient, fog, glow, border, or scene background

For image-to-image realm edits, preserve:

- input pixel-art style, low detail, and Q-style 2D anime look
- face shape, facial proportions, skin tone tendency, hairstyle, hair color
- eye color, pupil shape, expression baseline
- original facial marks, main accessories, subject size, head-shoulder ratio
- front-facing composition and pure white background

For yaoguai edits, also preserve species traits and their positions/basic shapes, such as fox ears, wolf ears, ear feathers, vertical pupils, scales, turtle-shell patterns, and cheek markings.

Realm edits may visibly strengthen gaze, pupil highlights, collar layering, accessory refinement, existing markings, and close-to-body glow. Keep the change obvious enough to show realm advancement, but never at the cost of pixel style or character identity.

Explicitly forbid realistic style, high-definition illustration style, painterly rendering, over-detailed rendering, scene backgrounds, halos, frames, and large-area effects.
