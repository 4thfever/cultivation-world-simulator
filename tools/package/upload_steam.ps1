param(
    [Parameter(Mandatory = $true)][string]$ContentRoot,
    [string]$BuildDesc = "",
    [string]$Branch = "",
    [switch]$Preview
)

$ErrorActionPreference = "Stop"

# ==============================================================================
# 0. Environment and path setup
# ==============================================================================
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path
$SteamDir = Join-Path $ScriptDir "steam"

function Import-EnvFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path
    )

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

# ==============================================================================
# 1. Load Steam config
# ==============================================================================
$EnvFile = Join-Path $SteamDir "steam_config.env"
if (-not (Test-Path $EnvFile)) {
    Write-Error "Steam config file not found: $EnvFile`nCopy steam_config.env.example to steam_config.env and fill in Steamworks fields."
    exit 1
}

Write-Host ">>> Loading Steam config..." -ForegroundColor Cyan
Import-EnvFile -Path $EnvFile

$SteamUser = $env:STEAM_USERNAME
$SteamPass = $env:STEAM_PASSWORD
$AppID = $env:STEAM_APP_ID
$DepotID = $env:STEAM_DEPOT_ID
$SteamCmd = $env:STEAM_CMD_PATH

if (-not $SteamUser -or -not $AppID -or -not $DepotID -or -not $SteamCmd) {
    Write-Error "steam_config.env is missing required fields. Check all fields except password."
    exit 1
}

if (-not $Preview -and -not $SteamPass) {
    $SecurePass = Read-Host "Enter Steam password for $SteamUser" -AsSecureString
    $SteamPass = (New-Object System.Management.Automation.PSCredential ("user", $SecurePass)).GetNetworkCredential().Password
}

if (-not $Preview -and -not (Test-Path $SteamCmd)) {
    Write-Error "steamcmd.exe not found: $SteamCmd"
    exit 1
}

# ==============================================================================
# 2. Resolve build version and content root
# ==============================================================================
$tag = Get-GitTag
if (-not $BuildDesc) {
    $BuildDesc = $tag
}

if (-not (Test-Path $ContentRoot)) {
    Write-Error "Build output not found: $ContentRoot`nRun the matching pack script before uploading."
    exit 1
}

$ContentRoot = (Resolve-Path $ContentRoot).Path

Write-Host ">>> Target build desc: $BuildDesc" -ForegroundColor Cyan
Write-Host ">>> ContentRoot: $ContentRoot" -ForegroundColor Cyan
if ($Branch) {
    Write-Host ">>> SetLive branch: $Branch" -ForegroundColor Cyan
}
else {
    Write-Host ">>> SetLive branch: <empty>; push this build manually in Steamworks after upload." -ForegroundColor Yellow
}

# ==============================================================================
# 3. Prepare output directories
# ==============================================================================
$TmpSteamDir = Join-Path $RepoRoot "tmp\steam"
New-Item -ItemType Directory -Force -Path $TmpSteamDir | Out-Null

$BuildOutputDir = Join-Path $TmpSteamDir "output"
New-Item -ItemType Directory -Force -Path $BuildOutputDir | Out-Null

$AppVdfOut = Join-Path $TmpSteamDir "app_build.vdf"
$DepotVdfOut = Join-Path $TmpSteamDir "depot_build.vdf"

# ==============================================================================
# 4. Generate VDF files
# ==============================================================================
Write-Host ">>> Generating VDF files..." -ForegroundColor Cyan

$ContentRootEscaped = $ContentRoot -replace "\\", "\\"
$BuildOutputEscaped = $BuildOutputDir -replace "\\", "\\"
$DepotVdfOutEscaped = $DepotVdfOut -replace "\\", "\\"

$DepotTemplate = Get-Content (Join-Path $SteamDir "depot_build.vdf.template") -Raw
$DepotContent = $DepotTemplate.Replace('${STEAM_DEPOT_ID}', $DepotID)
$DepotContent = $DepotContent.Replace('${CONTENT_ROOT_DIR}', $ContentRootEscaped)
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($DepotVdfOut, $DepotContent, $utf8NoBom)

$AppTemplate = Get-Content (Join-Path $SteamDir "app_build.vdf.template") -Raw
$AppContent = $AppTemplate.Replace('${STEAM_APP_ID}', $AppID)
$AppContent = $AppContent.Replace('${BUILD_DESC}', $BuildDesc)
$AppContent = $AppContent.Replace('${BUILD_OUTPUT_DIR}', $BuildOutputEscaped)
$AppContent = $AppContent.Replace('${STEAM_DEPOT_ID}', $DepotID)
$AppContent = $AppContent.Replace('${DEPOT_BUILD_VDF_PATH}', $DepotVdfOutEscaped)
$AppContent = $AppContent.Replace('${SET_LIVE_BRANCH}', $Branch)
[System.IO.File]::WriteAllText($AppVdfOut, $AppContent, $utf8NoBom)

Write-Host ">>> App VDF: $AppVdfOut" -ForegroundColor Gray
Write-Host ">>> Depot VDF: $DepotVdfOut" -ForegroundColor Gray

if ($Preview) {
    Write-Host "`n[Preview] Generated VDF files. SteamCMD upload was not executed." -ForegroundColor Yellow
    exit 0
}

# ==============================================================================
# 5. Upload to Steam
# ==============================================================================
Write-Host "`n>>> [Upload] Starting SteamCMD upload..." -ForegroundColor Cyan

$argsList = @(
    "+login", $SteamUser, $SteamPass,
    "+run_app_build", $AppVdfOut,
    "+quit"
)

try {
    & $SteamCmd @argsList

    if ($LASTEXITCODE -ne 0) {
        throw "SteamCMD failed with exit code $LASTEXITCODE. Check SteamCMD logs above and in the Steam ContentBuilder logs directory."
    }
    Write-Host "`n[Success] Uploaded this build to Steam." -ForegroundColor Green
    if ($Branch) {
        Write-Host "Requested setlive branch: $Branch" -ForegroundColor Cyan
    }
    else {
        Write-Host "Open Steamworks, find this build under SteamPipe builds, and push it to the target branch." -ForegroundColor Cyan
    }
} catch {
    Write-Error "Upload failed: $_"
    exit 1
} finally {
    Set-Item -Path "Env:STEAM_PASSWORD" -Value ""
}
