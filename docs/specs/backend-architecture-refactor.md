# 后端架构收口重构方案

本文档记录后端架构体检后的重构计划。目标不是重写后端，而是把当前已经拆出来的 `server/runtime`、`server/services`、`server/api`、`simulator_engine/phases` 等模块继续收口成稳定边界，降低后续新增系统、外接 API、角色扮演、存档扩展和测试维护的成本。

## 1. 背景

当前后端已经完成过一轮重要拆分：

- `src/server/api/public_v1/*` 承载稳定公共 API 路由。
- `src/server/services/*` 承载一批 query / command / lifecycle service。
- `src/server/runtime/session.py` 引入 `GameSessionRuntime` 和 mutation lock。
- `src/server/init_flow.py`、`loop_runtime.py`、`host_app.py` 从 `main.py` 中拆出了初始化、后台循环和宿主装配。
- `src/sim/simulator_engine/phases/*` 已将模拟器 `step()` 的大部分业务相位拆出。

这些方向是正确的，但当前仍处在过渡态：

1. `src/server/main.py` 仍是事实上的 composition root、全局状态创建点和依赖总线。
2. `GameSessionRuntime` 底层仍是 `dict`，状态 schema 没有强类型边界。
3. `command_handlers.py` 与 `public_query_builders.py` 通过超长参数列表和 `SimpleNamespace` 组装能力。
4. 很多领域模块仍直接 import `CONFIG`，与 settings / run config / reload 语义存在摩擦。
5. `save_game()` / `load_game()` 已成为所有子系统追加字段的集中耦合点。
6. API DTO、领域展示、LLM prompt context、存档序列化在若干模块中仍有混杂。

本次重构分两个 phase 推进：第一阶段先收服务端运行时与装配边界，第二阶段再收领域边界、存档边界和配置读取方式。

## 2. 总目标

1. 让 `main.py` 回到轻量启动入口，不再承担后端依赖总线。
2. 让运行时状态从散落字符串 key 的 `dict` 过渡到可测试、可类型检查的结构化模型。
3. 让 query / command 入口成为稳定 service，而不是由超长参数闭包拼装。
4. 让会修改世界状态的 API 持续经过统一 mutation 入口串行化。
5. 让只读 API、前端 DTO、LLM prompt context、领域展示和存档序列化拥有更清楚的边界。
6. 让新增系统不再必须修改大型 `save_game()` / `load_game()` 函数。

## 3. 非目标

1. 不重写模拟器核心规则。
2. 不在本轮引入数据库化世界状态。
3. 不追求旧内部接口完全兼容；当前仍处开发阶段，以清晰主路径优先。
4. 不把所有领域系统一次性改成依赖注入；先处理高收益边界。
5. 不改变公共 API 的语义契约，除非为统一 query / command 响应格式所必需。

## 4. 设计原则

### 4.1 Composition root 单一化

服务端依赖装配应集中在明确的 app context / container 中，避免继续让 `main.py` 直接持有大量全局对象。

### 4.2 Runtime 是唯一运行时状态入口

外部 API、后台 loop、初始化、读档和角色扮演应通过 `GameSessionRuntime` 访问当前世界和模拟器。新增代码不应直接读写 `game_instance`。

### 4.3 Query / Command 分离

只读能力进入 `GameQueryService`，写入能力进入 `GameCommandService`。写入能力必须通过 `runtime.run_mutation()` 或明确说明为什么不需要等待世界 mutation lock。

### 4.4 DTO 与领域对象分离

前端 DTO、外部 API DTO、LLM prompt context、文本展示、存档 payload 不应混在同一个 presenter 中长期演进。

### 4.5 配置调用时读取

影响运行时语义的配置应优先从当前 settings / run config / config provider 调用时读取，避免模块 import 时冻结配置对象。

## 5. Phase 1：服务端运行时与装配边界收口

Phase 1 聚焦 `src/server/**`。目标是在不大改领域逻辑的前提下，把 server 层从“闭包和全局变量拼装”推进到“明确上下文对象和服务对象”。

### 5.1 新增 ServerAppContext

建议新增：

- `src/server/app_context.py`

核心对象：

```python
@dataclass
class ServerAppContext:
    runtime: GameSessionRuntime
    manager: ConnectionManager
    avatar_assets: dict[str, dict[str, list[int]]]
    settings_service: SettingsService
    static_data: StaticGameDataRegistry | None
    config_provider: ConfigProvider
    query_service: GameQueryService
    command_service: GameCommandService
```

第一步可以不一次性补齐所有字段，允许 `static_data` / `config_provider` 先用薄包装承接现有全局 registry 和 `CONFIG`。

要求：

