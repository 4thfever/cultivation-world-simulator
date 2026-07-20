# Packaging Commands

`pack_*` commands only build local artifacts. `publish_*` commands build first,
then publish to a release channel or store.

## Pack

```powershell
powershell ./tools/package/pack_github.ps1
powershell ./tools/package/pack_desktop.ps1
```

## Publish

```powershell
powershell ./tools/package/publish_github.ps1
powershell ./tools/package/publish_steam.ps1
powershell ./tools/package/publish_epic.ps1
```

`publish_epic.ps1` uses Epic's BuildPatchTool when
`tools/package/epic/epic_config.env` is configured. Without `-RequireUpload`,
the Epic step stays in preview mode and prints the prepared command without
executing the upload.

Epic packages are built with `-Distribution epic` internally. EOS Metrics is
enabled only when `tools/package/epic/eos_runtime.env` is configured and a
prepared `eos-helper.exe` directory is available. The default EOS target is the
Live deployment; use `-EosEnv dev` only for an explicit Dev artifact test.
Use `-RequireEosRuntime` when an Epic build must fail instead of silently
disabling EOS Metrics.

## One Entry

```powershell
powershell ./tools/package/task.ps1 -List
powershell ./tools/package/task.ps1 -Action pack -Target desktop
powershell ./tools/package/task.ps1 -Action publish -Target steam -Preview
```

## Common Retries

```powershell
powershell ./tools/package/publish_github.ps1 -NoBuild
powershell ./tools/package/publish_steam.ps1 -NoBuild -Preview
powershell ./tools/package/publish_epic.ps1 -NoBuild
powershell ./tools/package/publish_epic.ps1 -NoBuild -RequireUpload
powershell ./tools/package/publish_epic.ps1 -RequireEosRuntime
powershell ./tools/package/publish_epic.ps1 -EosEnv dev -RequireEosRuntime
```

Use `publish_epic.ps1 -RequireUpload` only after the Epic distribution tooling
is configured and the `EPIC_CLIENT_SECRET` environment variable is set in your
current terminal.

## What I Want

| Goal | Command |
|---|---|
| Build GitHub executable directory | `powershell ./tools/package/pack_github.ps1` |
| Build desktop Electron package | `powershell ./tools/package/pack_desktop.ps1` |
| Publish GitHub Release | `powershell ./tools/package/publish_github.ps1` |
| Publish Steam | `powershell ./tools/package/publish_steam.ps1` |
| Prepare Epic desktop package | `powershell ./tools/package/publish_epic.ps1` |
| Upload Epic desktop package | `powershell ./tools/package/publish_epic.ps1 -RequireUpload` |
