# Epic EOS Dev Test Runbook

本文档记录 Epic EOS Metrics 的 dev 实测流程。目标是让一次测试很容易判断：

1. 包是否正确上传到 Epic dev artifact。
2. 游戏是否真的由 Epic Launcher 启动。
3. EOS helper 是否成功登录并上报 Metrics session。
4. 失败时应该先查哪个日志、怎么改。

## 当前测试目标

本阶段只验证 EOS Metrics：

1. 游戏启动时调用 `BeginPlayerSession`。
2. 游戏退出时调用 `EndPlayerSession`。
3. Epic 后台能看到玩家 session / 在线人数相关数据。

本阶段不验证：

1. 成就。
2. 好友、Presence、Overlay。
3. Lobby、P2P、云存档。
4. 游戏内 Epic 登录 UI。

## 前置条件

本地必须已经准备好这些东西：

1. `E:\tools\dotnet` 可用，`dotnet --info` 正常。
2. EOS SDK 解压在 `E:\SDK\EOS`。
3. BuildPatchTool 路径已写入 `tools/package/epic/epic_config.env`。
4. EOS runtime 配置已写入 `tools/package/epic/eos_runtime.env`。
5. `tools/package/epic/eos_runtime.env` 和 `tools/package/epic/epic_config.env` 不能提交到 git。

dev 测试时，Epic artifact 必须绑定 dev deployment。不要用 live deployment 来测 dev artifact。

## 重要规则：BuildVersion 必须唯一

Epic 的 BuildPatchTool 不允许同一个 artifact 重复上传同一个 `BuildVersion`。

如果看到：

```text
Build already exists.
The artifact ... already has a binary registered with version v3.8.0-desktop.
Please ensure the provided BuildVersion argument is unique for each upload.
```

这不是 EOS 失败，也不是包坏了。它只是说这个版本号已经上传过。

解决方式：每次 dev 上传都传一个新的 `-BuildVersion`。

推荐格式：

```powershell
$buildVersion = "v3.8.0-eos-dev-$(Get-Date -Format yyyyMMdd-HHmmss)"
powershell ./tools/package/publish_epic.ps1 -BuildVersion $buildVersion -RequireEosRuntime -RequireUpload -EosEnv dev -SkipNpmInstall
```

如果正在测试正式新版本，也可以用正式版本号加测试后缀：

```powershell
$buildVersion = "v3.8.1-eos-dev-$(Get-Date -Format yyyyMMdd-HHmmss)"
powershell ./tools/package/publish_epic.ps1 -BuildVersion $buildVersion -RequireEosRuntime -RequireUpload -EosEnv dev
```

BuildPatchTool 提示版本不是最新时：

```text
You are not using the latest version of BuildPatchTool.
```

这通常只是警告。只要后面没有非 0 exit code，并且上传成功，就不是当前 EOS 测试的阻断项。之后可以再下载最新版 BuildPatchTool 替换。

## Dev 测试步骤

### 1. 先做本地 helper 发布

```powershell
$env:DOTNET_ROOT = "E:\tools\dotnet"
$env:Path = "E:\tools\dotnet;$env:Path"
dotnet publish .\desktop-eos-helper\desktop-eos-helper.csproj -c Release -r win-x64 --self-contained true -o .\desktop-eos-helper\publish\win-x64
```

成功标准：

1. 命令 exit code 为 0。
2. `desktop-eos-helper\publish\win-x64\eos-helper.exe` 存在。
3. `desktop-eos-helper\publish\win-x64\EOSSDK-Win64-Shipping.dll` 存在。

EOS SDK 自带 C# wrapper 可能会输出很多 nullable warning。只要 publish 成功，这些 warning 不阻断测试。

### 2. 先做 preview 打包

```powershell
$buildVersion = "v3.8.0-eos-dev-$(Get-Date -Format yyyyMMdd-HHmmss)"
powershell ./tools/package/publish_epic.ps1 -BuildVersion $buildVersion -Preview -RequireEosRuntime -EosEnv dev -SkipNpmInstall
```

