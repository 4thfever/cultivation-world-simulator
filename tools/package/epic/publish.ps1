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

function Require-ConfigValue {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [string]$Value,
        [string[]]$Missing
    )

    if (-not $Value) {
        return @($Missing + $Name)
    }
    return $Missing
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

$BuildPatchTool = $env:EPIC_BUILD_PATCH_TOOL_PATH
$OrganizationId = $env:EPIC_ORGANIZATION_ID
$ProductId = $env:EPIC_PRODUCT_ID
$ArtifactId = $env:EPIC_ARTIFACT_ID
$ClientId = $env:EPIC_CLIENT_ID
$ClientSecretEnvVar = $env:EPIC_CLIENT_SECRET_ENV_VAR
$CloudDir = $env:EPIC_CLOUD_DIR
$AppLaunch = $env:EPIC_APP_LAUNCH
$AppArgs = $env:EPIC_APP_ARGS
$FileIgnoreList = $env:EPIC_FILE_IGNORE_LIST

if (-not $ClientSecretEnvVar) {
    $ClientSecretEnvVar = "EPIC_CLIENT_SECRET"
}
if (-not $CloudDir) {
    $CloudDir = Join-Path $RepoRoot "tmp\epic\cloud"
}
elseif (-not [System.IO.Path]::IsPathRooted($CloudDir)) {
    $CloudDir = Join-Path $RepoRoot $CloudDir
}
if (-not $AppLaunch) {
    $AppLaunch = "CultivationWorldSimulator.exe"
}

$Missing = @()
$Missing = Require-ConfigValue -Name "EPIC_BUILD_PATCH_TOOL_PATH" -Value $BuildPatchTool -Missing $Missing
$Missing = Require-ConfigValue -Name "EPIC_ORGANIZATION_ID" -Value $OrganizationId -Missing $Missing
$Missing = Require-ConfigValue -Name "EPIC_PRODUCT_ID" -Value $ProductId -Missing $Missing
$Missing = Require-ConfigValue -Name "EPIC_ARTIFACT_ID" -Value $ArtifactId -Missing $Missing
$Missing = Require-ConfigValue -Name "EPIC_CLIENT_ID" -Value $ClientId -Missing $Missing

Write-Host "=== Epic desktop upload ===" -ForegroundColor Cyan
Write-Host "Build version: $BuildVersion"
Write-Host "Content root: $ContentRoot"
Write-Host "Config file: $EnvFile"
Write-Host "BuildPatchTool: $BuildPatchTool"
Write-Host "ArtifactId: $ArtifactId"
Write-Host "AppLaunch: $AppLaunch"
Write-Host "CloudDir: $CloudDir"

if ($Missing.Count -gt 0) {
    $message = "Epic upload config is incomplete. Missing: $($Missing -join ', '). Copy tools/package/epic/epic_config.env.example to epic_config.env and fill it."
    if ($RequireUpload) {
        throw $message
    }

    Write-Host $message -ForegroundColor Yellow
    Write-Host "Desktop package is ready. Skipping Epic upload because -RequireUpload was not provided." -ForegroundColor Green
    exit 0
}

$ClientSecret = [Environment]::GetEnvironmentVariable($ClientSecretEnvVar)
if ($RequireUpload -and -not $ClientSecret) {
    $SecureSecret = Read-Host "Enter Epic BuildPatchTool client secret for $ClientId" -AsSecureString
    $ClientSecret = (New-Object System.Management.Automation.PSCredential ("epic", $SecureSecret)).GetNetworkCredential().Password
    Set-Item -Path "Env:$ClientSecretEnvVar" -Value $ClientSecret
}

if ($RequireUpload -and -not $ClientSecret) {
    throw "Epic client secret is required for upload. Set $ClientSecretEnvVar or enter it when prompted."
}

if (-not (Test-Path $BuildPatchTool)) {
    $message = "BuildPatchTool.exe not found: $BuildPatchTool"
    if ($RequireUpload) {
        throw $message
    }

    Write-Host $message -ForegroundColor Yellow
    Write-Host "Desktop package is ready. Skipping Epic upload because -RequireUpload was not provided." -ForegroundColor Green
    exit 0
}

New-Item -ItemType Directory -Force -Path $CloudDir | Out-Null

$ArgsList = @(
    "-mode=UploadBinary",
    "-BuildRoot=$ContentRoot",
    "-CloudDir=$CloudDir",
    "-ArtifactId=$ArtifactId",
    "-BuildVersion=$BuildVersion",
    "-AppLaunch=$AppLaunch",
    "-AppArgs=$AppArgs",
    "-ClientId=$ClientId",
    "-ClientSecretEnvVar=$ClientSecretEnvVar",
    "-OrganizationId=$OrganizationId",
    "-ProductId=$ProductId"
)

if ($FileIgnoreList) {
    $ArgsList += "-FileIgnoreList=$FileIgnoreList"
}

Write-Host "Prepared BuildPatchTool command. Client secret is passed via env var: $ClientSecretEnvVar" -ForegroundColor Cyan

if ($Preview -or -not $RequireUpload) {
    Write-Host "`n[Preview] Epic upload was not executed. Add -RequireUpload to upload." -ForegroundColor Yellow
    Write-Host "& `"$BuildPatchTool`" $($ArgsList -join ' ')" -ForegroundColor Gray
    exit 0
}

Write-Host "`n>>> [Upload] Starting Epic BuildPatchTool upload..." -ForegroundColor Cyan
try {
    & $BuildPatchTool @ArgsList
    if ($LASTEXITCODE -ne 0) {
        throw "BuildPatchTool failed with exit code $LASTEXITCODE."
    }
    Write-Host "`n[Success] Uploaded this build to Epic." -ForegroundColor Green
}
finally {
    Set-Item -Path "Env:$ClientSecretEnvVar" -Value ""
}