1. `main.py` 不再直接维护散落的 query builder / command handler 全局对象。
2. router 装配只接收 `context.query_service` 与 `context.command_service`。
3. 测试可以独立构造 `ServerAppContext`，无需 import 完整 `main.py`。

### 5.2 收敛 main.py

`src/server/main.py` 最终职责：

1. 修复 import path 与编码。
2. 解析 `--dev` 等启动参数。
3. 调用 `create_server_context(...)`。
4. 调用 `create_fastapi_app(context, ...)`。
5. 调用 `start_server(...)`。

不再承担：

1. 创建并散落暴露 query builder / command handler。
2. 直接传递几十个函数依赖。
3. 大量导入领域 registry 后逐个塞进闭包。

### 5.3 GameSessionState 类型化

建议在 `src/server/runtime/session.py` 或新文件中引入：

- `GameSessionState`
- `InitRuntimeState`
- `PauseRuntimeState`
- `LLMRuntimeState`
- `RoleplayRuntimeState`

初始阶段可以保留 `runtime.state` 对外兼容测试，但新增代码应使用明确方法：

- `runtime.get_world()`
- `runtime.require_world()`
- `runtime.get_simulator()`
- `runtime.set_world_and_sim(world, sim)`
- `runtime.mark_pending_initialization(clear_world=True)`
- `runtime.finish_initialization(...)`
- `runtime.fail_initialization(error)`
- `runtime.set_paused(...)`
- `runtime.clear_roleplay_session()`

验收点：

1. 新增 server 代码不再通过裸字符串 key 读写 `game_instance`。
2. 旧测试若仍 patch `game_instance`，可以暂时通过兼容层运行。
3. runtime state 的默认值由一个函数或 dataclass factory 生成，避免共享可变默认值。

### 5.4 GameQueryService

建议新增：

- `src/server/services/game_query_service.py`

职责：

1. 聚合现有 `public_query_builders.py` 和 `services/game_queries.py`。
2. 对 router 暴露稳定方法，例如：
   - `get_runtime_status()`
   - `get_current_run()`
   - `get_world_state()`
   - `get_world_map(locale=None)`
   - `get_events_page(...)`
   - `get_avatar_list()`
   - `get_detail(target_type, target_id)`
   - `get_rankings()`
3. 内部可继续调用现有 assembler / serializer，但依赖来自 context，而不是超长函数参数。

第一阶段不要求彻底拆小 `game_queries.py`，但不再新增新的 public query 到 `public_query_builders.py`。

### 5.5 GameCommandService

建议新增：

- `src/server/services/game_command_service.py`

职责：

1. 聚合现有 `command_handlers.py`。
2. 对 router 暴露稳定 command 方法，例如：
   - `start_game(req)`
   - `reinit_game()`
   - `reset_game()`
   - `pause_game()`
   - `resume_game()`
   - `load_game(filename)`
   - `save_game(custom_name)`
   - `create_avatar(req)`
   - `delete_avatar(avatar_id)`
   - `set_world_phenomenon(phenomenon_id)`
   - `start_roleplay(avatar_id)`
   - `submit_roleplay_decision(...)`
3. 所有会修改世界状态的 command 通过 `runtime.run_mutation()` 串行化。

角色扮演中只修改 runtime session metadata 的命令可以不进入 mutation lock，但必须在方法注释里说明原因。

### 5.6 Router 依赖简化

现有 `configure_routes_and_mounts(...)` 参数列表过长。Phase 1 后路由装配应改成：

```python
configure_routes_and_mounts(
    app=app,
    context=context,
    assets_path=assets_path,
    web_dist_path=web_dist_path,
    is_dev_mode=is_dev_mode,
)
```

各 router factory 只接收需要的 service：

- `create_public_query_router(query_service=context.query_service)`
- `create_public_command_router(command_service=context.command_service)`
- `create_settings_router(settings_service=context.settings_service, ...)`
- `create_websocket_router(manager=context.manager, runtime=context.runtime)`

### 5.7 Phase 1 验收标准

1. `src/server/main.py` 文件长度明显下降，只保留启动和装配入口。
2. `create_command_handlers()` 和 `create_public_query_builders()` 不再是新增能力入口；可以保留兼容 shim，但应标记为待删除。
3. public v1 router 不直接接收几十个 handler 函数，而是依赖 service 对象。
4. `GameSessionRuntime` 拥有结构化 state 或等价 typed facade。
5. 现有 API 测试通过：
   - `pytest tests/test_public_api_v1.py`
   - `pytest tests/test_websocket_handlers.py`
   - `pytest tests/test_init_status_api.py`
   - `pytest tests/test_game_init_integration.py`
6. server bootstrap 相关测试通过：
   - `pytest tests/test_server_bootstrap.py`
   - `pytest tests/test_server_binding.py`

## 6. Phase 2：领域边界、存档与配置读取收口

