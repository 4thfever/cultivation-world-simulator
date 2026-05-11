param(
    [switch]$Preview,
    [switch]$NoBuild
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path

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
$ZipFileName = "AI_Cultivation_World_Simulator_${tag}.zip"
$ZipPath = Join-Path $RepoRoot "tmp\$ZipFileName"

Write-Host "=== Publish GitHub release package ===" -ForegroundColor Cyan
Write-Host "Tag: $tag"
Write-Host "Zip path: $ZipPath"
Write-Host "Preview: $Preview"
Write-Host "NoBuild: $NoBuild"

if (-not $NoBuild) {
    Write-Host "`n>>> Step 1/3: Building GitHub package..." -ForegroundColor Cyan
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $ScriptDir "pack_github.ps1")
    if ($LASTEXITCODE -ne 0) {
        throw "pack_github.ps1 failed with exit code $LASTEXITCODE"
    }

    Write-Host "`n>>> Step 2/3: Compressing GitHub package..." -ForegroundColor Cyan
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $ScriptDir "compress.ps1")
    if ($LASTEXITCODE -ne 0) {
        throw "compress.ps1 failed with exit code $LASTEXITCODE"
    }
}
else {
    Write-Host "`n>>> Step 1/3: Skipping GitHub build and compression because -NoBuild was provided." -ForegroundColor Yellow
    if (-not (Test-Path $ZipPath)) {
        throw "Archive not found for -NoBuild publish: $ZipPath"
    }
}

Write-Host "`n>>> Step 3/3: Publishing GitHub release asset..." -ForegroundColor Cyan
if ($Preview) {
    Write-Host "Preview mode: GitHub release upload was not executed." -ForegroundColor Yellow
    Write-Host "Would upload: $ZipPath"
    exit 0
}

& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $ScriptDir "release.ps1")
if ($LASTEXITCODE -ne 0) {
    throw "release.ps1 failed with exit code $LASTEXITCODE"
}

Write-Host "`n=== GitHub publish pipeline completed ===" -ForegroundColor Green
