# Steam Electron 版前置优化方案

本文档记录在正式实现 Steam Electron 版本之前，适合先落地到主代码线的一批基础优化。

这些优化的共同标准是：

1. 对 GitHub / 浏览器使用模式也有收益。
2. 不绑定 Electron 技术细节。
3. 不改变当前开源包的默认交互习惯。
4. 能减少未来 Steam 桌面包的启动、配置、编码、LLM 失效处理风险。

## 背景

当前打包流程大体分为两类：

1. GitHub 开源包：PyInstaller 打包后端，运行时打开系统浏览器访问本地 Web UI。
2. Steam 包：目前仍然沿用类似 PyInstaller 后端 + Web UI 的方式，后续计划改成 Electron 桌面成品。

未来 Steam 版的预期形态是：

1. Electron 主进程负责启动本地 Python 后端。
2. 后端继续服务 Web UI、API、WebSocket 与静态资源。
3. Electron 窗口加载本地 HTTP 地址，而不是直接用 `file://` 打开前端产物。
4. Steam 版可以预置一套 LongCat 默认 LLM 配置，降低首次启动门槛。

在进入 Electron 实现前，应先把通用底盘补稳。

## 当前落地状态

截至 2026-04-26，本 spec 中的前置优化已完成一轮实现，Electron 本体尚未开始。

已完成：

1. LLM 全局失效处理：运行中遇到 401 / 403 / 404 / 429 会暂停模拟器，写入 `llm_check_failed` / `llm_error_message`，并广播 `llm_config_required`。
2. LLM 错误分类标准化：`src/utils/llm/client.py` 中新增 `LLMFailureKind`、`LLMFailureInfo` 与 `classify_llm_error()`，测试连接与真实调用共享分类逻辑。
3. LLM 状态接口补充失败状态：`/api/settings/llm/status` 返回 `configured`、`requires_config`、`last_failure`。
4. 打包版端口自动避让：未显式设置 `SERVER_PORT` 时从 `8002` 起自动寻找空闲端口；显式设置时不漂移。
5. 禁止自动打开浏览器开关：支持 `CWS_NO_BROWSER=1`，默认行为仍会打开系统浏览器。
6. 后端启动健康探针：新增 `GET /api/health`，无需开局即可返回服务健康状态。
7. UTF-8 子进程环境契约：已有 `PYTHONUTF8=1`、`PYTHONIOENCODING=utf-8` 契约，并补了相关测试。
8. 打包版启动诊断信息：启动时输出 runtime mode、data root、settings/secrets、saves/logs、host/port、web/assets 路径和浏览器/idle shutdown 状态，不输出 key。
9. 默认 LLM 配置种子机制：支持 `CWS_DEFAULT_LLM_*` 环境变量首次写入默认 LLM profile 与 `secrets.json`，不覆盖用户已有配置。
10. 禁止覆盖用户已有 LLM 配置测试：覆盖 seed 首次写入、不覆盖用户配置、reset 不重套 seed 等场景。
11. 前端 LLM 配置页展示当前失败原因：Socket/status 写入 UI store，`LLMConfigPanel` 顶部展示失败原因，保存成功后清空。
12. 打包脚本敏感文件清理契约：`pack_github.ps1`、`pack_steam.ps1`、`compress.ps1` 增加 `Assert-NoSensitiveConfigs`，并有 contract 测试覆盖。

验证记录：

- 后端全量：`pytest -q`，1410 passed, 2 skipped。
- 前端类型检查：`cd web && npm run type-check` 通过。
- 前端全量测试：`cd web && npm run test`，524 passed。

仍未开始：

- Electron 工程结构、主进程、窗口加载、后端进程管理、`electron-builder`、Steam Electron 上传链路。

## 目标

本阶段目标不是实现 Electron，而是提前完成以下基础能力：

1. 运行中 LLM key / 模型 / 额度失效时能统一提示用户配置。
2. 后端启动端口更稳，减少端口占用导致的启动失败。
3. 打包版可以选择不自动打开系统浏览器，为 Electron 壳预留控制权。
4. 子进程和打包脚本的 UTF-8 行为更明确。
5. 默认 LLM 配置可以通过安全的种子机制写入用户数据目录。
6. 敏感配置不进入发布包的契约更明确。

## 非目标

本阶段暂不做：

1. 不新增 Electron 目录、`electron-builder` 配置或桌面窗口逻辑。
2. 不把前端改为 `file://` 可运行。
3. 不改变 GitHub 包默认启动后打开系统浏览器的体验。
4. 不把真实 LongCat key 提交到仓库。
5. 不在每次 `/api/settings/llm/status` 请求时真实调用模型。
6. 不改变默认用户数据目录到 Electron `userData`。

