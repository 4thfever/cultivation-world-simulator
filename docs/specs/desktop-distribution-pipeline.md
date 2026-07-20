# Desktop distribution pipeline

This document records the current desktop packaging split after moving away from
the Steam-specific Electron pipeline.

For the short command list, see `docs/packaging.md`.

## Current Shape

1. `tools/package/pack_desktop.ps1` is the stable desktop build entry.
2. It delegates to `tools/package/desktop/pack.ps1`, which builds the web frontend, packages the Python backend with PyInstaller,
   builds the Electron shell, and copies the final unpacked Windows package to
   `tmp/<tag>_desktop/win-unpacked`.
3. The resolved content root is written to `tmp/desktop_content_root.txt`.
4. Store upload scripts must consume that content root instead of rebuilding or
   guessing platform-specific output directories.
5. Desktop packaging has an explicit distribution flag. Generic builds are the
   default; Epic publishing calls the same desktop packer with
   `-Distribution epic` so Epic-only runtime resources stay out of GitHub and
   generic desktop packages.

## Desktop Private Seed

Private default LLM values are configured through
`tools/package/desktop/desktop_seed.env`, copied from
`tools/package/desktop/desktop_seed.env.example`.

Only `CWS_DEFAULT_LLM_*` values are included in the generated
`desktop-seed.json` resource. Real keys must not be committed, logged, or
written into `settings.json` / `secrets.json`.

## Platform Upload Layers

`tools/package/publish_epic.ps1` is the Epic publishing entry. It builds the
desktop package and then calls `tools/package/epic/publish.ps1`, which wraps
Epic's BuildPatchTool `UploadBinary` mode. The real upload only runs with
`-RequireUpload`; otherwise the script validates available configuration and
prints a preview command.

Epic runtime EOS Metrics configuration is separate from BuildPatchTool upload
configuration. Local EOS runtime values live in ignored
`tools/package/epic/eos_runtime.env`, copied from
`tools/package/epic/eos_runtime.env.example`. When the runtime config and a
prepared `eos-helper.exe` directory are both available, Epic packaging includes
`desktop-distribution.json`, `eos-runtime.json`, and `eos-helper/` resources.
Without those pieces, EOS Metrics is disabled for that package unless
`-RequireEosRuntime` is supplied.

`tools/package/publish_steam.ps1` is the Steam publishing entry. It reuses
`pack_desktop.ps1` and no longer owns the desktop build layout.

`tools/package/publish_github.ps1` is separate from the desktop store targets.
It runs the GitHub release flow: `pack_github.ps1`, `compress.ps1`, then
`release.ps1`.

## Command Cheat Sheet

Pack only:

```powershell
powershell ./tools/package/pack_github.ps1
powershell ./tools/package/pack_desktop.ps1
```

Publish:

```powershell
powershell ./tools/package/publish_github.ps1
powershell ./tools/package/publish_steam.ps1
powershell ./tools/package/publish_epic.ps1
powershell ./tools/package/publish_epic.ps1 -RequireEosRuntime
powershell ./tools/package/publish_epic.ps1 -EosEnv dev -RequireEosRuntime
```

Epic publishing requires a local `tools/package/epic/epic_config.env` copied
from the example file. Product IDs may live in that ignored file. The client
secret should be supplied through the `EPIC_CLIENT_SECRET` environment variable
in the current terminal before running with `-RequireUpload`.

## Verification

Relevant contract tests live in `tests/test_package_contract.py`.
