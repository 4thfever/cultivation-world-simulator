$ErrorActionPreference = "Stop"

# ==============================================================================
# 0. 环境与路径设置
# ==============================================================================
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path
$SteamDir = Join-Path $ScriptDir "steam"

# ==============================================================================
# 1. 加载 Steam 配置
# ==============================================================================
$EnvFile = Join-Path $SteamDir "steam_config.env"
if (-not (Test-Path $EnvFile)) {
    Write-Error "找不到配置文件：$EnvFile`n请将 steam_config.env.example 复制为 steam_config.env，并填入你的 Steamworks 信息。"
    exit 1
}

Write-Host ">>> 正在加载 Steam 配置..." -ForegroundColor Cyan

# 简单解析 .env 文件
Get-Content $EnvFile | ForEach-Object {
    $line = $_.Trim()
    if ($line -match "^#" -or $line -eq "") { return }
    if ($line -match "^([^=]+)=(.*)$") {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim()
        Set-Item -Path "Env:$key" -Value $value
    }
}

$SteamUser = $env:STEAM_USERNAME
$SteamPass = $env:STEAM_PASSWORD
$AppID = $env:STEAM_APP_ID
$DepotID = $env:STEAM_DEPOT_ID
$SteamCmd = $env:STEAM_CMD_PATH

if (-not $SteamUser -or -not $AppID -or -not $DepotID -or -not $SteamCmd) {
    Write-Error "steam_config.env 缺少必要的配置参数，请检查填写的字段是否完整（密码除外）。"
    exit 1
}

# 密码为空时，弹出安全输入提示
if (-not $SteamPass) {
    $SecurePass = Read-Host "请输入 Steam 账号 ($SteamUser) 的密码" -AsSecureString
    $SteamPass = (New-Object System.Management.Automation.PSCredential ("user", $SecurePass)).GetNetworkCredential().Password
}

if (-not (Test-Path $SteamCmd)) {
    Write-Error "找不到指定的 steamcmd.exe 路径：$SteamCmd"
    exit 1
}

# ==============================================================================
# 2. 获取当前构建版本号（Git Tag）
# ==============================================================================
Push-Location $RepoRoot
try {
    $tag = git describe --tags --abbrev=0 2>$null
    if (-not $tag) {
        throw "Git tag not found"
    }
    $tag = $tag.Trim()
} catch {
    Write-Error "无法获取当前 Git 标签，请确保你在一个包含至少一个 tag 的仓库中运行此脚本。"
    exit 1
} finally {
    Pop-Location
}

Write-Host ">>> 目标上传版本 (Tag): $tag" -ForegroundColor Cyan

# ==============================================================================
# 3. 校验产物路径 & 准备输出目录
# ==============================================================================
$AppName = "AICultivationSimulator"
$ContentRoot = Join-Path $RepoRoot "tmp\$tag\$AppName"

if (-not (Test-Path $ContentRoot)) {
    Write-Error "找不到构建产物：$ContentRoot`n请先运行 pack.ps1 成功构建该版本后再执行上传。"
    exit 1
}

# 将临时 vdf 和缓存放到 tmp\steam 目录中 (该目录被 .gitignore 忽略)
$TmpSteamDir = Join-Path $RepoRoot "tmp\steam"
if (-not (Test-Path $TmpSteamDir)) {
    New-Item -ItemType Directory -Force -Path $TmpSteamDir | Out-Null
}

$BuildOutputDir = Join-Path $TmpSteamDir "output"
if (-not (Test-Path $BuildOutputDir)) {
    New-Item -ItemType Directory -Force -Path $BuildOutputDir | Out-Null
}

$AppVdfOut = Join-Path $TmpSteamDir "app_build.vdf"
$DepotVdfOut = Join-Path $TmpSteamDir "depot_build.vdf"

# ==============================================================================
# 4. 动态生成 VDF 文件
# ==============================================================================
Write-Host ">>> 正在生成 VDF 配置文件..." -ForegroundColor Cyan

# VDF 配置文件要求路径使用双反斜杠转义
$ContentRootEscaped = $ContentRoot -replace "\\", "\\"
$BuildOutputEscaped = $BuildOutputDir -replace "\\", "\\"
$DepotVdfOutEscaped = $DepotVdfOut -replace "\\", "\\"

# 处理 Depot VDF
$DepotTemplate = Get-Content (Join-Path $SteamDir "depot_build.vdf.template") -Raw
$DepotContent = $DepotTemplate.Replace('${STEAM_DEPOT_ID}', $DepotID)
$DepotContent = $DepotContent.Replace('${CONTENT_ROOT_DIR}', $ContentRootEscaped)
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($DepotVdfOut, $DepotContent, $utf8NoBom)

# 处理 App VDF
$AppTemplate = Get-Content (Join-Path $SteamDir "app_build.vdf.template") -Raw
$AppContent = $AppTemplate.Replace('${STEAM_APP_ID}', $AppID)
$AppContent = $AppContent.Replace('${BUILD_DESC}', "$tag")
$AppContent = $AppContent.Replace('${BUILD_OUTPUT_DIR}', $BuildOutputEscaped)
$AppContent = $AppContent.Replace('${STEAM_DEPOT_ID}', $DepotID)
$AppContent = $AppContent.Replace('${DEPOT_BUILD_VDF_PATH}', $DepotVdfOutEscaped)
[System.IO.File]::WriteAllText($AppVdfOut, $AppContent, $utf8NoBom)

# ==============================================================================
# 5. 上传至 Steam
# ==============================================================================
Write-Host "`n>>> [开始上传] 使用 SteamCMD 上传到 Steam 库中..." -ForegroundColor Cyan

# 组装 SteamCMD 执行参数
$argsList = @(
    "+login", $SteamUser, $SteamPass,
    "+run_app_build", $AppVdfOut,
    "+quit"
)

try {
    # 隐藏控制台直接回显密码，直接执行
    & $SteamCmd @argsList
    
    if ($LASTEXITCODE -ne 0) {
        throw "SteamCMD 运行失败，退出码：$LASTEXITCODE。请检查上述错误日志 (可能是密码错误或触发了 Steam Guard 令牌验证)。"
    }
    Write-Host "`n[Success] 成功上传该版本到 Steam！" -ForegroundColor Green
    Write-Host "现在你可以登录 Steamworks 网页后台，在 'SteamPipe -> 生成' 列表中找到此上传，并将其推送到默认分支。" -ForegroundColor Cyan
} catch {
    Write-Error "上传失败: $_"
    exit 1
} finally {
    # 脚本运行结束后，在环境变量中清除密码，避免内存驻留
    Set-Item -Path "Env:STEAM_PASSWORD" -Value ""
}
