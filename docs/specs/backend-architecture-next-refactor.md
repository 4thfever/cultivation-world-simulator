# 后端架构后续收口方案

本文档记录 Phase 1 / Phase 2 后仍值得继续推进的后端重构计划。上一轮已经完成服务端 context / query-command service / save-load section registry / avatar presenter 拆分 / static registry / roleplay state model / simulator phase metadata 的基础落地。本轮目标是在这些地基上继续收口，减少兼容 shim、全局状态、巨型 service 与测试共享状态污染。

## 1. 背景

当前后端已经具备新的结构基础：

1. `ServerAppContext` 已经承接 server runtime、manager、settings、static data、query service、command service。
2. public v1 router 已经优先依赖 `GameQueryService` / `GameCommandService`。
3. `save_game()` / `load_game()` 顶层已经转为 section registry 编排。
4. avatar 的 prompt context、text presenter、API assembler 已有独立入口。
5. `StaticGameDataRegistry` 已经聚合主要静态配置表。
6. roleplay runtime session 已有显式状态模型来源。
7. simulator phase 顺序已有 `phase_registry.py` 元数据来源。

但这批改动为了降低风险，保留了不少兼容层与薄包装：

1. `src/server/main.py` 仍保留大量 `build_public_*`、`run_*`、settings、LLM、init/game loop 兼容导出。
2. `GameQueryService` / `GameCommandService` 仍包着旧 `public_query_builders.py` / `command_handlers.py`。
3. save/load section registry 已建立，但 load 恢复逻辑仍集中在 `registry.py` 的大函数中。
4. `roleplay_service.py` 仍然是一个混合状态机、LLM conversation、choice、history 和 pause 逻辑的大文件。
5. simulator phase registry 还没有真正驱动 `Simulator.step()`。
6. 测试中仍有 `main.game_instance`、`main.AVATAR_ASSETS`、`language_manager` 等共享全局状态污染风险。

本轮分两个 phase 推进：

- Phase 3：清理兼容层和服务端应用层边界。
- Phase 4：深化领域运行时、模拟器、roleplay 与测试隔离。

## 2. 总目标

1. 让 `main.py` 真正只保留启动入口。
2. 删除或压缩旧的 builder / handler 兼容层。
3. 让 query / command service 成为真实 use-case service，而不是 thin facade。
4. 让 save/load section 拆成可维护的独立模块。
5. 让 roleplay 进入显式状态机和 conversation service。
6. 让 simulator phase registry 逐步驱动 `step()`。
7. 统一测试 runtime fixture，降低全局状态污染。
8. 继续治理高风险 `CONFIG` 直连和领域对象反向依赖 server runtime 的问题。

## 3. 非目标

1. 不改变公共 API 的业务语义。
2. 不重写世界模拟规则。
3. 不引入多会话服务器或数据库化 world state。
4. 不一次性消灭所有 `CONFIG` 直连；只处理运行时语义、高风险缓存和 service 边界。
5. 不追求旧内部 helper 全兼容；当前仍以清晰主路径优先。

## 4. 设计原则

### 4.1 新主路径优先

旧兼容导出可以短期保留，但新增代码必须走 `ServerAppContext`、service、section、assembler、prompt context 等新路径。

### 4.2 Service 持有 context，而不是闭包持有依赖列表

`GameQueryService` 与 `GameCommandService` 应直接持有 context 或专门 dependency object，避免继续复制旧的超长参数注入模式。

### 4.3 Section 拆文件，registry 只排顺序

save/load registry 不应长期包含大段业务恢复逻辑。registry 的职责应该只是声明 section 顺序并执行。

### 4.4 Runtime 能力窄接口化

领域层如果需要暂停、choice、reset 检查等外部能力，应依赖窄接口，而不是通过 `world.runtime` 反向拿完整 server runtime。

### 4.5 测试隔离先行

任何继续瘦 `main.py` 或迁移全局状态的工作，都应先建立可复用 fixture，避免因为测试共享状态而掩盖真实回归。