Phase 2 在 Phase 1 的上下文对象和 service 边界稳定后推进。目标是降低领域系统之间的隐性耦合，尤其是存档、配置、DTO、LLM prompt context 这几条长期增长线。

### 6.1 Save / Load Section Registry

当前 `src/sim/save/save_game.py` 与 `src/sim/load/load_game.py` 是存档扩展的集中耦合点。建议引入 section registry。

建议新增：

- `src/sim/save/sections/base.py`
- `src/sim/save/sections/world_core.py`
- `src/sim/save/sections/map_snapshot.py`
- `src/sim/save/sections/sect_runtime.py`
- `src/sim/save/sections/dynasty.py`
- `src/sim/save/sections/opportunity.py`
- `src/sim/save/sections/world_secret.py`
- `src/sim/save/sections/avatar.py`
- `src/sim/save/sections/events.py`

核心协议：

```python
class SaveSection(Protocol):
    key: str

    def dump(self, context: SaveContext) -> Any:
        ...

    def load(self, context: LoadContext, payload: Any) -> None:
        ...
```

顶层 `save_game()` / `load_game()` 只负责：

1. 创建 context。
2. 按固定顺序调用 sections。
3. 处理文件 IO。
4. 处理少量跨 section 的装配顺序。

要求：

1. 新增世界系统时优先新增 section，不继续膨胀顶层函数。
2. 旧存档兼容仅在零代价时保留，不为旧结构牺牲新主路径清晰度。
3. 所有 section payload 必须只包含 JSON 基础类型。

### 6.2 DTO / Presenter / Prompt Context 拆分

角色、宗门、地图、事件这几类信息需要区分不同输出用途：

1. API DTO：前端与外部 API 消费。
2. 文本展示：本地化人类可读文本。
3. LLM prompt context：面向模型的压缩结构。
4. 存档 payload：稳定可恢复的基础类型。

建议优先从角色信息开始：

- `src/server/assemblers/avatar_detail.py`
- `src/server/assemblers/avatar_list.py`
- `src/classes/core/avatar/text_presenter.py`
- `src/classes/core/avatar/prompt_context.py`

`src/classes/core/avatar/info_presenter.py` 可以先保留兼容导出，但新代码不再继续往里面追加职责。

验收点：

1. `Avatar.get_info()` 不再成为 API DTO 和 LLM context 的共同入口。
2. 前端详情页 DTO 由 server assembler 生成。
3. LLM prompt 使用 prompt context builder。
4. 文本展示与 i18n key 处理集中在 text presenter。

### 6.3 配置读取治理

Phase 2 应逐步清理模块级 `CONFIG` 直连，优先级如下：

1. import 时冻结配置值的模块级变量。
2. 影响运行时语义的世界规则配置。
3. LLM template path / prompt 配置。
4. save/load 路径与保存数量配置。
5. 静态资源 registry 加载路径。

建议引入轻量 provider：

- `StaticConfigProvider`
- `RuntimeConfigProvider`
- `RunConfigProvider`

规则：

1. 本局参数优先从 `world.run_config_snapshot` 或 `runtime.current_run_config` 读取。
2. 用户设置优先从 `SettingsService` 调用时读取。
3. 静态配置可以通过 provider 包装当前 `CONFIG`，避免模块初始化绑定死对象。

短期允许继续使用 `CONFIG` 的场景：

1. 静态枚举 / 常量表加载。
2. 不受 settings reload 或 run config 影响的版本内置规则。
3. 测试已有明确 patch 且迁移收益不高的边缘模块。

### 6.4 StaticGameDataRegistry

建议将现有全局配置表逐步收敛到：

- `src/run/static_data_registry.py`

包含：

- sects
- techniques
- weapons
- auxiliaries
- personas
- races
- goldfingers
- celestial phenomena
- maps / map presets metadata

第一阶段可以只是薄包装，内部仍引用现有全局 dict。后续 reload 时由 registry 统一刷新。

验收点：

1. server context 通过 `context.static_data` 访问静态数据。
2. API query 不再直接从 `main.py` 注入一堆 `*_by_id`。
3. save/load 恢复引用时优先使用 registry。

### 6.5 Roleplay State Machine

角色扮演 service 当前实质上是一个状态机。Phase 2 建议显式化：

- `RoleplaySession`
- `RoleplayStatus`
- `PendingDecisionRequest`
- `PendingChoiceRequest`
- `PendingConversationRequest`
- `RoleplayStateMachine`
- `RoleplayConversationService`

规则：

1. runtime session 不进存档。
2. reset / load / reinit / start 后显式清空。
3. 只在决策边界暂停。
4. conversation 原始聊天记录不进长期事件流，只允许 summary 落地。

验收点：

1. 非法状态转移有明确错误。
2. pending request 的类型和值结构不再靠裸 dict 约定。
3. roleplay service 文件长度和职责明显下降。

