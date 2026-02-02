$ErrorActionPreference = "Stop"

# ==============================================================================
# 1. Environment & Path Setup
# ==============================================================================
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path

# ==============================================================================
# 2. Get Git Tag (Version)
# ==============================================================================
Push-Location $RepoRoot
$tag = ""
$tagDesc = & git describe --tags --abbrev=0 2>$null
if ($LASTEXITCODE -eq 0 -and $tagDesc) {
    $tag = $tagDesc.Trim()
}
Pop-Location

if (-not $tag) {
    Write-Error "Cannot determine git tag. Please ensure this is a git repository with tags."
    exit 1
}

Write-Host "Target Version (Tag): $tag" -ForegroundColor Cyan

# ==============================================================================
# 3. Locate Source Directory
# ==============================================================================
# Instead of hardcoding the AppName (which may cause encoding issues with Chinese characters),
# we dynamically find the directory in tmp/<tag>/
$TagBaseDir = Join-Path $RepoRoot "tmp\$tag"

if (-not (Test-Path $TagBaseDir)) {
    Write-Error "Build directory for tag '$tag' not found at: $TagBaseDir"
    Write-Error "Please run 'tools/package/pack.ps1' first to build this version."
    exit 1
}

# Find the first directory inside the tag folder (this should be the AppName folder)
$AppDirObj = Get-ChildItem -Path $TagBaseDir -Directory | Select-Object -First 1

if (-not $AppDirObj) {
    Write-Error "No application directory found inside: $TagBaseDir"
    exit 1
}

$AppName = $AppDirObj.Name
$SourceDir = $AppDirObj.FullName

Write-Host "Found Application: $AppName" -ForegroundColor Gray
Write-Host "Source Directory: $SourceDir" -ForegroundColor Gray

# ==============================================================================
# 4. Clean Sensitive Files
# ==============================================================================
Write-Host "Cleaning up sensitive/temporary files..." -ForegroundColor Yellow

# 4.1 Remove local_config.yml (Recursively)
$SensitiveFiles = Get-ChildItem -Path $SourceDir -Include "local_config.yml" -Recurse -Force
if ($SensitiveFiles) {
    foreach ($file in $SensitiveFiles) {
        Remove-Item -Path $file.FullName -Force
        Write-Host "  [-] Deleted Config: $($file.FullName)" -ForegroundColor DarkGray
    }
} else {
    Write-Host "  [i] No local_config.yml files found." -ForegroundColor DarkGray
}

# 4.2 Remove log files (Recursively) - cleanup from testing
$LogFiles = Get-ChildItem -Path $SourceDir -Include "*.log" -Recurse -Force
if ($LogFiles) {
    foreach ($file in $LogFiles) {
        Remove-Item -Path $file.FullName -Force
        Write-Host "  [-] Deleted Log:    $($file.FullName)" -ForegroundColor DarkGray
    }
}

# 4.3 Remove saves directories (Recursively)
# Deletes 'saves' folder in root and inside '_internal' (and any save files within)
$SaveDirs = Get-ChildItem -Path $SourceDir -Include "saves" -Recurse -Directory -Force
if ($SaveDirs) {
    foreach ($dir in $SaveDirs) {
        if (Test-Path $dir.FullName) {
            Remove-Item -Path $dir.FullName -Recurse -Force
            Write-Host "  [-] Deleted Saves Dir: $($dir.FullName)" -ForegroundColor DarkGray
        }
    }
}

# ==============================================================================
# 5. Compress
# ==============================================================================
$ZipFileName = "AI_Cultivation_World_Simulator_${tag}.zip"
$ZipPath = Join-Path $RepoRoot "tmp\$ZipFileName"

if (Test-Path $ZipPath) {
    Remove-Item -Path $ZipPath -Force
    Write-Host "Removed existing archive: $ZipPath" -ForegroundColor DarkGray
}

Write-Host "Compressing to: $ZipPath" -ForegroundColor Cyan
Write-Host "This may take a moment..." -ForegroundColor Gray

try {
    # Compressing $SourceDir puts the directory itself into the root of the zip
    Compress-Archive -Path $SourceDir -DestinationPath $ZipPath -CompressionLevel Optimal
    
    if (Test-Path $ZipPath) {
        Write-Host "`nSUCCESS: Package created at:" -ForegroundColor Green
        Write-Host $ZipPath -ForegroundColor White
    } else {
        throw "Archive file was not created."
    }
} catch {
    Write-Error "Compression failed: $_"
    exit 1
}
