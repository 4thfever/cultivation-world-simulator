param(
    [string]$BuildVersion = "",
    [switch]$Preview,
    [switch]$NoBuild,
    [string]$ContentRoot = "",
    [switch]$SkipNpmInstall,
    [switch]$RequireUpload
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path
$ContentRootMarker = Join-Path $RepoRoot "tmp\desktop_content_root.txt"

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
if (-not $BuildVersion) {
    $BuildVersion = "$tag-desktop"
}

Write-Host "=== Publish desktop package to Epic ===" -ForegroundColor Cyan
Write-Host "Tag: $tag"
Write-Host "Build version: $BuildVersion"
Write-Host "Preview: $Preview"
Write-Host "NoBuild: $NoBuild"
Write-Host "Require upload: $RequireUpload"

if (-not $NoBuild) {
    $PackScript = Join-Path $ScriptDir "pack_desktop.ps1"
    $PackArgs = @("-BuildDesc", $BuildVersion)
    if ($SkipNpmInstall) {
        $PackArgs += "-SkipNpmInstall"
    }

    Write-Host "`n>>> Step 1/3: Building desktop Electron package..." -ForegroundColor Cyan
    & powershell -NoProfile -ExecutionPolicy Bypass -File $PackScript @PackArgs
    if ($LASTEXITCODE -ne 0) {
        throw "pack_desktop.ps1 failed with exit code $LASTEXITCODE"
    }
}
else {
    Write-Host "`n>>> Step 1/3: Skipping desktop build because -NoBuild was provided." -ForegroundColor Yellow
}

Write-Host "`n>>> Step 2/3: Resolving content root..." -ForegroundColor Cyan
if (-not $ContentRoot) {
    if (-not (Test-Path $ContentRootMarker)) {
        throw "Content root marker not found: $ContentRootMarker"
    }
    $ContentRoot = (Get-Content $ContentRootMarker -Raw).Trim()
}
if (-not $ContentRoot -or -not (Test-Path $ContentRoot)) {
    throw "Content root is invalid: $ContentRoot"
}

Write-Host "Content root: $ContentRoot"

Write-Host "`n>>> Step 3/3: Publishing to Epic..." -ForegroundColor Cyan
$PublishScript = Join-Path $ScriptDir "epic\publish.ps1"
$PublishArgs = @(
    "-ContentRoot", $ContentRoot,
    "-BuildVersion", $BuildVersion
)
if ($Preview) {
    $PublishArgs += "-Preview"
}
if ($RequireUpload) {
    $PublishArgs += "-RequireUpload"
}

& powershell -NoProfile -ExecutionPolicy Bypass -File $PublishScript @PublishArgs
if ($LASTEXITCODE -ne 0) {
    throw "epic/publish.ps1 failed with exit code $LASTEXITCODE"
}

Write-Host "`n=== Epic publish placeholder completed ===" -ForegroundColor Green
Write-Host "Build version: $BuildVersion"
Write-Host "Content root: $ContentRoot"
