param(
    [string]$BuildDesc = "",
    [switch]$SkipNpmInstall
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PackScript = Join-Path $ScriptDir "desktop\pack.ps1"

$ArgsList = @()
if ($BuildDesc) {
    $ArgsList += @("-BuildDesc", $BuildDesc)
}
if ($SkipNpmInstall) {
    $ArgsList += "-SkipNpmInstall"
}

& powershell -NoProfile -ExecutionPolicy Bypass -File $PackScript @ArgsList
if ($LASTEXITCODE -ne 0) {
    throw "desktop/pack.ps1 failed with exit code $LASTEXITCODE"
}
