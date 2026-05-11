param(
    [Parameter(Mandatory = $true)][string]$ContentRoot,
    [string]$BuildVersion = "",
    [switch]$Preview,
    [switch]$RequireUpload
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..\..\..")).Path
$EpicDir = $ScriptDir

function Import-EnvFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path
    )

    if (-not (Test-Path $Path)) {
        return
    }

    Get-Content $Path | ForEach-Object {
        $line = $_.Trim()
        if ($line -match "^#" -or $line -eq "") { return }
        if ($line -match "^([^=]+)=(.*)$") {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            Set-Item -Path "Env:$key" -Value $value
        }
    }
}

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

if (-not (Test-Path $ContentRoot)) {
    throw "Build output not found: $ContentRoot`nRun pack_desktop.ps1 before uploading."
}

if (-not $BuildVersion) {
    $BuildVersion = "$(Get-GitTag)-desktop"
}

$ContentRoot = (Resolve-Path $ContentRoot).Path
$EnvFile = Join-Path $EpicDir "epic_config.env"
Import-EnvFile -Path $EnvFile

Write-Host "=== Epic desktop upload placeholder ===" -ForegroundColor Cyan
Write-Host "Build version: $BuildVersion"
Write-Host "Content root: $ContentRoot"
if ($Preview) {
    Write-Host "Preview mode: Epic upload would be skipped." -ForegroundColor Yellow
}

$message = "Epic upload is not implemented yet. Add Epic distribution tool settings to tools/package/epic/epic_config.env and wire the official upload command here."
if ($RequireUpload) {
    throw $message
}

Write-Host $message -ForegroundColor Yellow
Write-Host "Desktop package is ready. Exiting successfully because Epic publishing is currently a placeholder." -ForegroundColor Green
