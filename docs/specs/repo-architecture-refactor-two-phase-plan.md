# 仓库架构重构两阶段计划

本文档记录当前仓库下一轮值得推进的重构计划。目标不是推翻重写，而是在已经落地的
runtime、service、section、composable 等基础上继续收口，减少薄包装、兼容出口和领域大文件。

截至当前代码状态，前端若干历史计划已经基本完成，例如 HTTP timeout 与 caller abort 语义、
Pixi 地图旧对象销毁、全局音效模块化、状态栏弹窗 registry、`AvatarDetail` 展示层拆分等。
因此本轮不再把这些已完成事项列为主要目标。

本计划分两个 phase：

1. Phase 1：后端应用层边界收口，优先处理会影响后续 API、测试与外接控制能力的结构问题。已完成。
2. Phase 2：领域模块拆分与模拟器深化，在主路径稳定后清理长期维护负担。已完成。

## 1. 当前状态

当前仓库已经具备以下基础：

1. `ServerAppContext` 已经承接 runtime、manager、settings、static data、query service、command service。
2. `/api/v1/query/*` 与 `/api/v1/command/*` 已经优先依赖 `GameQueryService` / `GameCommandService`。
3. `save_game()` 顶层已经通过 section registry 编排 dump。
4. simulator `step()` 已经委托 `SimulationPhaseRunner`，phase 顺序由 `phase_registry.py` 记录。
5. roleplay 已拆出 state、state machine、conversation service、prompt builder、history 等辅助模块。
6. 前端状态栏弹窗已经 registry 化，`worldStore` 的旧跨 store proxy 主调用点已清理。

Phase 1 完成后，应用层迁移中段问题已经收口：

1. `src/server/main.py` 已通过 `create_server_context()` 组装 context/service，旧 helper 导出集中为 legacy adapter。
2. `GameQueryService` / `GameCommandService` 已直接持有 dependency object 并实现 public use case。
3. `public_query_builders.py` / `command_handlers.py` 已退化为兼容 shim，新主路径不再依赖它们。
4. 测试侧已增加 `main.game_instance` 自动隔离，降低历史全局 dict patch 的污染风险。

Phase 2 完成后，领域维护负担已经收口：

1. load restore 已拆为 `src/sim/save/sections/load_*.py` section，`load_restore.py` 只编排顺序。
2. `src/sim/avatar_init.py` 已迁为 `src/sim/avatar_init/` package，并提供 planning/factory/equipment/relations/sect_assignment/request_parser 边界。
3. `src/systems/opportunity.py` 已迁为 `src/systems/opportunity/` package，并提供 models/manager/targeting/outcomes/events/phases/context 边界。
4. simulator phase registry 已绑定 handler metadata，runner 直接执行 registry handler。

## 2. 非目标

1. 不改变公共 API 的业务语义。
2. 不重写世界模拟规则。
3. 不引入多会话服务器、数据库化 world state 或新的前端状态框架。
4. 不为旧内部 helper 付出复杂兼容成本；开发阶段仍以清晰主路径优先。
5. 不把已经完成的前端历史修复重新纳入本轮 scope。
6. 不在一次改动中同时迁移 query、command、save/load 和领域大文件。

## 3. 设计原则

### 3.1 新主路径优先

新增服务端 API、query、command、runtime hook 不应再从 `src/server/main.py` 取全局对象或注册兼容导出。
旧兼容导出可以短期保留，但必须集中、可识别，并只服务旧测试或旧入口。

### 3.2 Service 是 use case，不是 facade

`GameQueryService` 与 `GameCommandService` 应直接实现或聚合 use-case service，而不是长期暴露
`.builders` / `.handlers` 给调用侧。

### 3.3 Section 对称化

save 与 load 应按同一套 section 边界演进。registry 只声明顺序和执行，不放大段领域恢复逻辑。

### 3.4 测试隔离先行

任何继续清理 `main.py` 全局状态的工作，都应先建立或复用测试 fixture，避免共享 runtime、
avatar assets、language context、static registry 污染测试结果。

### 3.5 分批迁移

先收后端应用层，再拆领域大文件。每一步都应能单独验证、单独提交。

## 4. Phase 1：应用层边界收口（已完成）

Phase 1 目标是让服务端主路径从“薄包装 + 兼容出口”推进到“真实 context/service 边界”。

完成状态：

1. `src/server/app_context.py` 已提供 `create_server_context()`。
2. `src/server/main.py` 已改为通过 context factory 创建 `ServerAppContext`、`GameQueryService`、`GameCommandService`。
3. `src/server/services/game_query_service.py` 已直接实现 public query use case。
4. `src/server/services/game_command_service.py` 已直接实现 public command use case，并保留 mutation lock 语义。
5. `src/server/public_query_builders.py` 与 `src/server/command_handlers.py` 已变为 legacy adapter。
6. `tests/conftest.py` 已新增 server runtime state 自动隔离 fixture。
7. `tests/test_backend_phase3_architecture.py` 已补充架构约束测试。

