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

# Paths and directories
$DistDir = Join-Path $RepoRoot ("tmp\" + $tag)
$BuildDir = Join-Path $RepoRoot ("tmp\build\" + $tag)
$SpecDir = Join-Path $RepoRoot ("tmp\spec\" + $tag)
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
# CHANGED: Use server main.py instead of run.py
$EntryPy = Join-Path $RepoRoot "src\server\main.py"
$AppName = "CultivationWorld"

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
    # "--windowed",  <-- REMOVED: We want a console window for the server so user can close it
    "--console",
    "--distpath", $DistDir,
    "--workpath", $BuildDir,
    "--specpath", $SpecDir,
    "--paths", $RepoRoot,
    "--additional-hooks-dir", $AdditionalHooksPath,
    
    # Data Files
    "--add-data", "${AssetsPath};assets",       # Game Assets (Images) -> _internal/assets
    # REMOVED: "--add-data", "${WebDistDir};web_dist",  (We will copy this manually to outside)
    "--add-data", "${StaticPath};static",       # Configs -> _internal/static (backup)
    
    # Excludes
    "--exclude-module", "litellm",              # Optional LLM client with heavy dependencies
    "--exclude-module", "google",               # Google Cloud/AI libs
    "--exclude-module", "scipy",                # Scientific computing
    "--exclude-module", "pygame",               # Exclude heavy library not needed for server
    "--exclude-module", "matplotlib",           # Plotting library often pulled by pandas
    "--exclude-module", "tkinter",              # Python default GUI
    "--exclude-module", "PyQt5",                # Qt GUI
    "--exclude-module", "PyQt6",
    "--exclude-module", "PySide2",
    "--exclude-module", "PySide6",
    "--exclude-module", "wx",                   # wxPython
    "--exclude-module", "notebook",             # Jupyter notebook
    "--exclude-module", "ipython",
    "--exclude-module", "boto3",                # AWS SDK (huge, for Bedrock/S3)
    "--exclude-module", "botocore",
    "--exclude-module", "s3transfer",
    "--exclude-module", "azure",                # Azure SDK
    "--exclude-module", "huggingface_hub",      # HuggingFace (for local models)
    "--exclude-module", "transformers",         # Transformers (huge)
    "--exclude-module", "tensorflow",
    "--exclude-module", "torch",                # PyTorch (massive if present)
    
    # Hidden imports for LLM
    "--hidden-import", "tiktoken_ext.openai_public",
    "--hidden-import", "tiktoken_ext",
    "--collect-all", "tiktoken",
    "--copy-metadata", "tiktoken"
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
    $ErrorActionPreference = "Continue"  # 允许继续执行即使有错误
    & pyinstaller @argsList
    $ErrorActionPreference = "Stop"  # 恢复错误停止设置
} finally {
    Pop-Location
    
    # 在 finally 块中执行后续操作，确保一定会执行
    Write-Host "`n=== Post-build processing ===" -ForegroundColor Green
    
    # Copy cmd files to exe directory
    $CmdSrc = Join-Path $ScriptDir "set_env.cmd"
    $ExeDir = Join-Path $DistDir $AppName
    if ((Test-Path $CmdSrc) -and (Test-Path $ExeDir)) {
        Copy-Item -Path $CmdSrc -Destination $ExeDir -Force
        # Rename cmd file
        $OldCmdPath = Join-Path $ExeDir "set_env.cmd"
        $NewCmdPath = Join-Path $ExeDir "点击输入大模型密钥.cmd"
        if (Test-Path $OldCmdPath) {
            Move-Item -Path $OldCmdPath -Destination $NewCmdPath -Force
            Write-Host "✓ Copied and renamed to 点击输入大模型密钥.cmd in exe directory" -ForegroundColor Green
        }
    }
    
    # Copy static to exe directory (Config needs to be next to exe for CWD access)
    if (Test-Path $ExeDir) {        
        # NOTE: We DO NOT copy 'assets' to root anymore. They are inside _internal via --add-data.
        
        if (Test-Path $StaticPath) {
            Copy-Item -Path $StaticPath -Destination $ExeDir -Recurse -Force
            # 删除 local_config.yml
            $LocalConfigPath = Join-Path $ExeDir "static\local_config.yml"
            if (Test-Path $LocalConfigPath) {
                Remove-Item -Path $LocalConfigPath -Force
                Write-Host "✓ Copied static to exe directory (excluded local_config.yml)" -ForegroundColor Green
            } else {
                Write-Host "✓ Copied static to exe directory" -ForegroundColor Green
            }
        }

        # Copy Web Dist to exe directory (Manual copy instead of PyInstaller bundle)
        if (Test-Path $WebDistDir) {
             $DestWeb = Join-Path $ExeDir "web_static"
             Copy-Item -Path $WebDistDir -Destination $DestWeb -Recurse -Force
             Write-Host "✓ Copied web_dist to web_static in exe directory" -ForegroundColor Green
        }
    }
    
    # Clean up build and spec directories (delete entire directories)
    $BuildDirRoot = Join-Path $RepoRoot "tmp\build"
    if (Test-Path $BuildDirRoot) {
        Remove-Item -Path $BuildDirRoot -Recurse -Force
        Write-Host "✓ Deleted entire build directory: $BuildDirRoot" -ForegroundColor Green
    }
    
    Write-Host "`n=== Package completed ===" -ForegroundColor Cyan
    Write-Host "Distribution directory: " (Resolve-Path $DistDir).Path
    if (Test-Path $ExeDir) {
        Write-Host "Executable directory: " (Resolve-Path $ExeDir).Path
    }
}