## 前置优化清单

### 1. LLM 全局失效处理

现状：

- 初始化阶段会调用 `check_llm_connectivity()`。
- 若失败，会设置 `llm_check_failed` 与 `llm_error_message`。
- WebSocket 连接时若发现该标记，会发送 `llm_config_required`。
- 运行中的普通 LLM 调用失败目前不会统一进入这条恢复链路。

目标：

1. 在统一 LLM 调用层识别“需要用户重新配置”的错误。
2. 对这类错误统一触发运行时状态更新和前端提示。
3. 避免把超时、临时网络抖动、服务商 5xx 当成配置失效。

建议判定为需要配置的错误：

- HTTP 401：API Key 错误或失效。
- HTTP 403：模型未授权、账号受限或 IP 受限。
- HTTP 404：Base URL 或模型名明显不可用。
- HTTP 429：额度超限或请求频率被限制。

不建议立即判定为需要配置的错误：

- timeout。
- DNS / socket 临时失败。
- HTTP 5xx。
- JSON 解析失败。
- LLM 输出格式不符合预期。

触发后行为：

1. 暂停模拟器。
2. 写入 `llm_check_failed=True`。
3. 写入可给用户看的 `llm_error_message`。
4. 通过 WebSocket 广播 `llm_config_required`。
5. 前端打开 LLM 配置页并显示失败原因。

### 2. LLM 错误分类标准化

现状：

- `test_connectivity()` 内部已经有较完整的 HTTP 错误分类。
- 普通 `call_llm()` 失败时仍然是直接抛出字符串化异常。

目标：

1. 抽出统一错误分类函数，供测试连接和真实调用共用。
2. 保持错误码、用户提示、日志细节三者分离。
3. 为前端和未来 Electron 桌面提示提供稳定字段。

建议结构：

```python
class LLMFailureKind(str, Enum):
    CONFIG_REQUIRED = "config_required"
    RATE_LIMITED = "rate_limited"
    TEMPORARY_NETWORK = "temporary_network"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    PARSE_ERROR = "parse_error"
    UNKNOWN = "unknown"
```

建议返回信息：

- `kind`
- `http_status`
- `provider_message`
- `user_message`
- `is_config_required`

### 3. LLM 状态接口补充失败状态

现状：

- `/api/settings/llm/status` 只返回 `{ "configured": boolean }`。
- `configured` 仅判断 `base_url + model_name + api_key` 是否存在。

目标：

状态接口仍然保持轻量，不主动消耗模型额度，但补充当前运行时已知失败信息。

建议响应：

```json
{
  "configured": true,
  "requires_config": false,
  "last_failure": ""
}
```

语义：

- `configured`：静态字段是否完整。
- `requires_config`：当前运行时是否已知需要用户处理配置。
- `last_failure`：最近一次可展示给用户的失败原因。

约束：

- 不在该接口中真实调用 LLM。
- 不把 API Key 返回前端。

### 4. 打包版端口自动避让

现状：

- 后端默认监听 `127.0.0.1:8002`。
- 如果端口被占用，打包版可能直接启动失败。

目标：

1. 用户没有显式设置 `SERVER_PORT` 时，自动寻找空闲端口。
2. 用户显式设置 `SERVER_PORT` 时，尊重该端口，失败则明确报错。
3. 前端和浏览器目标地址使用最终选定端口。

建议规则：

- 默认起始端口仍为 `8002`。
- 自动搜索范围可以从 `8002` 到 `8102`，或复用已有 `get_free_port()`。
- `SERVER_PORT` 存在且非空时不自动漂移。

收益：

- GitHub exe 版减少端口冲突。
- Electron 版后续可以直接通过环境变量传入已分配端口。

### 5. 增加禁止自动打开浏览器的开关

现状：

- 后端启动时会调用 `webbrowser.open(target_url)`。

目标：

增加环境变量：

- `CWS_NO_BROWSER=1`

语义：

- 默认不设置时，行为不变，继续打开系统浏览器。
- 设置为真值时，后端只启动服务，不打开浏览器。

真值建议：

- `1`
- `true`
- `yes`
- `on`

收益：

- GitHub 版默认体验不变。
- Electron 版后续可以自己控制窗口加载时机，避免双开。
- 开发者和自动化测试也可以用该开关启动无浏览器后端。

### 6. 后端启动健康探针

目标：

提供一个无需开局、无需 LLM、无需世界已初始化即可稳定返回的健康检查接口。

建议路径：

- `GET /api/health`

建议响应：

```json
{
  "ok": true,
  "status": "ready",
  "version": "..."
}
```

