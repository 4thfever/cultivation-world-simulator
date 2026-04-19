# Static Resource Path Hardening

## Background

Issue `#192` exposed a startup failure when the process was launched from a non-project working directory. The immediate crash happened in `src/utils/config.py` while reading `static/config.yml` through a relative path, which then cascaded into missing `CONFIG.resources`.

After fixing that entry point, a second same-class failure appeared in `src/classes/story_teller.py`, which still loaded `static/story_styles.json` relative to the current working directory. This shows the problem is broader than one file: the repo contains a mix of runtime code, tool scripts, and tests that assume `cwd == project root`.

## Problem Statement

The project must be able to:

1. Import and start backend runtime modules without depending on the caller's current working directory.
2. Execute repo-owned maintenance scripts from arbitrary launch directories as long as the repo itself is available.
3. Keep tests deterministic even when pytest or subprocess-based runners change working directory.

## Goals

1. Eliminate cwd-sensitive static resource reads in backend runtime code.
2. Eliminate cwd-sensitive static resource reads in repo-owned Python tools that operate on `static/`.
3. Update tests that directly open static files so they resolve paths from project root instead of ambient cwd.
4. Add regression coverage for non-project cwd startup/import behavior.

## Non-Goals

1. Do not rewrite frontend build-time imports such as `web/src/... -> ../../../static/...`; those are handled by the bundler, not Python runtime cwd.
2. Do not change documentation-only string literals that mention `static/...`.
3. Do not introduce backward-compatibility shims for old path conventions beyond zero-cost safe defaults.

## Findings From Repository Scan

### Must Harden

- `src/utils/config.py`
  - Reads `static/config.yml`
  - Produces runtime resource paths consumed during import/startup
- `src/classes/story_teller.py`
  - Reads `static/story_styles.json`
- `src/i18n/template_resolver.py`
  - Had a relative fallback for `static/locales`
- `tools/i18n/align_po_files.py`
  - Reads `static/locales`
- `tools/i18n/align_po_files_preview.py`
  - Reads `static/locales`
  - Wrote preview output relative to cwd
- `tools/i18n/split_po.py`
  - Reads `static/locales`
- `tools/migrate_assets_and_map.py`
  - Reads `static/game_configs`
  - Reads `assets/sects`
- Tests that open templates or configs with `Path("static/...")`
  - `tests/test_language.py`
  - `tests/test_sect_thinker.py`
  - `tests/tools/test_prompt_template_format.py`

### Safe To Leave As-Is

- Frontend source imports like `web/src/locales/registry.ts` and `web/src/utils/worldInfo.ts`
  - These are module-resolution inputs for Vite, not runtime cwd-dependent Python file I/O.
- Contract tests asserting literal copy sources such as `"static/locales/registry.json"`
  - These validate Docker/build semantics, not filesystem lookup behavior.
- Comments/docstrings mentioning `static/...`
  - Informational only.

## Design Decisions

### Single Source of Truth For Project Root

Use `src.i18n.locale_registry.get_project_root()` where runtime code already depends on app-side helpers.

For standalone tool scripts, either:

1. Reuse an existing project-root helper when import-safe, or
2. Compute `PROJECT_ROOT = Path(__file__).resolve().parents[...]` locally when that keeps the script simpler and more robust.

### Path Resolution Rule

When code needs to read repo-owned static assets at runtime, always resolve from project root:

- `get_project_root() / "static" / ...`
- `PROJECT_ROOT / "static" / ...`

Do not rely on:

- `Path("static/...")`
- `Path("assets/...")`
- output files implicitly landing in the caller's cwd unless that behavior is explicitly intended

### Runtime Config Safety

If static config loading fails to provide optional sections such as `resources`, runtime code should use safe defaults rooted at project root rather than raising on import.

## Implemented Changes

1. Hardened runtime config loading in `src/utils/config.py`.
2. Hardened story style loading in `src/classes/story_teller.py`.
3. Hardened locale template fallback in `src/i18n/template_resolver.py`.
4. Hardened cwd-sensitive tool scripts:
   - `tools/i18n/align_po_files.py`
   - `tools/i18n/align_po_files_preview.py`
   - `tools/i18n/split_po.py`
   - `tools/migrate_assets_and_map.py`
5. Updated direct-file-reading tests to use project-root paths.
6. Added subprocess regression coverage for importing `src.server.main` from a non-project cwd.

## Risks And Tradeoffs

1. Tool scripts now write/read against repo-root locations even when launched elsewhere.
   - This is desired for repo maintenance scripts, but it intentionally changes behavior for anyone who used cwd redirection as an implicit input.
2. Mixed root-resolution styles remain possible across the repo if future code bypasses the helper.
   - Mitigation: keep regression tests and code review guidance focused on repo-owned static file access.
3. Some non-runtime helper scripts may still contain relative paths outside the scanned scope.
   - Current scan focused on Python code that performs real static file I/O, which is the failure mode observed in `#192`.

## Acceptance Criteria

1. Importing backend entry modules from a non-project cwd does not fail because repo-owned static files cannot be found.
2. `src.utils.config.update_paths_for_language()` works even if `resources` is absent from the loaded config object.
3. Template-reading tests do not depend on ambient cwd.
4. Repo-owned i18n and migration tools updated in this change resolve `static/` and `assets/` from project root.
5. Existing targeted regression tests pass.

## Validation Plan

1. Run `pytest tests/test_server_binding.py tests/test_language.py`.
2. Run `pytest tests/test_sect_thinker.py tests/tools/test_prompt_template_format.py`.
3. Verify subprocess-based import smoke test passes from a non-project cwd.

## Follow-Up Guidance

When adding any new Python file that reads repo-owned assets, prefer one of these patterns from the start:

```python
from src.i18n.locale_registry import get_project_root

path = get_project_root() / "static" / "..."
```

or

```python
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[<n>]
path = PROJECT_ROOT / "static" / "..."
```
