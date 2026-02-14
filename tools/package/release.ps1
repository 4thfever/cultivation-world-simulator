$ErrorActionPreference = "Stop"

# ==============================================================================
# 1. 环境与路径设置
# ==============================================================================
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path

# ==============================================================================
# 2. 获取 Git 标签 (版本号)
# ==============================================================================
Push-Location $RepoRoot
try {
    $tag = (git describe --tags --abbrev=0 2>$null)
    if (-not $tag) {
        throw "未找到 git 标签"
    }
    $tag = $tag.Trim()
} catch {
    Write-Error "无法确定 git 标签。请确保这是一个 git 仓库且至少包含一个标签。"
    exit 1
} finally {
    Pop-Location
}

Write-Host "目标发布版本 (Tag): $tag" -ForegroundColor Cyan

# ==============================================================================
# 3. 构建与压缩
# ==============================================================================
# 调用 pack.ps1 构建可执行文件
Write-Host "`n>>> [1/3] 正在构建程序包 (pack.ps1)..." -ForegroundColor Cyan
& "$ScriptDir\pack.ps1"

# 调用 compress.ps1 创建压缩包
Write-Host "`n>>> [2/3] 正在压缩归档 (compress.ps1)..." -ForegroundColor Cyan
& "$ScriptDir\compress.ps1"

# ==============================================================================
# 4. GitHub 发布 (Release)
# ==============================================================================
$ZipFileName = "AI_Cultivation_World_Simulator_${tag}.zip"
$ZipPath = Join-Path $RepoRoot "tmp\$ZipFileName"

if (-not (Test-Path $ZipPath)) {
    Write-Error "未找到压缩文件: $ZipPath"
    exit 1
}

Write-Host "`n>>> [3/3] 正在处理 GitHub Release..." -ForegroundColor Cyan

# 使用 gh 命令行工具检查 Release 是否存在
if (gh release view $tag 2>$null) {
    Write-Warning "Release '$tag' 已存在。正在上传文件到现有 Release (覆盖)..."
    gh release upload $tag $ZipPath --clobber
} else {
    Write-Host "正在创建新的草稿 Release..."
    # --draft: 创建为草稿 (自动化脚本最安全的方式，发布前可人工确认)
    # --generate-notes: 从 Git 提交记录自动生成更新日志
    gh release create $tag $ZipPath --title "$tag" --generate-notes --draft
}

Write-Host "`n[成功] 发布流程完成！" -ForegroundColor Green
gh release view $tag --json url --template "查看 Release 页面: {{.url}}`n"