成功标准：

1. 输出 `[OK] Prepared Epic EOS runtime config and helper.`。
2. 输出 `[Preview] Epic upload was not executed.`。
3. `tmp\desktop_content_root.txt` 指向的 `win-unpacked` 目录存在。
4. `win-unpacked\resources\eos-helper\eos-helper.exe` 存在。
5. `win-unpacked\resources\eos-runtime.json` 存在。

不要打开或打印 `eos-runtime.json` 的内容，因为里面可能包含 runtime client secret。

### 3. 上传 dev artifact

每次上传都重新生成一个唯一 `BuildVersion`：

```powershell
$buildVersion = "v3.8.0-eos-dev-$(Get-Date -Format yyyyMMdd-HHmmss)"
powershell ./tools/package/publish_epic.ps1 -BuildVersion $buildVersion -RequireEosRuntime -RequireUpload -EosEnv dev -SkipNpmInstall
```

成功标准：

1. BuildPatchTool exit code 为 0。
2. 脚本输出 `[Success] Uploaded this build to Epic.`。
3. Epic 后台 artifact 能看到这个新的 build version。

失败标准：

1. `Build already exists`：版本号重复，换新的 `-BuildVersion` 后重传。
2. `BuildPatchTool failed with exit code ...`：上传工具失败，先看 `C:\Users\wangx\AppData\Local\BuildPatchTool\Saved\Logs\BuildPatchTool.log`。
3. 提示 secret 缺失：检查 `tools/package/epic/epic_config.env` 中 `EPIC_CLIENT_SECRET_ENV_VAR` 对应的环境变量是否有值，或按提示手输。

### 4. 从 Epic Launcher 安装并启动

必须从 Epic Launcher 启动测试。不要直接双击 `win-unpacked\CultivationWorldSimulator.exe`。

原因：EOS Auth 的 exchange code 来自 Epic Launcher 注入的启动参数。直接双击本地 exe 时没有 `AUTH_PASSWORD`，helper 会返回 `missing_exchange_code`，这是正常失败。

成功标准：

1. Epic Launcher 能安装或更新到刚上传的 build version。
2. 从 Launcher 点启动后游戏正常打开。
3. 游戏没有因为 EOS 失败而退出。

### 5. 查本地日志

日志目录：

```text
%LOCALAPPDATA%\CultivationWorldSimulator\logs\electron
```

重点看三个文件：

```text
telemetry.log
eos-helper.stdout.log
eos-helper.stderr.log
```

成功时通常应看到：

```json
{"type":"status","state":"session_active"}
```

退出游戏后还应看到：

```json
{"type":"status","state":"session_ended"}
```

如果只看到 `session_active`，但没看到 `session_ended`，先确认游戏是否正常退出。异常杀进程可能来不及上报 end session。

### 6. 到 Epic 后台看 Metrics

Epic 后台指标可能不是实时刷新。dev 测试时建议：

1. 启动游戏后停留 2 到 5 分钟。
2. 正常关闭游戏。
3. 等几分钟后再看 Metrics / player sessions / online users 相关页面。

成功标准：

1. 后台出现对应 build/deployment 的玩家 session 数据。
2. 同一时间段的在线或 session 统计有变化。

失败标准：

1. 本地日志已经 `session_active`，但后台短时间看不到：先等一段时间，不立刻判失败。
2. 长时间仍无数据：检查 dev artifact 是否绑定 dev deployment，检查 package 使用的 `-EosEnv dev` 是否正确。

## 常见失败与处理

### `missing_exchange_code`

含义：helper 没拿到 Epic Launcher 注入的 exchange code。

常见原因：

1. 直接双击 exe，不是从 Epic Launcher 启动。
2. Epic artifact 的 launch 配置不对。
3. Launcher 没有把 Auth 参数传给游戏。