约束：

- 不触发游戏初始化。
- 不读取或返回敏感配置。
- 不依赖 WebSocket。

收益：

- GitHub 版用户排查本地服务是否启动更容易。
- Electron 版可以等待该接口成功后再显示窗口或加载页面。
- Steam 包自动化 smoke 测试可以使用该接口做启动检查。

### 7. 统一 UTF-8 子进程环境

现状：

- Python 侧已有 `configure_process_encoding()`。
- 前端 dev server 子进程已有 `build_utf8_subprocess_env()`。
- Steam VDF 生成已使用 UTF-8 no BOM。

目标：

将 UTF-8 环境作为所有本地子进程启动的显式契约。

建议环境变量：

- `PYTHONUTF8=1`
- `PYTHONIOENCODING=utf-8`

建议检查点：

1. 后端自身启动。
2. dev server 子进程。
3. 未来 Electron 启动 Python 后端子进程。
4. PowerShell 打包脚本写出的临时文本配置。

约束：

- 不改变业务数据编码，仍统一读写 UTF-8。
- 不在日志中输出敏感信息。

### 8. 打包版启动诊断信息

目标：

后端启动时输出足够排查问题的信息，但不泄露敏感数据。

建议输出：

- runtime mode：开发 / PyInstaller 打包。
- data root。
- settings 文件路径。
- secrets 文件路径。
- saves 目录。
- logs 目录。
- server host / port。
- web dist path。
- assets path。
- 是否禁用自动打开浏览器。
- 是否启用 idle auto shutdown。

禁止输出：

- API Key 原文。
- `Authorization` header。
- 完整 LLM 请求体中的敏感字段。

收益：

- 用户反馈问题时能快速定位数据目录和端口。
- Steam 客服/玩家日志更容易判断是端口、路径、权限还是前端资源问题。

### 9. 默认 LLM 配置种子机制

目标：

建立一种通用的默认 LLM 配置写入机制，为 Steam 版预置 LongCat 配置铺路，但本阶段不提交真实 key。

建议来源：

- 环境变量。
- 打包时生成但不入仓库的私有 seed 文件。

第一阶段优先支持环境变量：

- `CWS_DEFAULT_LLM_BASE_URL`
- `CWS_DEFAULT_LLM_MODEL`
- `CWS_DEFAULT_LLM_FAST_MODEL`
- `CWS_DEFAULT_LLM_API_FORMAT`
- `CWS_DEFAULT_LLM_MODE`
- `CWS_DEFAULT_LLM_MAX_CONCURRENT_REQUESTS`
- `CWS_DEFAULT_LLM_API_KEY`

写入时机：

- `SettingsService` 首次创建 `settings.json` / `secrets.json` 时。

覆盖规则：

1. 如果用户已有 `settings.json`，不覆盖普通配置。
2. 如果用户已有 `secrets.json`，不覆盖 API Key。
3. 如果环境变量缺字段，不写入半残缺 LLM profile。
4. API Key 只写入 `secrets.json`。
5. `settings.json` 只保存 `has_api_key` 与 profile 信息，不保存 key 原文。

收益：

- GitHub 高级用户可以用环境变量预置本地配置。
- Steam 版以后只需要在构建或启动环境中注入 LongCat seed。
- 仍遵守配置架构中“用户设置真源是 data root”的规则。

### 10. 禁止覆盖用户已有 LLM 配置的测试契约

目标：

为默认 LLM 配置种子机制补明确测试，防止版本更新覆盖玩家自己的 key。

测试场景：

1. 无 `settings.json`、无 `secrets.json`，且环境变量完整：写入默认 LLM profile 与 key。
2. 已有 `settings.json`：不覆盖用户 profile。
3. 已有 `secrets.json`：不覆盖用户 key。
4. 环境变量缺少 key：不写入 `has_api_key=true`。
5. 环境变量缺少 base url 或模型名：不写入残缺 profile。
6. `reset_settings()` 是否清除 seed 后配置需明确：
   - 推荐：重置回空配置，不重新应用 seed。
   - 原因：重置应表达用户主动清除设置。

### 11. 前端 LLM 配置页展示当前失败原因

现状：

- Socket 收到 `llm_config_required` 时会打开 LLM 配置页，并 toast 错误。
- 配置页本身不会稳定展示“为什么被要求配置”。

目标：

让 LLM 配置页能显示当前失败原因，避免 toast 消失后用户不知道问题来源。

建议方案：

1. UI store 或专门状态保存最近一次 LLM 配置错误。
2. `llm_config_required` socket 消息写入该状态。
3. `/api/settings/llm/status` 返回的 `last_failure` 也可写入该状态。
4. `LLMConfigPanel` 顶部展示一条非阻塞错误提示。
5. 用户成功测试并保存配置后清空该状态。

