---
name: external-control-api
description: 规划或实现面向外部 agent / Claw 的稳定控制 API，优先做底层分层、query/command 收口、runtime 串行化与契约文档，而不是零散补接口
---

## 适用场景

当任务涉及以下任一方向时使用本技能：

- 设计或重构外接控制 API
- 让项目更适合被 Claw / agent / 自动化脚本调用
- 把现有前端私有接口收口为稳定公共契约
- 规划 query / command 分层
- 规划 runtime/session 抽象与 mutation 串行化

## 目标

本技能的目标不是“快补几个 endpoint”，而是确保 API 方向具备长期可演进性：

1. 明确 Query 与 Command 边界
2. 明确 Runtime / Service / API 三层职责
3. 建立统一的 mutation 串行化模型
4. 形成稳定 DTO、错误码和文档

## 首先检查什么

1. 当前能力是不是其实已经存在，只是散落在旧接口里？
2. 这次任务是“补接口”，还是“给之后打基础”？
3. 是否涉及 `src/server/main.py` 中直接读写 `game_instance` 的路径？
4. 是否会与 `game_loop()` / `sim.step()` 产生并发写 world 风险？
5. 前端当前是否依赖旧 JSON 结构？如果重构会影响哪些 store / mapper？

## 推荐工作流

### 1. 先梳理现状

优先查看：

- `src/server/main.py`
- `src/server/services/*.py`
- `src/sim/simulator_engine/simulator.py`
- `web/src/api/**/*.ts`
- `web/src/types/api.ts`
- `docs/specs/external-control-api.md`
- `.cursor/rules/external-control-api.mdc`

目标：

- 列出现有 Query API
- 列出现有 Command API
- 标出哪些接口是“前端私有历史接口”
- 标出哪些逻辑应该抽到 service/runtime

### 2. 再定边界

在改代码前先明确：

- 新接口命名空间是什么
- 哪些属于 Query，哪些属于 Command
- 哪些旧接口这次可以直接替换，不做兼容
- 哪些字段要进入稳定 DTO

### 3. 先做底盘，再做接口

如果任务范围足够大，优先顺序应是：

1. runtime/session 抽象
2. mutation 锁 / 串行化
3. service 收口
4. public v1 query
5. public v1 command
6. 前端适配
7. 文档与 README

不要反过来先加一堆 endpoint，再回头补底盘。

### 4. 保持“有语义的命令”设计

优先：

- `set_long_term_objective`
- `set_world_phenomenon`
- `create_avatar`
- `delete_avatar`
- `update_avatar_adjustment`

避免直接引入：

- 任意对象通用 patch
- 任意字段透传写入
- 没有明确副作用边界的“万能控制接口”

## 代码改动建议

### 路由层

- 路由层只做参数解析与响应包装
- 不在路由中直接写复杂 world 逻辑

### Service 层

- 把角色控制、世界控制、生命周期控制分开
- 复用已有 service，不要重复实现
- 对未来可能被测试 patch、运行时 reload 或继续拆模块的依赖，优先注入 getter，例如：
  - `get_load_game`
  - `get_generate_custom_content_draft`
  - `get_generate_custom_goldfinger_draft`
  - `get_apply_runtime_content_locale`
  - `get_config`

### Runtime 层

- 任何会修改 world/sim 的操作都优先接入统一 runtime
- 如果新增的 command 绕过 runtime，通常说明设计有问题

### 配置与存档目录

- 配置真源可能在测试中被 reload 或被 patch；不要默认某个模块级 `CONFIG` 一直是最新对象。
- 读写存档时优先在调用时解析当前 saves dir；如果是基础设施层 helper，可以考虑同时兼容 `main.CONFIG` 与当前配置模块中的最新 `CONFIG`，避免全量测试或数据根切换时读错目录。
- 这类动态读取主要是为了“底盘稳”，不是为了保留旧 public API。

## 文档要求

改动外接控制 API 时，优先同步：

- `docs/specs/external-control-api.md`
- `README.md`
- `AGENTS.md`

如果引入新规则或新的长期约束，记得同步 `.cursor/rules/*.mdc` 和仓库根 `AGENTS.md`。

## 测试建议

至少考虑：

- query 契约测试
- command 契约测试
- 状态守卫测试
- runtime 串行化测试
- 初始化/读档/事件查询的回归测试

若涉及前端同步迁移，还应运行：

```bash
pytest
cd web && npm run test
cd web && npm run type-check
```

## Claw 最小模板

如果目标是尽快做出一个可用的 Claw / agent 控制 skill，优先按下面套路实现：

1. 每轮先查 `GET /api/v1/query/runtime/status`
2. 若未 ready：
   - 未开局就调用 `POST /api/v1/command/game/start`
   - 初始化中就继续轮询
   - 错误态就读取错误信息并考虑 `reinit`
3. ready 后再查：
   - `GET /api/v1/query/world/state`
   - `GET /api/v1/query/events`
   - 必要时 `GET /api/v1/query/detail`
4. 只调用“有语义的 command”，例如：
   - `avatar/set-long-term-objective`
   - `world/set-phenomenon`
   - `avatar/create`
   - `avatar/update-adjustment`
5. command 之后重新 query，不要假设本地缓存一定正确

## 新增接口时怎么落

- 新 query：
  - 先看是否已有 service 可复用
  - 再接到 `src/server/public_query_builders.py`
  - 最后挂到 `src/server/api/public_v1/query.py`
- 新 command：
  - 业务逻辑优先落 service
  - 编排接到 `src/server/command_handlers.py`
  - 最后挂到 `src/server/api/public_v1/command.py`
- 会修改 world / sim 的接口：
  - 必须经过统一 runtime mutation 入口