处理：

1. 必须从 Epic Launcher 启动。
2. 在 Epic 后台确认 artifact 的 launch executable 是 `CultivationWorldSimulator.exe`。
3. 重新安装或更新到刚上传的 dev build。

### `eos_initialize_failed`

含义：EOS SDK 初始化失败。

处理：

1. 确认 `resources\eos-helper\EOSSDK-Win64-Shipping.dll` 存在。
2. 确认 `resources\eos-helper\xaudio2_9redist.dll` 存在。
3. 看 `eos-helper.stderr.log` 中 EOS 自身日志。

### `eos_platform_create_failed`

含义：EOS Platform 创建失败。

常见原因：

1. Product ID、Sandbox ID、Deployment ID、Client ID、Client Secret 有误。
2. dev artifact 和 deployment 不匹配。
3. 打包时没有带上 `eos-runtime.json`。

处理：

1. 检查 `tools/package/epic/eos_runtime.env`，不要打印 secret。
2. 用 `-Preview -RequireEosRuntime -EosEnv dev` 重新确认包内资源存在。
3. 确认 dev artifact 绑定 dev deployment。

### `eos_login_failed`

含义：EOS Auth 登录失败。

常见 detail：

1. `AuthExchangeCodeNotFound`：exchange code 无效、过期，或不是 Launcher 正常注入。
2. `InvalidAuth` / `InvalidParameters`：client 或 deployment 配置不匹配。

处理：

1. 关闭游戏，从 Epic Launcher 重新启动。
2. 确认当前测试 build 是刚上传的 dev build。
3. 确认 runtime client policy 使用的是 Game Client，并允许 Metrics/Auth 所需基础权限。
4. 确认 package 使用 `-EosEnv dev`。

### `eos_metrics_begin_failed`

含义：登录可能成功了，但 Metrics BeginPlayerSession 失败。

处理：

1. 看 `eos-helper.stderr.log` 中 EOS result。
2. 确认 policy 权限没有限制 Metrics。
3. 确认 Product / Sandbox / Deployment / Artifact 是同一套 dev 链路。

### 游戏能启动，但没有 EOS 日志

含义：Electron 没有启用 Epic telemetry provider，或者 helper 没被打进包。

处理：

1. 确认这是 Epic distribution 包，不是 generic/GitHub 包。
2. 确认 `resources\desktop-distribution.json` 存在。
3. 确认 `resources\eos-helper\eos-helper.exe` 存在。
4. 确认打包命令包含 `-RequireEosRuntime`。

## 测完 dev 后再测正式新版本

推荐流程：

1. 先在 dev artifact 用唯一 `BuildVersion` 测 EOS。
2. dev 日志和后台 Metrics 都确认成功。
3. 再发新的正式版本号，例如 `v3.8.1`。
4. 用新 tag / 新版本号打正式 Epic 包。
5. live 测试时使用 `-EosEnv live`，并确认 live artifact 绑定 live deployment。

live 上传示例：

```powershell
$buildVersion = "v3.8.1-desktop"
powershell ./tools/package/publish_epic.ps1 -BuildVersion $buildVersion -RequireEosRuntime -RequireUpload -EosEnv live
```

如果同一个 live 版本号已经上传过，不要覆盖，换新的正式版本号或带修订后缀。

## 判断结论模板

dev 测试成功可以这样记录：

```text
Epic EOS dev test passed.
BuildVersion: <实际上传版本>
Launcher start: OK
Local helper session_active: OK
Local helper session_ended: OK
Epic backend Metrics visible: OK
```

dev 测试失败可以这样记录：

```text
Epic EOS dev test failed.
BuildVersion: <实际上传版本>
Launcher start: OK/Failed
Local helper state: <stdout 中的 state>
Local helper detail: <stdout 中的 detail，不含 secret>
stderr key result: <EOS result>
Next action: <按本文档对应失败项处理>
```
