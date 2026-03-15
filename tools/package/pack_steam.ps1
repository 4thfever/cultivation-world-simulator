$ErrorActionPreference = "Stop"

# Locate repository root directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path

# Get Git TAG (only the tag name, without commit hash or dirty flag)
$tag = ""
Push-Location $RepoRoot

# Get the most recent tag name
$tagDesc = & git describe --tags --abbrev=0 2>$null
if ($LASTEXITCODE -eq 0 -and $tagDesc) {
    $tag = $tagDesc.Trim()
}

Pop-Location

if (-not $tag) {
    Write-Error "Cannot get git tag. Please run in a Git repository with at least one tag."
    exit 1
}

# Paths and directories (Use _steam suffix to differentiate)
$DistDir = Join-Path $RepoRoot ("tmp\" + $tag + "_steam")
$BuildDir = Join-Path $RepoRoot ("tmp\build\" + $tag + "_steam")
$SpecDir = Join-Path $RepoRoot ("tmp\spec\" + $tag + "_steam")
New-Item -ItemType Directory -Force -Path $DistDir, $BuildDir, $SpecDir | Out-Null

# --- Web Frontend Build ---
$WebDir = Join-Path $RepoRoot "web"
$WebDistDir = Join-Path $WebDir "dist"

Write-Host "Checking Web Frontend..." -ForegroundColor Cyan
if (Test-Path $WebDir) {
    Push-Location $WebDir
    try {
        if (-not (Test-Path "node_modules")) {
            Write-Host "Installing npm dependencies..."
            # Use cmd /c to ensure npm is found on Windows
            cmd /c "npm install"
        }
        Write-Host "Building web frontend..."
        cmd /c "npm run build"
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Web build failed."
            exit 1
        }
    } catch {
        Write-Error "Web build process failed: $_"
        exit 1
    } finally {
        Pop-Location
    }
} else {
    Write-Error "Web directory not found at $WebDir"
    exit 1
}

# Entry and app name
$EntryPy = Join-Path $RepoRoot "src\server\main.py"
$AppName = "AICultivationSimulator_Steam"

if (-not (Test-Path $EntryPy)) {
    Write-Error "Entry script not found: $EntryPy"
    exit 1
}

# Assets and static paths
$AssetsPath = Join-Path $RepoRoot "assets"
$StaticPath = Join-Path $RepoRoot "static"

# Icon path
$IconPath = Join-Path $AssetsPath "icon.ico"

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
    # The packaged executable always launches the local server and opens the game in the system browser.
    "--distpath", $DistDir,
    "--workpath", $BuildDir,
    "--specpath", $SpecDir,
    "--paths", $RepoRoot,
    "--additional-hooks-dir", $AdditionalHooksPath,
    
    # Data Files
    "--add-data", "${AssetsPath};assets",       # Game Assets (Images) -> _internal/assets
    "--add-data", "${StaticPath};static",       # Configs -> _internal/static (backup)
    
    # Excludes
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
    $argsList += @("--runtime-hook", $RuntimeHookPath)
}

# Add icon if available
if (Test-Path $IconPath) {
    $argsList += @("--icon", $IconPath)
}

# Call PyInstaller
Push-Location $RepoRoot
try {
    Write-Host "Executing PyInstaller for Steam..."
    & pyinstaller @argsList
    
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller execution failed with exit code $LASTEXITCODE. Please check the error logs above."
    }
    $BuildSuccess = $true
} catch {
    Write-Error "Build failed: $_"
    exit 1
} finally {
    Pop-Location
    
    if ($BuildSuccess) {
        Write-Host "`n=== Post-build processing ===" -ForegroundColor Green
        
        $ExeDir = Join-Path $DistDir $AppName
        
        if (Test-Path $ExeDir) {        
            if (Test-Path $StaticPath) {
                Copy-Item -Path $StaticPath -Destination $ExeDir -Recurse -Force
                $SensitiveConfigNames = @("local_config.yml", "settings.json", "secrets.json")
                $RemovedSensitiveConfigs = $false
                foreach ($SensitiveName in $SensitiveConfigNames) {
                    $MatchedFiles = Get-ChildItem -Path $ExeDir -Include $SensitiveName -Recurse -Force -ErrorAction SilentlyContinue
                    foreach ($MatchedFile in $MatchedFiles) {
                        Remove-Item -Path $MatchedFile.FullName -Force
                        $RemovedSensitiveConfigs = $true
                    }
                }
                if ($RemovedSensitiveConfigs) {
                    Write-Host "✓ Copied static to exe directory (excluded sensitive config files)" -ForegroundColor Green
                }
                else {
                    Write-Host "✓ Copied static to exe directory" -ForegroundColor Green
                }
            }
    
            if (Test-Path $WebDistDir) {
                 $DestWeb = Join-Path $ExeDir "web_static"
                 Copy-Item -Path $WebDistDir -Destination $DestWeb -Recurse -Force
                 Write-Host "✓ Copied web_dist to web_static in exe directory" -ForegroundColor Green
            }
            
            $BuildDirRoot = Join-Path $RepoRoot "tmp\build"
            if (Test-Path $BuildDirRoot) {
                Remove-Item -Path $BuildDirRoot -Recurse -Force
                Write-Host "✓ Deleted entire build directory: $BuildDirRoot" -ForegroundColor Green
            }
            
            Write-Host "`n=== Package completed for Steam ===" -ForegroundColor Cyan
            Write-Host "Distribution directory: " (Resolve-Path $DistDir).Path
            if (Test-Path $ExeDir) {
                Write-Host "Executable directory: " (Resolve-Path $ExeDir).Path
            }
        } else {
             Write-Error "Build finished but executable directory not found at $ExeDir"
        }
    } else {
        Write-Warning "Build failed. Keeping build directory for debugging."
    }
}
