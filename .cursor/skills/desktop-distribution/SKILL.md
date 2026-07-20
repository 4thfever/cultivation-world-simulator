# Desktop Distribution

Use this skill when packaging or publishing desktop builds for GitHub, Steam, or Epic.

## Mental Model

1. `pack_*` commands only build artifacts.
2. `publish_*` commands build and publish to a release channel or store.
3. Desktop store packages share one build truth: `tools/package/desktop/pack.ps1`, exposed through `tools/package/pack_desktop.ps1`.
4. Steam and Epic are publish targets. They must consume the desktop content root instead of duplicating desktop build logic.
5. GitHub release packaging is separate from desktop store publishing.

## Commands

Pack only:

- `powershell ./tools/package/pack_github.ps1`
- `powershell ./tools/package/pack_desktop.ps1`

Publish:

- `powershell ./tools/package/publish_github.ps1`
- `powershell ./tools/package/publish_steam.ps1`
- `powershell ./tools/package/publish_epic.ps1 -RequireEosRuntime`

Epic EOS publishing targets the Live deployment by default. Add `-EosEnv dev`
only when explicitly preparing or uploading a Dev artifact for EOS validation.

Single entry:

- `powershell ./tools/package/task.ps1 -List`
- `powershell ./tools/package/task.ps1 -Action pack -Target desktop`
- `powershell ./tools/package/task.ps1 -Action publish -Target steam -Preview`

## Safety

1. Never echo API keys, Steam passwords, Steam Guard tokens, Epic client secrets, or GitHub tokens.
2. Never commit real `*.env` files.
3. Keep default LLM seed config in `tools/package/desktop/desktop_seed.env`.
4. Keep store credentials only in that store target directory.
5. Run sensitive config scans on packaged output before publishing.