## 5. Phase 3：服务端应用层与兼容层清理

Phase 3 目标是把上一轮建立的 context/service 从“新主路径薄包装”推进到“真实应用层边界”，同时显著缩小 `main.py`。

### 5.1 继续瘦身 main.py

当前 `main.py` 仍包含：

- runtime 创建
- manager 创建
- avatar assets 缓存
- query builder / command handler 兼容导出
- settings patch/reset wrapper
- LLM failure handler
- init progress / init_game_async
- game_loop / auto-save wiring
- FastAPI app 创建与 router 装配
- start 入口

建议拆分：

- `src/server/app_context.py`
  - 增加 `create_server_context(...)`。
- `src/server/runtime_hooks.py`
  - 放 `init_game_async`、`game_loop`、`trigger_auto_save` 等 runtime hook 创建。
- `src/server/settings_handlers.py`
  - 放 settings patch/reset、runtime locale 同步。
- `src/server/llm_runtime_handlers.py`
  - 放 LLM update / failure handling。
- `src/server/app_factory.py`
  - 放 FastAPI app + lifespan + route mount 创建。

验收点：

1. `main.py` 只保留编码初始化、参数解析、context/app 创建、`start()`。
2. `main.py` 不再直接创建 `public_query_builders` / `command_handlers`。
3. 旧测试若仍依赖 `main.game_instance` / `main.app`，通过兼容导出集中在 `main.py` 底部或测试 fixture 中处理。

### 5.2 合并 public_query_builders 到 GameQueryService

当前 `GameQueryService` 仍包着 `public_query_builders.py`。下一步应将 builders 的方法迁入 service。

建议：

1. `GameQueryService.__init__` 接收 `ServerAppContext` 或 `GameQueryDependencies`。
2. 把 `build_public_world_state()` 等方法迁为 service 方法。
3. `public_query_builders.py` 短期保留 shim，最终删除。
4. `game_queries.py` 按域拆小模块。

建议拆分：

- `src/server/queries/runtime_status.py`
- `src/server/queries/world_state.py`
- `src/server/queries/world_map.py`
- `src/server/queries/avatar_queries.py`
- `src/server/queries/event_queries.py`
- `src/server/queries/detail_queries.py`
- `src/server/queries/catalog_queries.py`
- `src/server/queries/sect_queries.py`
- `src/server/queries/dynasty_queries.py`

验收点：

1. 新 public query 不再进入 `public_query_builders.py`。
2. `GameQueryService` 直接实现 public query use case。
3. `game_queries.py` 文件长度显著下降或拆为空壳聚合。

### 5.3 合并 command_handlers 到 GameCommandService

当前 `GameCommandService` 仍包着 `command_handlers.py`。下一步应按命令域拆成 use-case service。

建议拆分：

- `GameLifecycleCommands`
- `AvatarCommands`
- `WorldCommands`
- `SaveLoadCommands`
- `RoleplayCommands`
- `CustomContentCommands`
- `EventCommands`

`GameCommandService` 负责聚合这些 command use case。router 只依赖 `GameCommandService`。

验收点：

1. 新 command 不再进入 `command_handlers.py`。
2. 所有修改世界状态的 command 仍通过 `runtime.run_mutation()`。
3. roleplay 中只修改 runtime metadata 的 command 必须保留注释说明不进入 world mutation lock 的原因。

### 5.4 深化 StaticGameDataRegistry

当前 `StaticGameDataRegistry` 只是薄包装。Phase 3 应让主要 public query 和 command 从 context 的 static data 读取。

优先迁移：

1. catalog query：sects、races、personas、realms、techniques、weapons、auxiliaries。
2. avatar create / adjustment。
3. save/load 恢复引用。
4. phenomenon query / command。

验收点：

1. `main.py` 不再为了 public API 注入一堆 `*_by_id`。
2. `GameQueryService` 和 `GameCommandService` 通过 `context.static_data` 访问静态表。
3. `reload_all_static_data()` 后 registry 更新策略明确。

### 5.5 继续拆 save/load section 文件