### 4.1 建立服务端测试隔离 fixture

优先处理测试共享状态污染风险。建议新增或统一以下 fixture：

1. `reset_server_runtime`
2. `reset_avatar_assets`
3. `reset_language_context`
4. `reset_static_data_registry`

要求：

1. 涉及 `main.game_instance` 的测试统一走 fixture。
2. 涉及 `main.AVATAR_ASSETS` 的测试必须恢复为完整初始结构。
3. 涉及 `language_manager` 的测试必须恢复语言。
4. 避免浅拷贝含嵌套 mutable dict/list 的 runtime state。

验收点：

1. `pytest tests/test_public_api_v1.py tests/test_websocket_handlers.py tests/test_settings_service.py`
   同进程合跑不依赖执行顺序。
2. save/load、settings、websocket、public API 测试不因上一个测试留下的全局状态失败。

### 4.2 继续瘦身 `src/server/main.py`

当前 `main.py` 仍包含：

1. `game_instance` / `runtime` / `manager` 创建。
2. static data 创建与多份 `*_by_id` 兼容变量。
3. `GameQueryService` / `GameCommandService` 组装。
4. 一长串 `build_public_*` 兼容导出。
5. 一长串 `run_*` command 兼容导出。
6. settings、LLM、init、game loop 的兼容 wrapper。
7. FastAPI app 创建与启动入口。

建议：

1. 在 `src/server/app_context.py` 中新增或完善 `create_server_context(...)`。
2. 把 static data、runtime、manager、query service、command service 的组装移出 `main.py`。
3. `main.py` 只保留编码初始化、命令行参数、runtime path、context/app 创建、`start()`。
4. 仍必须保留的旧兼容导出集中放到底部，并标注为测试/历史入口。
5. 新代码不得新增 `main.py` 级别的 `build_public_*` 或 `run_*`。

验收点：

1. `main.py` 不再直接创建 public query builders 或 command handlers。
2. `main.py` 不再作为新增 query/command 的注册地点。
3. 路由和 app factory 只依赖 `ServerAppContext` 与 service 对象。

### 4.3 将 `GameQueryService` 从 facade 迁为真实 query service

当前 `GameQueryService` 主要包裹 `public_query_builders.py`。下一步应把 query use case 迁入 service
或 service 聚合的 query 模块。

建议拆分：

1. `src/server/queries/runtime_status.py`
2. `src/server/queries/world_state.py`
3. `src/server/queries/world_map.py`
4. `src/server/queries/avatar_queries.py`
5. `src/server/queries/event_queries.py`
6. `src/server/queries/detail_queries.py`
7. `src/server/queries/catalog_queries.py`
8. `src/server/queries/sect_queries.py`
9. `src/server/queries/dynasty_queries.py`

迁移顺序建议：

1. 先迁低风险纯读 query：runtime status、current run、avatar meta、phenomena、game data catalog。
2. 再迁 world state / world map / events / detail 这类数据结构较复杂的 query。
3. 最后删除或压缩 `public_query_builders.py` shim。

验收点：

1. 新 public query 不再进入 `public_query_builders.py`。
2. router 调用 `GameQueryService` 方法，不接触 builder namespace。
3. `GameQueryService` 直接持有 `ServerAppContext` 或明确的 `GameQueryDependencies`。
4. `game_queries.py` 显著变薄，或被拆成领域 query 模块。

### 4.4 将 `GameCommandService` 从 facade 迁为 command use case 聚合

当前 `GameCommandService` 主要包裹 `command_handlers.py`。下一步应按命令域拆分。

建议拆分：

1. `GameLifecycleCommands`
2. `AvatarCommands`
3. `WorldCommands`
4. `SaveLoadCommands`
5. `RoleplayCommands`
6. `CustomContentCommands`
7. `EventCommands`

要求：

1. 所有修改世界状态的 command 必须继续通过 `runtime.run_mutation()` 串行化。
2. 只修改 roleplay runtime metadata 的 command 可以不进入 world mutation lock，但必须保留注释说明原因。
3. router 只依赖 `GameCommandService`，不直接依赖领域 command 类。
4. 新 command 不再进入 `command_handlers.py`。

验收点：

1. `command_handlers.py` 不再是新增命令主路径。
2. `GameCommandService` 聚合各领域 command use case。
3. public command tests 继续覆盖 pause/resume/init/save/load/avatar/custom content/roleplay。

