# 配置架构重构说明

本文档记录 2026-04 的配置系统重构结果，作为后续开发时的单一设计参考。

## 目标

本次重构的目标不是兼容旧结构，而是把配置边界重新拉直：

1. `static/config.yml` 只保留版本内置静态配置。
2. 用户设置和敏感信息统一由 `SettingsService` 管理。
3. 开局参数统一由 `RunConfig` 表达，并随存档保存。
4. 清除历史废弃配置，不再保留旧字段兜底。

## 最终分层

### 1. 静态配置

文件：

- `static/config.yml`
- `src/utils/config.py`

职责：

- 版本号
- 静态资源目录
- 游戏平衡参数
- 世界规则和故事概率
- LLM 任务级默认模式
- 前端内置默认表现参数

限制：

- 不承载用户偏好
- 不承载 API Key
- 不承载本局启动参数
- 不承载部署地址和端口

### 2. 应用设置

文件：

- `settings.json`
- `secrets.json`
- `src/config/settings_schema.py`
- `src/config/settings_service.py`

职责：

- UI 语言
- 音量
- 自动存档设置
- LLM profile
- 新开局默认参数
- API Key

限制：

- 不写回 `static/config.yml`
- 前端正式真源统一是 `/api/settings`

### 3. 本局运行配置

类型：

- `RunConfig`

职责：

- `content_locale`
- `init_npc_num`
- `sect_num`
- `npc_awakening_rate_per_month`
- `world_lore`

规则：

1. 新开局时由前端请求生成。
2. 服务端将快照写入 `game_instance["run_config"]`。
3. 世界对象将其保存到 `world.run_config_snapshot`。
4. 存档必须序列化 `run_config`。
5. 读档恢复时优先恢复该快照，而不是回退到静态配置。

### 4. 部署环境配置

来源：

- `SERVER_HOST`
- `SERVER_PORT`
- `CWS_DATA_DIR`

职责：

- 服务监听地址
- 服务端口
- 用户数据根目录

限制：

- 不再通过 `static/config.yml` 承载

## 前端配置边界

前端当前有两条不同的配置链路，必须分开理解：

### 1. 应用设置链路

来源：

- `/api/settings`
- `useSettingStore`

职责：

- UI 语言
- 音量
- 自动存档
- LLM 设置
- 新开局默认参数

约束：

- `ui.locale` 与 `new_game_defaults.content_locale` 是两条独立链路
- 前端不得在切换 UI 语言时自动覆盖内容语言
- 启动新游戏时提交的 `RunConfig` 应直接来自当前 draft

### 2. 地图渲染默认链路

来源：

- `/api/v1/query/world/map -> render_config`
- `useMapStore`

职责：

- `water_speed`
- `cloud_frequency`

约束：

- 这组参数表示静态地图表现默认值，不属于用户设置
- 命名上统一使用 `render_config` / `renderConfig` / `MapRenderConfigDTO`
- 不再使用过于宽泛的 `config` / `frontendConfig` 命名

## 当前静态配置结构

`static/config.yml` 目前采用以下顶层结构：

- `meta`
- `resources`
- `llm`
- `ai`
- `world`
- `sect`
- `avatar`
- `social`
- `nickname`
- `save`
- `frontend_defaults`
- `df`
- `play`

其中：

- `resources` 只描述静态资源根目录
- `world` 只描述世界规则，不再包含新开局默认值
- `frontend_defaults` 表示前端内置默认表现，不是用户设置

## 已删除的废弃配置

以下配置已从静态配置中彻底删除：

- `system.language`
- `system.host`
- `system.port`
- `paths.saves`
- `ai.max_concurrent_requests`
- 注释形式保留的旧 `templates/game_configs` 路径残留

这些字段不再有兼容 alias，也不再有回退逻辑。

## 核心设计约束

### 1. `CONFIG` 不是万能真源

`src.utils.config.CONFIG` 现在只代表静态配置���运行期派生出的资源路径。

禁止：

- 从 `CONFIG` 读取用户设置
- 从 `CONFIG` 读取本局启动参数
- 从 `CONFIG` 读取 host/port

### 2. `RunConfig` 是开局参数唯一真源

服务端 `get_runtime_run_config()` 只允许：

1. 返回当前运行中的 `game_instance["run_config"]`
2. 否则返回 `SettingsService.get_default_run_config()`

禁止再从 `CONFIG.world` 回退读取开局参数。

### 3. 用户数据目录统一由 `data_paths` 决定

运行时的 `CONFIG.paths.saves` 只是 `data_paths` 注入后的派生结果。

它不是静态配置字段，不允许在 `static/config.yml` 中重新定义。

### 4. 语言资源路径必须显式切换

`update_paths_for_language()` 的职责是“给定语言后切换静态资源路径”，
而不是“从静态配置猜测当前用户语言”。

因此默认语言选择属于 settings / runtime 层，不属于静态配置层。

## 后续新增配置时的放置规则

新增字段前先判断它属于哪一层：

1. 如果它跟版本一起发布、主要用于平衡或静态规则，放 `static/config.yml`。
2. 如果它是用户偏好、可在设置页修改，放 `settings.json`。
3. 如果它只在这一局开始时确定，并需要随存档保存，放 `RunConfig`。
4. 如果它跟部署环境有关，放环境变量。

若一个字段同时想放进两层，通常说明职责划分有问题，应先重新建模。