当前 section 协议已存在，但恢复逻辑仍集中在 `sections/registry.py`。Phase 3 应把 section 拆成独立文件。

建议文件：

- `src/sim/save/sections/meta.py`
- `src/sim/save/sections/run_config.py`
- `src/sim/save/sections/custom_content.py`
- `src/sim/save/sections/world_core.py`
- `src/sim/save/sections/map_state.py`
- `src/sim/save/sections/sect_runtime.py`
- `src/sim/save/sections/avatar.py`
- `src/sim/save/sections/region_runtime.py`
- `src/sim/save/sections/events.py`
- `src/sim/save/sections/simulator.py`

registry 职责：

1. 声明顺序。
2. 调用 `dump()` / `load()`。
3. 不放大段领域恢复逻辑。

验收点：

1. `registry.py` 不再超过少量编排代码。
2. 新增世界子系统时能新增 section，不需要改顶层 save/load。
3. `tests/test_save_load_*.py` 全绿。

### 5.6 测试隔离治理

Phase 3 应优先处理已经暴露的测试共享状态污染。

建议新增 fixture：

- `reset_server_runtime`
- `reset_avatar_assets`
- `reset_language_context`
- `reset_static_data_registry`

要求：

1. 涉及 `main.game_instance` 的测试统一走 fixture。
2. 涉及 `main.AVATAR_ASSETS` 的测试必须清空并恢复完整对象。
3. 涉及 `language_manager` 的测试必须恢复语言。
4. 避免浅拷贝含嵌套 mutable dict/list 的 runtime state。

验收点：

1. `pytest tests/test_save_load_*.py tests/test_public_api_v1.py` 同进程合跑不因状态污染失败。
2. websocket / settings / public API 测试不依赖执行顺序。

### 5.7 Phase 3 验收命令

建议至少运行：

- `pytest tests/test_public_api_v1.py`
- `pytest tests/test_websocket_handlers.py`
- `pytest tests/test_settings_service.py`
- `pytest tests/test_init_status_api.py`
- `pytest tests/test_game_init_integration.py`
- `pytest tests/test_save_load_*.py`
- `pytest tests/test_save_custom_name.py`
- `pytest tests/test_server_bootstrap.py`
- `pytest tests/test_server_binding.py`

## 6. Phase 4：领域运行时、roleplay、simulator 与配置治理深化

Phase 4 目标是进入更深层的 runtime / simulation / roleplay / config 边界，减少领域层反向依赖 server 和隐式全局配置。

### 6.1 Roleplay service 状态机化

当前已存在 `RoleplayStatus` 与 `RoleplaySession`，但 `roleplay_service.py` 仍然混合大量职责。

建议拆分：

- `src/server/services/roleplay_state_machine.py`
- `src/server/services/roleplay_choice_service.py`
- `src/server/services/roleplay_conversation_service.py`
- `src/server/services/roleplay_prompt_builder.py`
- `src/server/services/roleplay_history.py`

状态机职责：

1. 校验合法状态转移。
2. 创建/清理 pending request。
3. 管理 observing / awaiting_decision / awaiting_choice / conversing / submitting。
4. 明确 reset / load / reinit / start 后清空 runtime session。

Conversation service 职责：

1. 玩家输入。
2. 目标角色 LLM 回复。
3. summary 生成。
4. 原始聊天记录只留 runtime，不进长期事件流。

验收点：

1. 非法状态转移有明确错误。
2. `roleplay_service.py` 文件长度和职责明显下降。
3. `tests/test_single_choice.py`、`tests/test_public_api_v1.py`、`tests/test_mutual_actions.py` 全绿。

### 6.2 Simulator phase runner

当前 `phase_registry.py` 只提供相位元数据。Phase 4 应让它逐步驱动 `Simulator.step()`。

建议步骤：

1. 给 `SimulationPhase` 增加 handler 或 handler name。
2. 建立 `SimulationPhaseRunner`。
3. 将 reset check、事件收集、日志、phase enabled 规则集中到 runner。
4. `Simulator.step()` 只创建 context 并调用 runner。

