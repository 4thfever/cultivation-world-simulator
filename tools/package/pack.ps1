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
    
    # Copy static and assets to exe directory
    if (Test-Path $ExeDir) {        
        if (Test-Path $AssetsPath) {
            Copy-Item -Path $AssetsPath -Destination $ExeDir -Recurse -Force
            Write-Host "✓ Copied assets to exe directory" -ForegroundColor Green
        }
        
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
    }
    
    # Clean up build and spec directories (delete entire directories)
    $BuildDirRoot = Join-Path $RepoRoot "tmp\build"
    if (Test-Path $BuildDirRoot) {
        Remove-Item -Path $BuildDirRoot -Recurse -Force
        Write-Host "✓ Deleted entire build directory: $BuildDirRoot" -ForegroundColor Green
    }
    
    # $SpecDirRoot = Join-Path $RepoRoot "tmp\spec"
    # if (Test-Path $SpecDirRoot) {
    #     Remove-Item -Path $SpecDirRoot -Recurse -Force
    #     Write-Host "✓ Deleted entire spec directory: $SpecDirRoot" -ForegroundColor Green
    # }
    
    Write-Host "`n=== Package completed ===" -ForegroundColor Cyan
    Write-Host "Distribution directory: " (Resolve-Path $DistDir).Path
    if (Test-Path $ExeDir) {
        Write-Host "Executable directory: " (Resolve-Path $ExeDir).Path
    }
}