### 6.6 Simulator Phase 元数据化

模拟器相位拆分方向保留。Phase 2 可考虑轻量 phase registry：

```python
@dataclass(frozen=True)
class SimulationPhase:
    name: str
    index: int
    handler: Callable[..., Awaitable[list[Event] | None] | list[Event] | None]
    reset_check_after: bool = True
```

目标：

1. 相位顺序不再只靠 `step()` 中的注释维护。
2. 新增相位时可以测试 phase list 顺序。
3. reset check 规则显式化。

不要求引入复杂 pipeline 框架。

### 6.7 Phase 2 验收标准

1. `save_game()` / `load_game()` 顶层函数只做编排，子系统保存恢复由 section 负责。
2. 至少角色 DTO / prompt context / text presenter 拆分完成。
3. 高风险模块级 `CONFIG` 缓存清理完成，尤其 import 时冻结值的点。
4. 静态数据 registry 至少覆盖 public API query 所需的主要 registry。
5. roleplay runtime state 有显式模型或状态机。
6. 模拟器相位顺序有可测试的元数据来源。
7. 相关测试通过：
   - `pytest tests/test_save_load_*.py`
   - `pytest tests/test_public_api_v1.py`
   - `pytest tests/test_single_choice.py`
   - `pytest tests/test_mutual_actions.py`
   - `pytest tests/test_simulator.py`

## 7. 推荐落地顺序

### Phase 1 推荐顺序

1. 新增 `ServerAppContext`，把 `runtime`、`manager`、`avatar_assets` 收进去。
2. 新增 `GameQueryService`，先包住现有 query builder，不急着拆所有 query。
3. 新增 `GameCommandService`，先包住现有 command handlers。
4. 改 router factory，让它们依赖 service 对象。
5. 缩减 `main.py`。
6. 类型化 `GameSessionRuntime` 的高频状态访问方法。

### Phase 2 推荐顺序

1. 先做 save/load section registry，因为它会降低后续所有系统扩展成本。
2. 拆角色 DTO / prompt context / text presenter。
3. 引入 static data registry 薄包装。
4. 清理高风险 `CONFIG` import-time 缓存。
5. 显式化 roleplay state machine。
6. 做 simulator phase metadata。

## 8. 风险与控制

### 8.1 风险：一次性改动过大

控制：

- Phase 1 先用 wrapper 包住现有能力，不强行重写领域逻辑。
- 保留兼容 shim，等测试和调用点迁移完成后再删除。

### 8.2 风险：测试 patch 依赖旧全局对象

控制：

- `GameSessionRuntime.state` 可短期保留 dict 视图。
- `main.py` 可短期导出 `runtime` / `game_instance` 兼容旧测试，但新增测试应构造 context。

### 8.3 风险：配置 provider 抽象过度

控制：

- 只在运行时语义会变化的地方引入 provider。
- 静态常量表和低风险模块暂不强行迁移。

### 8.4 风险：save/load section 顺序错误

控制：

- section registry 必须显式定义顺序。
- 对 map、sect、avatar、relations、events 这些有依赖顺序的 section 加测试。

## 9. 完成后的目标模块地图

Phase 1 后：

- `src/server/main.py`
  - 轻量启动入口。
- `src/server/app_context.py`
  - 服务端上下文与依赖装配。
- `src/server/runtime/session.py`
  - 结构化运行时状态与 mutation lock。
- `src/server/services/game_query_service.py`
  - public query use cases。
- `src/server/services/game_command_service.py`
  - public command use cases。
- `src/server/host_app.py`
  - FastAPI app、lifespan、router、mounts。

Phase 2 后：

- `src/sim/save/sections/*`
  - 分段存档与恢复。
- `src/run/static_data_registry.py`
  - 静态配置表聚合。
- `src/server/assemblers/*`
  - 前端与外部 API DTO 组装。
- `src/classes/core/avatar/prompt_context.py`
  - 角色 LLM prompt context。
- `src/classes/core/avatar/text_presenter.py`
  - 角色文本展示。
- `src/server/services/roleplay_state_machine.py`
  - 角色扮演 runtime 状态机。

## 10. 后续维护约定

1. 新增公共只读接口优先进入 `GameQueryService`。
2. 新增公共写接口优先进入 `GameCommandService`，并说明 mutation lock 策略。
3. 新增世界子系统时必须考虑 save/load section，而不是直接扩写顶层 `save_game()` / `load_game()`。
4. 新增前端 DTO 时优先落到 `server/assemblers`。
5. 新增 LLM prompt context 时优先落到独立 prompt context builder。
6. 若修改本 spec 对应规则，应同步检查 `AGENTS.md` 与 `.cursor/rules` 是否需要更新。