注意：

- 不要一次性改写所有 phase 签名。
- 可以先迁移无复杂返回的 phase，再迁移 async phase。
- 每次迁移后保持 `tests/test_simulator.py` 全绿。

验收点：

1. 相位顺序由 `SIMULATION_PHASES` 驱动或至少可双向校验。
2. 新增 phase 时有顺序测试。
3. reset check 规则不再手写散落在 `step()`。

### 6.3 Runtime 能力窄接口化

当前一些领域逻辑通过 `world.runtime` 访问 server runtime。下一步应把这类能力拆窄。

建议接口：

- `CancellationToken`
- `ChoiceResolver`
- `RuntimePauseController`
- `RoleplayDecisionGateway`
- `RuntimeEventSink`

目标：

1. `World` 不需要知道完整 `GameSessionRuntime`。
2. simulator / single choice / roleplay 只依赖自己需要的 runtime 能力。
3. headless simulation 或测试可以构造轻量 runtime capabilities。

验收点：

1. 新代码不再新增 `world.runtime` 的直接依赖。
2. 旧 `world.runtime` 可以短期保留，但关键路径逐步迁移到 capability 对象。

### 6.4 配置 provider 治理

Phase 4 应继续清理高风险 `CONFIG` 直连。

优先级：

1. import 时冻结配置值的模块级变量。
2. save/load 路径和数量配置。
3. LLM template path。
4. fortune / opportunity / story / random minor event / sect random event 概率配置。
5. simulator phase 中影响运行时语义的配置。

建议新增：

- `src/config/providers.py`
  - `StaticConfigProvider`
  - `RuntimeConfigProvider`
  - `RunConfigProvider`

规则：

1. 本局参数优先读 `world.run_config_snapshot` 或 runtime current run。
2. 用户设置优先从 `SettingsService` 调用时读取。
3. 静态配置可通过 provider 包装 `src.utils.config.CONFIG`，避免模块初始化时绑定死对象。

验收点：

1. 没有高风险 import-time 配置缓存。
2. 测试 patch / config reload 后关键路径读取当前配置。
3. 不为低风险静态常量引入过度抽象。

### 6.5 WebSocket / game loop 收口

当前 `loop_runtime.py` 可继续拆：

- `GameLoopRunner`
- `TickPayloadBuilder`
- `AutoSaveScheduler`
- `RuntimeBroadcaster`
- `LoopErrorPolicy`

目标：

1. tick payload 构造可单测。
2. auto-save 调度独立。
3. broadcast 错误策略独立。
4. game loop 错误处理不再依赖零散 `print()`。

验收点：

1. `tests/test_websocket_handlers.py` 全绿。
2. game loop 相关测试可以独立测试 tick payload 和 pause 行为。

### 6.6 错误处理与日志统一

后端仍存在一些脚本式错误处理：

- `print()`
- `traceback.print_exc()`
- 返回 `(False, None)`
- 字符串错误信息直出

建议：

1. domain / service 抛明确异常。
2. API 层转换为稳定 error code。
3. 后台 loop 进入 structured logger。
4. 用户可见 toast/message 单独组装。

优先路径：

- save/load
- init_flow
- game_loop
- LLM 调用
- roleplay conversation

### 6.7 i18n / DTO 边界继续加固

继续避免 API DTO、LLM prompt context、UI 文案混用。

规则：

1. API DTO 优先提供 `id`、`label`、`desc` 结构。
2. 前端显示走后端本地化 DTO 或明确 i18n key。
3. LLM prompt context 不复用 UI 文案 DTO。
4. 短槽位和长说明分离。

优先模块：

- avatar detail
- sect detail
- race / persona / action option DTO
- roleplay pending request DTO

### 6.8 Phase 4 验收命令

建议至少运行：

