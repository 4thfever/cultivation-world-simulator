param(
    [string]$BuildDesc = "",
    [switch]$SkipNpmInstall
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path
$SteamDir = Join-Path $ScriptDir "steam"

function Get-GitTag {
    Push-Location $RepoRoot
    try {
        $tagDesc = & git describe --tags --abbrev=0 2>$null
        if ($LASTEXITCODE -eq 0 -and $tagDesc) {
            return $tagDesc.Trim()
        }
        throw "Cannot get git tag. Please run in a Git repository with at least one tag."
    }
    finally {
        Pop-Location
    }
}

function Assert-NoSensitiveConfigs {
    param(
        [Parameter(Mandatory = $true)][string]$RootPath
    )

    $SensitiveConfigNames = @("local_config.yml", "settings.json", "secrets.json")
    $MatchedFiles = Get-ChildItem -Path $RootPath -Include $SensitiveConfigNames -Recurse -Force -ErrorAction SilentlyContinue
    if ($MatchedFiles) {
        $List = ($MatchedFiles | ForEach-Object { $_.FullName }) -join "`n"
        throw "Sensitive config files remain in package:`n$List"
    }
}

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

function Write-SteamSeedFile {
    param(
        [Parameter(Mandatory = $true)][string]$OutputPath
    )

    $SeedKeys = @(
        "CWS_DEFAULT_LLM_BASE_URL",
        "CWS_DEFAULT_LLM_MODEL",
        "CWS_DEFAULT_LLM_FAST_MODEL",
        "CWS_DEFAULT_LLM_API_FORMAT",
        "CWS_DEFAULT_LLM_MODE",
        "CWS_DEFAULT_LLM_MAX_CONCURRENT_REQUESTS",
        "CWS_DEFAULT_LLM_API_KEY"
    )

    $Seed = [ordered]@{}
    foreach ($Key in $SeedKeys) {
        $Value = [Environment]::GetEnvironmentVariable($Key)
        if ($Value) {
            $Seed[$Key] = $Value
        }
    }

    if ($Seed.Count -eq 0) {
        return $false
    }

    $Parent = Split-Path -Parent $OutputPath
    New-Item -ItemType Directory -Force -Path $Parent | Out-Null
    $Json = $Seed | ConvertTo-Json -Depth 3
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($OutputPath, $Json, $utf8NoBom)
    return $true
}

$tag = Get-GitTag
if (-not $BuildDesc) {
    $BuildDesc = "$tag-electron"
}

$DistRoot = Join-Path $RepoRoot ("tmp\" + $tag + "_steam_electron")
$BackendDistRoot = Join-Path $DistRoot "backend_dist"
$BackendBuildDir = Join-Path $RepoRoot ("tmp\build\" + $tag + "_steam_electron_backend")
$BackendSpecDir = Join-Path $RepoRoot ("tmp\spec\" + $tag + "_steam_electron_backend")
$SeedFile = Join-Path $DistRoot "steam-seed.json"
$ContentRootFile = Join-Path $RepoRoot "tmp\steam_electron_content_root.txt"

New-Item -ItemType Directory -Force -Path $DistRoot, $BackendDistRoot, $BackendBuildDir, $BackendSpecDir | Out-Null

Write-Host ">>> Steam Electron package tag: $tag" -ForegroundColor Cyan
Write-Host ">>> Build desc: $BuildDesc" -ForegroundColor Cyan

# Load optional private Steam/LLM settings. This file is ignored by git via *.env rules.
Import-EnvFile -Path (Join-Path $SteamDir "steam_config.env")
$HasSeed = Write-SteamSeedFile -OutputPath $SeedFile
if ($HasSeed) {
    Write-Host "[OK] Prepared Steam private LLM seed file." -ForegroundColor Green
}
else {
    Write-Host "i No CWS_DEFAULT_LLM_* seed values found; building without private LLM seed." -ForegroundColor Yellow
}

# --- Web Frontend Build ---
$WebDir = Join-Path $RepoRoot "web"
$WebDistDir = Join-Path $WebDir "dist"

if (-not (Test-Path $WebDir)) {
    throw "Web directory not found at $WebDir"
}

Push-Location $WebDir
try {
    if (-not (Test-Path "node_modules") -and -not $SkipNpmInstall) {
        Write-Host "Installing web npm dependencies..."
        cmd /c "npm install"
    }
    Write-Host "Building web frontend..."
    cmd /c "npm run build"
    if ($LASTEXITCODE -ne 0) {
        throw "Web build failed."
    }
}
finally {
    Pop-Location
}

# --- Backend PyInstaller Build ---
$EntryPy = Join-Path $RepoRoot "src\server\main.py"
$AppName = "AICultivationSimulator_Steam"
$AssetsPath = Join-Path $RepoRoot "assets"
$StaticPath = Join-Path $RepoRoot "static"
$IconPath = Join-Path $AssetsPath "icon.ico"
$RuntimeHookPath = Join-Path $ScriptDir "runtime_hook_setcwd.py"

if (-not (Test-Path $EntryPy)) {
    throw "Entry script not found: $EntryPy"
}

$PyInstallerArgs = @(
    $EntryPy,
    "--name", $AppName,
    "--onedir",
    "--clean",
    "--noconfirm",
    "--windowed",
    "--distpath", $BackendDistRoot,
    "--workpath", $BackendBuildDir,
    "--specpath", $BackendSpecDir,
    "--paths", $RepoRoot,
    "--additional-hooks-dir", $ScriptDir,
    "--add-data", "${AssetsPath};assets",
    "--add-data", "${StaticPath};static",
    "--exclude-module", "litellm",
    "--exclude-module", "google",
    "--exclude-module", "scipy",
    "--exclude-module", "pygame",
    "--exclude-module", "matplotlib",
    "--exclude-module", "tkinter",
    "--exclude-module", "PyQt5",
    "--exclude-module", "PyQt6",
    "--exclude-module", "PySide2",
    "--exclude-module", "PySide6",
    "--exclude-module", "wx",
    "--exclude-module", "notebook",
    "--exclude-module", "ipython",
    "--exclude-module", "boto3",
    "--exclude-module", "botocore",
    "--exclude-module", "s3transfer",
    "--exclude-module", "azure",
    "--exclude-module", "huggingface_hub",
    "--exclude-module", "transformers",
    "--exclude-module", "tensorflow",
    "--exclude-module", "torch",
    "--exclude-module", "numpy",
    "--exclude-module", "pandas",
    "--exclude-module", "PIL",
    "--exclude-module", "Pillow",
    "--exclude-module", "tiktoken"
)

if (Test-Path $RuntimeHookPath) {
    $PyInstallerArgs += @("--runtime-hook", $RuntimeHookPath)
}
if (Test-Path $IconPath) {
    $PyInstallerArgs += @("--icon", $IconPath)
}

Push-Location $RepoRoot
try {
    Write-Host "Executing PyInstaller for Steam Electron backend..."
    & pyinstaller @PyInstallerArgs
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller execution failed with exit code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}

$BackendExeDir = Join-Path $BackendDistRoot $AppName
if (-not (Test-Path $BackendExeDir)) {
    throw "Backend build finished but executable directory was not found: $BackendExeDir"
}

if (Test-Path $StaticPath) {
    Copy-Item -Path $StaticPath -Destination $BackendExeDir -Recurse -Force
}
if (Test-Path $WebDistDir) {
    $DestWeb = Join-Path $BackendExeDir "web_static"
    Copy-Item -Path $WebDistDir -Destination $DestWeb -Recurse -Force
}

Assert-NoSensitiveConfigs -RootPath $BackendExeDir
Write-Host "[OK] Verified backend package contains no local sensitive config files." -ForegroundColor Green

# --- Electron Build ---
$DesktopDir = Join-Path $RepoRoot "desktop"
if (-not (Test-Path $DesktopDir)) {
    throw "Desktop Electron directory not found: $DesktopDir"
}

Push-Location $DesktopDir
try {
    if (-not (Test-Path "node_modules") -and -not $SkipNpmInstall) {
        Write-Host "Installing desktop npm dependencies..."
        cmd /c "npm install"
    }

    $env:CWS_STEAM_BACKEND_DIR = $BackendExeDir
    $env:CSC_IDENTITY_AUTO_DISCOVERY = "false"
    if ($HasSeed) {
        $env:CWS_STEAM_SEED_FILE = $SeedFile
    }

    Write-Host "Building Electron Steam package..."
    cmd /c "npm run dist:steam"
    if ($LASTEXITCODE -ne 0) {
        throw "Electron build failed."
    }
}
finally {
    Remove-Item Env:CWS_STEAM_BACKEND_DIR -ErrorAction SilentlyContinue
    Remove-Item Env:CWS_STEAM_SEED_FILE -ErrorAction SilentlyContinue
    Remove-Item Env:CSC_IDENTITY_AUTO_DISCOVERY -ErrorAction SilentlyContinue
    Pop-Location
}

$ElectronOutput = Join-Path $DesktopDir "release\win-unpacked"
if (-not (Test-Path $ElectronOutput)) {
    throw "Electron unpacked output not found: $ElectronOutput"
}

$FinalContentRoot = Join-Path $DistRoot "win-unpacked"
if (Test-Path $FinalContentRoot) {
    Remove-Item -Path $FinalContentRoot -Recurse -Force
}
Copy-Item -Path $ElectronOutput -Destination $FinalContentRoot -Recurse -Force

Assert-NoSensitiveConfigs -RootPath $FinalContentRoot
$SourceMaps = Get-ChildItem -Path $FinalContentRoot -Include "*.map" -Recurse -Force -ErrorAction SilentlyContinue
if ($SourceMaps) {
    $List = ($SourceMaps | ForEach-Object { $_.FullName }) -join "`n"
    throw "Source maps remain in Steam Electron package:`n$List"
}

$ResolvedContentRoot = (Resolve-Path $FinalContentRoot).Path
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($ContentRootFile, $ResolvedContentRoot, $utf8NoBom)

Write-Host "`n=== Steam Electron package completed ===" -ForegroundColor Cyan
Write-Host "Content root: $ResolvedContentRoot"
Write-Host "Content root marker: $ContentRootFile"
Write-Host "Build desc: $BuildDesc"