### 4.5 深化 `StaticGameDataRegistry`

当前 static registry 已存在，但部分路径仍通过散落的 `*_by_id` 变量注入。

优先迁移：

1. catalog query：sects、races、personas、realms、techniques、weapons、auxiliaries。
2. avatar create / adjustment。
3. save/load 恢复引用。
4. phenomenon query / command。

验收点：

1. `main.py` 不再为了 public API 注入一堆 `*_by_id`。
2. query/command service 通过 `context.static_data` 访问静态表。
3. `reload_all_static_data()` 后 registry 更新策略明确。

### 4.6 Phase 1 验收记录

已运行并通过：

```powershell
pytest tests/test_public_api_v1.py tests/test_websocket_handlers.py tests/test_settings_service.py tests/test_init_status_api.py tests/test_game_init_integration.py tests/test_server_bootstrap.py tests/test_server_binding.py -q
pytest <all tests/test_save_load_*.py> tests/test_save_custom_name.py -q
pytest tests/test_backend_phase2_architecture.py tests/test_backend_phase3_architecture.py tests/test_backend_phase4_architecture.py -q
git diff --check
```

结果：

1. public API / websocket / settings / init / bootstrap / binding：`160 passed`。
2. save/load 与 save custom name：`62 passed`。
3. backend architecture phase 2/3/4：`20 passed`。
4. `git diff --check` 无 whitespace error，仅 Windows CRLF 提示。

## 5. Phase 2：领域模块拆分与模拟器深化（已完成）

Phase 2 目标是在应用层边界稳定后，减少领域大文件和后续扩展会反复触碰的混合模块。

完成状态：

1. `src/sim/save/sections/load_restore.py` 已只保留 `LOAD_SECTIONS` 与 `restore_loaded_game()` 编排。
2. load 侧新增 `load_run_config.py`、`load_world_core.py`、`load_sect_runtime.py`、`load_avatars.py`、
   `load_region_runtime.py`、`load_membership.py`、`load_events.py`、`load_simulator.py`。
3. `src/sim/avatar_init` 已成为 package，保留 `src.sim.avatar_init` 原导入面和 monkeypatch 兼容。
4. `src.systems.opportunity` 已成为 package，保留原导入面和私有 helper monkeypatch 兼容。
5. `SimulationPhase` 已包含 `handler` callable，`SimulationPhaseRunner` 不再维护手写转发方法。

### 5.1 拆分 load restore sections

dump 侧已有 section，但 load restore 仍集中在 `restore_loaded_game()`。建议把 load 侧拆成与 save 对称的 section。

建议文件：

1. `src/sim/save/sections/meta.py`
2. `src/sim/save/sections/run_config.py`
3. `src/sim/save/sections/custom_content.py`
4. `src/sim/save/sections/world_core.py`
5. `src/sim/save/sections/map_state.py`
6. `src/sim/save/sections/sect_runtime.py`
7. `src/sim/save/sections/avatar.py`
8. `src/sim/save/sections/relations.py`
9. `src/sim/save/sections/region_runtime.py`
10. `src/sim/save/sections/events.py`
11. `src/sim/save/sections/simulator.py`

要求：

1. registry 只声明顺序和执行。
2. 需要跨 section 共享的中间状态放在 `LoadContext`。
3. 旧存档兼容仍遵守开发阶段规则：零代价 `.get` 可做，不为旧结构引入复杂双轨。

验收点：

1. `load_restore.py` 不再包含大段领域恢复逻辑。
2. 新增世界子系统时能新增 section，不需要改一个巨型恢复函数。
3. `tests/test_save_load_*.py` 全绿。

### 5.2 拆分 `src/sim/avatar_init.py`

`avatar_init.py` 当前混合了人口规划、随机约束、装备分配、角色工厂、关系应用、宗门职位、请求解析。
这些职责已经自然形成边界，适合模块化。

建议目录：

1. `src/sim/avatar_init/__init__.py`
2. `src/sim/avatar_init/planning.py`
3. `src/sim/avatar_init/equipment.py`
4. `src/sim/avatar_init/relations.py`
5. `src/sim/avatar_init/sect_assignment.py`
6. `src/sim/avatar_init/factory.py`
7. `src/sim/avatar_init/request_parser.py`

迁移策略：

1. 先移动纯 helper 与 class，不改行为。
2. 保持 `make_avatars()` 与 `create_avatar_from_request()` 对外导出不变。
3. 每次迁移一个职责边界，避免同时改初始化语义。

验收点：

1. 外部调用仍可从 `src.sim.avatar_init` 导入 `make_avatars` 与 `create_avatar_from_request`。
2. 角色创建、觉醒、种族、关系、宗门分配相关测试通过。
3. 原单文件不再承载多个大型职责。

