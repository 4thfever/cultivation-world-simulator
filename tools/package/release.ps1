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
try {
    $tag = git describe --tags --abbrev=0 2>$null
    if (-not $tag) {
        throw "Git tag not found"
    }
    $tag = $tag.Trim()
} catch {
    Write-Error "Could not determine git tag. Please ensure this is a git repository with at least one tag."
    exit 1
} finally {
    Pop-Location
}

Write-Host "Target Release Version (Tag): $tag" -ForegroundColor Cyan

# ==============================================================================
# 3. Build & Compress
# ==============================================================================
# # Call pack.ps1 to build executable
# Write-Host "`n>>> [1/3] Building package (pack.ps1)..." -ForegroundColor Cyan
# & "$ScriptDir\pack.ps1"

# # Call compress.ps1 to create archive
# Write-Host "`n>>> [2/3] Compressing archive (compress.ps1)..." -ForegroundColor Cyan
# & "$ScriptDir\compress.ps1"

# ==============================================================================
# 4. GitHub Release
# ==============================================================================
$ZipFileName = "AI_Cultivation_World_Simulator_${tag}.zip"
$ZipPath = Join-Path $RepoRoot "tmp\$ZipFileName"

if (-not (Test-Path $ZipPath)) {
    Write-Error "Archive not found: $ZipPath"
    exit 1
}

Write-Host "`n>>> [3/3] Processing GitHub Release..." -ForegroundColor Cyan

# Check if release exists using gh cli
$releaseExists = $false
try {
    # Temporarily ignore errors to check for existence
    $null = gh release view $tag 2>&1
    if ($LASTEXITCODE -eq 0) {
        $releaseExists = $true
    }
} catch {
    # If gh returns non-zero or writes to stderr, it might throw due to ErrorActionPreference='Stop'
    $releaseExists = $false
}


# Ensure tag is pushed to remote before creating/updating release
Write-Host "Ensuring tag '$tag' is pushed to remote..."
git push origin $tag
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to push tag to origin. If the tag already exists on remote, this is fine."
}

if ($releaseExists) {
    Write-Warning "Release '$tag' already exists. Updating to 'latest' and uploading assets..."
    # Ensure it is not a draft and is marked as latest
    gh release edit $tag --draft=false --latest
    if ($LASTEXITCODE -ne 0) { Write-Warning "Could not update release status (might already be correct)." }

    gh release upload $tag $ZipPath --clobber
    if ($LASTEXITCODE -ne 0) { throw "Failed to upload assets." }
} else {
    Write-Host "Creating new release (latest)..."
    # --latest: Mark as latest release
    # --generate-notes: Auto-generate notes from git commits
    gh release create $tag $ZipPath --title "$tag" --generate-notes --latest
    if ($LASTEXITCODE -ne 0) { throw "Failed to create release." }
}

Write-Host "`n[Success] Release process completed!" -ForegroundColor Green
gh release view $tag --json url --template "View Release: {{.url}}`n"