约束：

- 不把 API Key 或完整请求体展示给用户。
- 长错误消息需要截断，避免撑坏面板。

### 12. 打包脚本敏感文件清理契约

现状：

- `pack_github.ps1`、`pack_steam.ps1`、`compress.ps1` 已清理 `local_config.yml`、`settings.json`、`secrets.json`。

目标：

把“发布包不得带本地敏感配置”变成可检查契约，而不是只依赖人工看脚本。

建议做法：

1. 增加脚本自检：打包结束后扫描产物目录。
2. 扫描命中敏感文件时直接失败。
3. 敏感文件名至少包含：
   - `local_config.yml`
   - `settings.json`
   - `secrets.json`
4. 若后续引入 Steam 私有 seed 文件，必须保证：
   - 不进入 GitHub 包。
   - 不提交到仓库。
   - 只进入明确的 Steam 构建产物或安装后首次写入用户数据目录。

可选测试：

- 对打包脚本文本做 contract 测试，确保敏感文件名仍在清理列表中。
- 对临时 fixture 目录运行清理函数，确认敏感文件会被删除。

## 推荐实施顺序

### Phase 1: 运行时与宿主底盘

优先级最高，直接影响 GitHub 打包版稳定性：

1. 打包版端口自动避让。
2. `CWS_NO_BROWSER` 开关。
3. `/api/health` 健康探针。
4. 启动诊断信息。
5. UTF-8 子进程环境契约补测试。

### Phase 2: LLM 失效恢复链路

优先级最高，直接影响玩家体验：

1. LLM 错误分类标准化。
2. LLM 全局失效处理。
3. `/api/settings/llm/status` 补失败状态。
4. 前端 LLM 配置页展示当前失败原因。

### Phase 3: 默认配置种子与发布契约

为 Steam 版预置 LongCat 做准备：

1. 默认 LLM 配置种子机制。
2. 禁止覆盖用户已有 LLM 配置的测试契约。
3. 打包脚本敏感文件清理契约。

## 测试策略

### 后端单元测试

建议覆盖：

1. LLM HTTP 错误分类。
2. timeout / network / 5xx 不触发 config required。
3. 401 / 403 / 404 / 429 触发 config required。
4. `CWS_NO_BROWSER` 为真时不调用 `webbrowser.open()`。
5. 未指定 `SERVER_PORT` 时可自动避让占用端口。
6. 显式指定 `SERVER_PORT` 时不自动漂移。
7. `/api/health` 在未开局时可用。
8. 默认 LLM seed 首次创建配置时生效。
9. 默认 LLM seed 不覆盖已有用户配置。

### 前端测试

建议覆盖：

1. `llm_config_required` 会打开 LLM 配置页。
2. 错误原因会保存在前端状态中。
3. `LLMConfigPanel` 会展示当前失败原因。
4. 成功测试并保存后清空失败原因。
5. `/api/settings/llm/status` 的 `requires_config` 会触发配置页入口。

### 打包契约测试

建议覆盖：

1. GitHub 包不包含 `settings.json` / `secrets.json` / `local_config.yml`。
2. Steam 包不包含开发者本地 settings/secrets。
3. VDF 生成仍为 UTF-8 no BOM。
4. 打包产物中的 Web 静态资源路径仍通过本地 HTTP 正常访问。

## 与 Electron 阶段的衔接

完成本 spec 后，Electron 阶段只需要关注桌面壳本身：

1. Electron 主进程找空闲端口或指定端口。
2. 设置 `SERVER_PORT`、`CWS_NO_BROWSER=1`、UTF-8 环境变量。
3. 启动 PyInstaller 后端 exe。
4. 轮询 `/api/health`。
5. `BrowserWindow.loadURL("http://127.0.0.1:<port>")`。
6. 窗口退出时关闭后端进程。
7. Steam 打包上传 Electron builder 产物。

这样 Electron 不需要重新解决 LLM 配置、端口避让、编码、健康检查、敏感文件清理等底层问题。

## 维护约定

1. 任何新增的默认 LLM 配置来源都不得绕过 `SettingsService`。
2. API Key 不得写入 `settings.json`、静态配置、前端资源或日志。
3. 任何会要求用户处理 LLM 配置的错误，都应统一走 `llm_config_required` 链路。
4. 打包版新增宿主行为时，应优先通过环境变量控制，保持 GitHub 默认体验不变。
5. 后续实现 Electron 时，应先复查本 spec 的完成状态，再新增桌面壳逻辑。
