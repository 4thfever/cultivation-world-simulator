param(
    [string]$BuildDesc = "",
    [string]$Branch = "",
    [switch]$PreviewUpload,
    [switch]$SkipNpmInstall
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path
$ContentRootMarker = Join-Path $RepoRoot "tmp\steam_electron_content_root.txt"

function Get-GitTag {
    Push-Location $RepoRoot
    try {
        $tag = git describe --tags --abbrev=0 2>$null
        if (-not $tag) {
            throw "Git tag not found"
        }
        return $tag.Trim()
    }
    finally {
        Pop-Location
    }
}

$tag = Get-GitTag
if (-not $BuildDesc) {
    $BuildDesc = "$tag-electron"
}

Write-Host "=== Steam Electron build and upload ===" -ForegroundColor Cyan
Write-Host "Tag: $tag"
Write-Host "Build desc: $BuildDesc"
if ($Branch) {
    Write-Host "SetLive branch: $Branch"
}
else {
    Write-Host "SetLive branch: <empty>; upload will not auto-push live."
}

$PackScript = Join-Path $ScriptDir "pack_steam_electron.ps1"
$UploadScript = Join-Path $ScriptDir "upload_steam.ps1"

$PackArgs = @("-BuildDesc", $BuildDesc)
if ($SkipNpmInstall) {
    $PackArgs += "-SkipNpmInstall"
}

Write-Host "`n>>> Step 1/3: Building Steam Electron package..." -ForegroundColor Cyan
& powershell -NoProfile -ExecutionPolicy Bypass -File $PackScript @PackArgs
if ($LASTEXITCODE -ne 0) {
    throw "pack_steam_electron.ps1 failed with exit code $LASTEXITCODE"
}

Write-Host "`n>>> Step 2/3: Reading content root marker..." -ForegroundColor Cyan
if (-not (Test-Path $ContentRootMarker)) {
    throw "Content root marker not found: $ContentRootMarker"
}

$ContentRoot = (Get-Content $ContentRootMarker -Raw).Trim()
if (-not $ContentRoot -or -not (Test-Path $ContentRoot)) {
    throw "Content root from marker is invalid: $ContentRoot"
}

Write-Host "Content root: $ContentRoot"

Write-Host "`n>>> Step 3/3: Uploading to Steam..." -ForegroundColor Cyan
$UploadArgs = @(
    "-ContentRoot", $ContentRoot,
    "-BuildDesc", $BuildDesc
)
if ($Branch) {
    $UploadArgs += @("-Branch", $Branch)
}
if ($PreviewUpload) {
    $UploadArgs += "-Preview"
}

& powershell -NoProfile -ExecutionPolicy Bypass -File $UploadScript @UploadArgs
if ($LASTEXITCODE -ne 0) {
    throw "upload_steam.ps1 failed with exit code $LASTEXITCODE"
}

Write-Host "`n=== Steam Electron pipeline completed ===" -ForegroundColor Green
Write-Host "Tag: $tag"
Write-Host "Build desc: $BuildDesc"
Write-Host "Content root: $ContentRoot"
if ($PreviewUpload) {
    Write-Host "Upload mode: preview only; SteamCMD was not executed."
}
elseif ($Branch) {
    Write-Host "Upload mode: uploaded and requested setlive branch '$Branch'."
}
else {
    Write-Host "Upload mode: uploaded; push the build to the target branch in Steamworks."
}