- `pytest tests/test_single_choice.py`
- `pytest tests/test_public_api_v1.py`
- `pytest tests/test_mutual_actions.py`
- `pytest tests/test_simulator.py`
- `pytest tests/test_websocket_handlers.py`
- `pytest tests/test_settings_service.py`
- `pytest tests/test_llm_failures.py`
- `pytest tests/test_backend_locales.py`
- `pytest tests/test_frontend_locales.py`

## 7. 推荐执行顺序

### Phase 3 推荐顺序

1. 建测试隔离 fixture，先解决 `main.AVATAR_ASSETS` / runtime 状态污染。
2. 抽 `create_server_context()`，继续瘦 `main.py`。
3. 将 `public_query_builders.py` 迁入 `GameQueryService`。
4. 将 `command_handlers.py` 按命令域迁入 `GameCommandService` 聚合。
5. 深化 `StaticGameDataRegistry` 使用。
6. 拆 save/load section 文件。

### Phase 4 推荐顺序

1. 拆 `roleplay_service.py` 状态机和 conversation service。
2. 将 simulator phase registry 接入 phase runner。
3. 引入 runtime capability 窄接口，减少 `world.runtime` 反向依赖。
4. 做配置 provider 治理。
5. 收 WebSocket / game loop。
6. 统一错误处理与日志。
7. 加固 i18n / DTO 边界。

## 8. 风险与控制

### 8.1 风险：删除兼容层导致旧测试大面积失败

控制：

- 先迁移测试到新 fixture。
- shim 标记废弃后分批删除。
- 每删除一组旧导出，跑 public API / websocket / settings 回归。

### 8.2 风险：save/load section 顺序被拆散

控制：

- registry 保持唯一顺序真源。
- 对 section 顺序加测试。
- 对 avatar relation、region runtime、events migration 加针对性测试。

### 8.3 风险：roleplay 状态机重构引入行为回归

控制：

- 先补状态转移测试，再拆服务。
- 保持 runtime session 不进存档。
- 保持只在决策边界暂停。

### 8.4 风险：simulator phase runner 过度抽象

控制：

- 只做轻量 runner。
- 不一次性改所有 phase 签名。
- 每迁移一批 phase 就跑 `tests/test_simulator.py`。

### 8.5 风险：配置 provider 抽象污染静态配表

控制：

- 只治理运行时语义和 import-time 缓存。
- 静态常量表暂不强迁。
- 明确哪些配置属于 RunConfig、SettingsService、StaticConfig。

## 9. 完成后的目标模块地图

Phase 3 后：

- `src/server/main.py`
  - 轻量启动入口。
- `src/server/app_context.py`
  - context 创建和 server dependency 装配。
- `src/server/app_factory.py`
  - FastAPI app / lifespan / router / mounts。
- `src/server/settings_handlers.py`
  - settings 与 runtime locale 同步。
- `src/server/llm_runtime_handlers.py`
  - LLM update / failure handling。
- `src/server/queries/*`
  - 分域 query use case。
- `src/server/commands/*`
  - 分域 command use case。
- `src/sim/save/sections/*`
  - 独立 save/load sections。

Phase 4 后：

- `src/server/services/roleplay_state_machine.py`
  - roleplay 状态转移。
- `src/server/services/roleplay_conversation_service.py`
  - roleplay conversation。
- `src/sim/simulator_engine/phase_runner.py`
  - simulator phase runner。
- `src/server/runtime/capabilities.py`
  - runtime 窄接口。
- `src/config/providers.py`
  - config provider。
- `src/server/loop/*`
  - game loop、tick、auto-save、broadcast、error policy。

## 10. 后续维护约定

1. 新 public query 必须进入 `GameQueryService` 或 `server/queries/*`。
2. 新 command 必须进入 `GameCommandService` 或 `server/commands/*`，并说明 mutation lock 策略。
3. 新 save/load 字段必须优先新增或扩展 section。
4. 新 roleplay 状态必须进入状态机，不要散落裸 dict 状态判断。
5. 新 simulator phase 必须进入 phase registry，并补顺序测试。
6. 新测试若触碰 `main.game_instance`、`AVATAR_ASSETS`、`language_manager`，必须使用统一 fixture。
