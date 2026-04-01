---
description: 统一配置架构与用户数据目录规范
globs: src/config/**/*.py, src/server/**/*.py, src/utils/config.py, src/utils/llm/**/*.py, src/sim/save/**/*.py, src/sim/load/**/*.py, web/src/stores/setting.ts, web/src/api/modules/system.ts, web/src/api/modules/llm.ts, web/src/components/game/panels/system/**/*.vue, web/src/App.vue
---
# 配置架构规范

## 1. 三层配置边界
- `static/config.yml` 及其派生 `CONFIG` 只承载**只读版本配置 / 平衡参数**，不要再写入用户设置。
- `src/config/settings_service.py` 管理**应用设置**（`settings.json`）和**敏感信息**（`secrets.json`），所有用户设置读写必须收敛到这里。
- `RunConfig` 代表**当前这局游戏的启动快照**；开局后逻辑和存档应读取 `run_config`，不要回头读/写用户设置文件。

## 2. 用户数据目录
- 用户数据必须写入 `src/config/data_paths.py` 计算出的 data root，不得写回 `static/`、仓库根目录或 `web/localStorage` 作为正式真源。
- 存档路径统一走 `CONFIG.paths.saves`，其值由 `data_paths` 注入；不要手写 `assets/saves` 或 `static/local_config.yml`。
- 测试中涉及 settings/secrets/saves 时，必须通过 `tests/conftest.py` 的临时数据目录隔离。

## 3. 前后端职责
- 前端正式设置的唯一真源是 `/api/settings`，不要再拆成语言/自动存档/开局配置多个独立真源。
- `SystemMenu`、`GameStartPanel`、`LLMConfigPanel` 应只消费 `stores/setting.ts`，避免组件各自 mount 后再 fetch 一套状态。
- 不要在前端启动时把 UI 语言反向覆盖到后端内容语言；`ui.locale` 和 `RunConfig.content_locale` 是两条独立链路。

## 4. LLM 设置
- LLM 非敏感配置放 `settings.json`，API Key 放 `secrets.json`；即使当前允许明文，也不要再把 key 混进普通设置文件。
- `/api/settings/llm` 不返回已保存的 key，只返回 `has_api_key`；“留空”表示保持不变，“清空”必须是显式动作。
- 运行时 LLM 读取统一走 `src.utils.llm.config` + `SettingsService`，不要再直接读 `CONFIG.llm`。

## 5. 存档与读档
- 存档必须保存 `run_config` 快照；读档恢复时用该快照恢复内容语言与运行参数，不要回写应用设置。
- 若新增与本局相关的启动参数，应优先放入 `RunConfig` 并在存档中持久化。

## 6. Docker 持久化约束
- Docker Compose / 自建容器必须显式设置 `CWS_DATA_DIR`，并把该目录挂载到宿主机持久卷。
- 不要依赖 `assets/saves` 作为运行时存档真源；后端运行时存档路径由 `CONFIG.paths.saves` 注入到 `data_paths`。
- 仓库根目录 `docker-compose.yml` 的约定数据目录为 `/data`，宿主机默认映射 `./docker-data:/data`，后续部署改动需保持语义一致。