### 5.3 拆分 `src/systems/opportunity.py`

`opportunity.py` 当前混合模型、manager、目标选择、记录生成、奖励/惩罚结算、事件生成、phase 入口和 prompt context。
机会系统后续很可能继续扩展，建议提前拆分。

建议目录：

1. `src/systems/opportunity/__init__.py`
2. `src/systems/opportunity/models.py`
3. `src/systems/opportunity/manager.py`
4. `src/systems/opportunity/targeting.py`
5. `src/systems/opportunity/outcomes.py`
6. `src/systems/opportunity/events.py`
7. `src/systems/opportunity/phases.py`
8. `src/systems/opportunity/context.py`

迁移策略：

1. 先移动 `OpportunityRecord`、`OpportunityManager` 等模型和状态管理。
2. 再移动 targeting 与 outcome 逻辑。
3. 最后移动 phase 入口，并在 `__init__.py` re-export 当前外部依赖的函数名。

验收点：

1. 现有机会系统测试全绿。
2. 外部调用 `phase_generate_opportunities`、`phase_check_opportunities`、`serialize_opportunities`、
   `load_opportunities`、`get_opportunity_context_text` 不需要大规模改动。
3. 新增 opportunity outcome 时不需要修改一个 600 行以上的混合文件。

### 5.4 进一步深化 simulator phase registry

当前 `SimulationPhaseRunner` 已经消费 `phase_registry.py`，但 runner 仍维护一份 handler 字典和转发方法。
如果后续 phase 继续增长，可以让 registry 绑定更完整的 handler metadata。

可选方向：

1. `SimulationPhase` 增加 handler resolver 或 callable。
2. runner 只负责通用编排：创建 context、执行 phase、await、reset check、finalize。
3. phase 处理函数保留在 `phases/*.py`，不要把业务逻辑塞回 runner。

验收点：

1. 新增 phase 只需改 registry 和对应 phase 模块。
2. runner 不再随着 phase 数量增长而持续变长。
3. `tests/test_simulator.py` 与 phase 顺序相关测试通过。

### 5.5 前端只做机会型清理

当前前端主要历史风险已经处理，Phase 2 不建议安排大规模前端重构。

仅在后续改到相关区域时顺手做：

1. 继续压缩大型面板的模板重复，例如调整面板的 option row / custom draft preview 可拆小组件。
2. 保持复杂业务逻辑在 composable 中，展示组件不重新堆状态。
3. 继续遵守懒加载弹窗 watcher `{ immediate: true }` 约束。
4. 大对象、Pixi 实例继续使用 `shallowRef` 或非响应式容器。

## 6. 推荐执行顺序

1. Phase 1.1：测试隔离 fixture。已完成。
2. Phase 1.2：`main.py` context 创建迁移与兼容导出集中。已完成。
3. Phase 1.3：迁移 `GameQueryService`。已完成。
4. Phase 1.4：迁移 `GameCommandService`。已完成。
5. Phase 1.5：收口 static registry 使用。已完成，query/command 主路径通过 `static_data` 访问静态表。
6. Phase 2.1：拆 load restore sections。
7. Phase 2.2：拆 `avatar_init.py`。
8. Phase 2.3：拆 `opportunity.py`。
9. Phase 2.4：按需深化 simulator phase registry。

## 8. Phase 2 验收记录

已运行并通过：

```powershell
pytest tests/test_backend_phase2_architecture.py tests/test_backend_phase3_architecture.py tests/test_backend_phase4_architecture.py -q
pytest <all tests/test_save_load_*.py> tests/test_save_custom_name.py -q
pytest tests/test_avatar_init.py tests/test_avatar_init_race.py tests/test_avatar_init_relation.py tests/test_api_avatar_detail.py tests/test_sect_ranks.py tests/test_yao_world_info_persona.py tests/test_opportunity_system.py tests/test_simulator.py -q
```

结果：

1. backend architecture phase 2/3/4：`23 passed`。
2. save/load 与 save custom name：`62 passed`。
3. avatar init / opportunity / simulator 相关测试：`62 passed, 1 skipped`。

## 7. 完成定义

本轮重构完成后，应满足：

1. `src/server/main.py` 是启动入口，不是 query/command 注册中心。
2. public API 新增 query/command 时，有明确 service/use-case 归属。
3. save/load 新增子系统时，通过 section 扩展，而不是继续膨胀 restore 大函数。
4. 角色初始化与机会系统的核心职责分模块维护。
5. 前端保持现有分层，不因后端重构引入新的硬编码业务选项或 store 边界回退。
6. 相关测试可同进程稳定合跑，不依赖测试执行顺序。
