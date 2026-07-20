param(
    [string]$BuildDesc = "",
    [switch]$SkipNpmInstall,
    [ValidateSet("generic", "epic")][string]$Distribution = "generic",
    [ValidateSet("dev", "live")][string]$EosEnv = "live",
    [switch]$RequireEosRuntime
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
$ArgsList += @("-Distribution", $Distribution)
$ArgsList += @("-EosEnv", $EosEnv)
if ($RequireEosRuntime) {
    $ArgsList += "-RequireEosRuntime"
}

& powershell -NoProfile -ExecutionPolicy Bypass -File $PackScript @ArgsList
if ($LASTEXITCODE -ne 0) {
    throw "desktop/pack.ps1 failed with exit code $LASTEXITCODE"
}
