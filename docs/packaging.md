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

`publish_epic.ps1` is currently a placeholder after the desktop build step. Wire
the Epic distribution tool in `tools/package/epic/publish.ps1` before using it
for a real upload.

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
```

Use `publish_epic.ps1 -RequireUpload` only after the Epic distribution tooling
is configured.

## What I Want

| Goal | Command |
|---|---|
| Build GitHub executable directory | `powershell ./tools/package/pack_github.ps1` |
| Build desktop Electron package | `powershell ./tools/package/pack_desktop.ps1` |
| Publish GitHub Release | `powershell ./tools/package/publish_github.ps1` |
| Publish Steam | `powershell ./tools/package/publish_steam.ps1` |
| Prepare Epic desktop package | `powershell ./tools/package/publish_epic.ps1` |
