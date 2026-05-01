# Vietnamese LLM Prompt Review

This document records the Vietnamese prompt rewrite for the LLM templates under `static/locales/vi-VN/templates`. The rewrite applies a consistent formal Hán-Việt / tiên hiệp voice while preserving the runtime prompt contracts.

## Architecture

The current LLM client does not send a separate `system` role message. Prompt text is assembled from locale-specific `.txt` templates and then sent as a single user message:

```json
{"messages": [{"role": "user", "content": "<rendered prompt>"}]}
```

Main prompt sources:

- `static/locales/<locale>/templates/*.txt`: primary LLM prompt templates.
- `static/locales/<locale>/modules/*.po` and `static/locales/<locale>/game_configs_modules/*.po`: localized prompt fragments and game config strings.
- Runtime path: `CONFIG.paths.templates` -> `call_llm_with_task_name(...)` -> `call_llm_with_template(...)` -> `build_prompt(...)`.

Locale roles from `static/locales/registry.json`:

- `zh-CN`: default locale and `source_of_truth`.
- `en-US`: fallback locale.
- `vi-VN`: enabled locale.

Important contract rule: placeholders such as `{world_info}` and machine-facing JSON keys such as `"thinking"`, `"choice"`, `"avatar_thinking"`, and `"action_name_params_pairs"` must remain exact. Enum values, action names, ids, and code-like type hints must also remain stable.

## Final Style Guide

The `vi-VN` runtime templates now use one consistent prompt voice:

- Role/setup lines address the model as `Ngươi`.
- The tone is formal, directive, and tu chân themed, but still clear enough for instruction following.
- Preferred terms:
  - `Xianxia / 修仙 / 仙侠`: `tu chân giới`, `tiên hiệp`
  - `sect`: `tông môn`
  - `cultivator`: `tu sĩ`
  - `goldfinger`: `ngoại quải`
  - other recurring terms: `đạo thống`, `linh thạch`, `tán tu`, `công pháp`, `pháp môn`, `cơ duyên`, `cục diện`, `điển tịch`, `truyền thừa`
- Natural Vietnamese is still preferred when overly archaic wording would reduce JSON compliance or task clarity.

## Applied Changes

All `vi-VN/templates/*.txt` were normalized, not only the P0/P1 files. This removes the previous mixed English/Vietnamese tone across prompt families.

Key schema fixes:

- `ai.txt` now includes `{avatar_ai_context}` and `{player_command}`, matching the `zh-CN` source contract.
- `single_choice.txt` now uses `{situation}` and `{options_json}` instead of the stale `{choices}` placeholder.
- `random_minor_event.txt` has no `zh-CN` source template, so its Vietnamese rewrite follows the `en-US` structure.

The rewrite covers these prompt groups:

- action decision and finite choice prompts;
- mutual action, conversation, and roleplay conversation prompts;
- story generation prompts;
- character backstory, nickname, and long-term objective prompts;
- random minor event prompts;
- relation delta/update prompts;
- sect decision/thinking/random-event prompts;
- custom content and custom ngoại quải prompts;
- world lore map/item/sect rewrite prompts.

## Template Audit

| Template | Previous state | Current state | Priority resolved |
|---|---|---|---|
| `ai.txt` | Mostly English, missing source placeholders | Rewritten Hán-Việt; placeholder parity restored | P0 |
| `single_choice.txt` | English copy with stale `{choices}` schema | Rewritten Hán-Việt; source schema restored | P0 |
| `auction_need.txt` | English copy | Rewritten Hán-Việt | P1 |
| `conversation.txt` | English copy | Rewritten Hán-Việt | P1 |
| `mutual_action.txt` | English copy | Rewritten Hán-Việt | P1 |
| `relation_update.txt` | English copy | Rewritten Hán-Việt | P1 |
| `sect_random_event.txt` | English copy | Rewritten Hán-Việt | P1 |
| `world_lore_item.txt` | English copy | Rewritten Hán-Việt | P1 |
| `world_lore_map.txt` | English copy | Rewritten Hán-Việt | P1 |
| `world_lore_sect.txt` | English copy | Rewritten Hán-Việt | P1 |
| `long_term_objective.txt`, `nickname.txt`, `story_*` | Mostly English | Rewritten Hán-Việt | P1 |
| Remaining `vi-VN` templates | Partial or inconsistent Vietnamese | Rewritten/normalized | P2 |

## Validation Method

Local validation should always be run after prompt edits:

```bash
pytest tests/test_backend_locales.py
pytest tests/tools/test_prompt_template_format.py
```

Additional local checks used for this rewrite:

- Format every `vi-VN/templates/*.txt` with representative placeholder data.
- Compare `vi-VN` placeholders with `zh-CN` for every template that has a `zh-CN` source.
- Search for English instruction leftovers, allowing only machine-facing tokens such as JSON keys, enum names, ids, `dict`, `key`, and action names.

MiniMax validation must be done without committing credentials:

- Set the API key only as a transient environment variable, for example `MINIMAX_API_KEY`.
- Use the global OpenAI-compatible endpoint `https://api.minimax.io/v1/chat/completions` with model `MiniMax-M2.7`.
- Recommended validation settings: `temperature: 0.2`; include `extra_body: {"reasoning_split": true}` where supported.
- Use compact batches to ask the model to critique Hán-Việt consistency, instruction clarity, JSON strictness, placeholder preservation, and runtime safety.
- Smoke-test representative rendered prompts from `ai`, `single_choice`, `conversation`, `mutual_action`, `relation_update`, `sect_decider`, `sect_thinker`, and one `story_*` template; parse JSON responses and verify expected keys.

Do not write API keys into repo files, shell history, docs, test fixtures, or committed logs.
