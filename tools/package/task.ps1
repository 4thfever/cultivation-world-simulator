param(
    [ValidateSet("pack", "publish")][string]$Action = "",
    [ValidateSet("github", "desktop", "steam", "epic")][string]$Target = "",
    [switch]$List,
    [switch]$Preview,
    [switch]$NoBuild,
    [switch]$RequireUpload,
    [string]$BuildVersion = "",
    [string]$ContentRoot = "",
    [string]$Branch = "",
    [switch]$SkipNpmInstall,
    [ValidateSet("dev", "live")][string]$EosEnv = "live",
    [switch]$RequireEosRuntime
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

function Show-TaskList {
    Write-Host "Pack:" -ForegroundColor Cyan
    Write-Host "  github   Build GitHub release executable directory only."
    Write-Host "  desktop  Build desktop Electron package only."
    Write-Host ""
    Write-Host "Publish:" -ForegroundColor Cyan
    Write-Host "  github   Build, compress, and upload GitHub Release asset."
    Write-Host "  steam    Build desktop package and publish to Steam."
    Write-Host "  epic     Build desktop package and enter Epic BuildPatchTool publishing flow."
}

if ($List) {
    Show-TaskList
    exit 0
}

if (-not $Action -or -not $Target) {
    Show-TaskList
    throw "Specify both -Action and -Target, or use -List."
}

$ScriptName = $null
if ($Action -eq "pack") {
    if ($Target -eq "github") {
        $ScriptName = "pack_github.ps1"
    }
    elseif ($Target -eq "desktop") {
        $ScriptName = "pack_desktop.ps1"
    }
    else {
        throw "Pack target '$Target' is not supported. Use 'github' or 'desktop'."
    }
}
elseif ($Action -eq "publish") {
    if ($Target -eq "github") {
        $ScriptName = "publish_github.ps1"
    }
    elseif ($Target -eq "steam") {
        $ScriptName = "publish_steam.ps1"
    }
    elseif ($Target -eq "epic") {
        $ScriptName = "publish_epic.ps1"
    }
    else {
        throw "Publish target '$Target' is not supported. Use 'github', 'steam', or 'epic'."
    }
}

$TaskArgs = @()
if ($Action -eq "pack" -and $Target -eq "desktop") {
    if ($BuildVersion) { $TaskArgs += @("-BuildDesc", $BuildVersion) }
    if ($SkipNpmInstall) { $TaskArgs += "-SkipNpmInstall" }
}
elseif ($Action -eq "publish") {
    if ($BuildVersion) { $TaskArgs += @("-BuildVersion", $BuildVersion) }
    if ($Preview) { $TaskArgs += "-Preview" }
    if ($NoBuild) { $TaskArgs += "-NoBuild" }
    if ($ContentRoot) { $TaskArgs += @("-ContentRoot", $ContentRoot) }
    if ($Branch -and $Target -eq "steam") { $TaskArgs += @("-Branch", $Branch) }
    if ($RequireUpload -and $Target -eq "epic") { $TaskArgs += "-RequireUpload" }
    if ($SkipNpmInstall -and ($Target -eq "steam" -or $Target -eq "epic")) { $TaskArgs += "-SkipNpmInstall" }
    if ($Target -eq "epic") { $TaskArgs += @("-EosEnv", $EosEnv) }
    if ($RequireEosRuntime -and $Target -eq "epic") { $TaskArgs += "-RequireEosRuntime" }
}

$ScriptPath = Join-Path $ScriptDir $ScriptName
Write-Host "Running package task: $Action $Target" -ForegroundColor Cyan
& powershell -NoProfile -ExecutionPolicy Bypass -File $ScriptPath @TaskArgs
if ($LASTEXITCODE -ne 0) {
    throw "$ScriptName failed with exit code $LASTEXITCODE"
}
