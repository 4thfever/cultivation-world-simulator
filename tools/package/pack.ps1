$ErrorActionPreference = "Stop"

# Locate repository root directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path

# Get Git TAG
$tag = ""
Push-Location $RepoRoot

# Get exact tag
$exact = & git describe --tags --abbrev=0 --exact-match
if ($LASTEXITCODE -eq 0 -and $exact) {
    $tag = $exact.Trim()
}

# Fallback: any readable description
if (-not $tag) {
    $desc = & git describe --tags --dirty --always
    if ($LASTEXITCODE -eq 0 -and $desc) {
        $tag = $desc.Trim()
    }
}

Pop-Location

if (-not $tag) {
    Write-Error "Cannot get git tag. Please run in a Git repository."
    exit 1
}

# Paths and directories
$DistDir = Join-Path $RepoRoot ("tmp\" + $tag)
$BuildDir = Join-Path $RepoRoot ("tmp\build\" + $tag)
$SpecDir = Join-Path $RepoRoot ("tmp\spec\" + $tag)
New-Item -ItemType Directory -Force -Path $DistDir, $BuildDir, $SpecDir | Out-Null

# Entry and app name
$EntryPy = Join-Path $RepoRoot "src\run\run.py"
$AppName = "CultivationWorld"

if (-not (Test-Path $EntryPy)) {
    Write-Error "Entry script not found: $EntryPy"
    exit 1
}

# Assets and static paths
$AssetsPath = Join-Path $RepoRoot "assets"
$StaticPath = Join-Path $RepoRoot "static"

# Runtime hook
$RuntimeHookPath = Join-Path $ScriptDir "runtime_hook_setcwd.py"

# Additional hooks directory
$AdditionalHooksPath = $ScriptDir

# Source path
$SrcPath = Join-Path $RepoRoot "src"

# Assemble PyInstaller arguments
$argsList = @(
    $EntryPy,
    "--name", $AppName,
    "--onedir",
    "--clean",
    "--noconfirm",
    "--windowed",
    "--distpath", $DistDir,
    "--workpath", $BuildDir,
    "--specpath", $SpecDir,
    "--paths", $RepoRoot,
    "--additional-hooks-dir", $AdditionalHooksPath,
    "--add-data", "${AssetsPath};assets",
    "--add-data", "${StaticPath};static",
    "--hidden-import", "tiktoken_ext.openai_public",
    "--hidden-import", "tiktoken_ext",
    "--collect-all", "tiktoken",
    "--collect-all", "litellm",
    "--copy-metadata", "tiktoken",
    "--copy-metadata", "litellm"
)

if (Test-Path $RuntimeHookPath) {
    $argsList += @("--runtime-hook", $RuntimeHookPath)
}

# Call PyInstaller
Push-Location $RepoRoot
try {
    & pyinstaller @argsList
} finally {
    Pop-Location
}

# Copy cmd files
$CmdSrc = Join-Path $ScriptDir "set_env.cmd"
if (Test-Path $CmdSrc) {
    Copy-Item -Path $CmdSrc -Destination $DistDir -Force
}

Write-Host "Package completed: " (Resolve-Path $DistDir).Path
Write-Host "Executable directory: " (Join-Path $DistDir $AppName)