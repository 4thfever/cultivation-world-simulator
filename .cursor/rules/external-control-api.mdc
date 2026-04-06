---
description: 外接控制 API 基础架构与对外契约规范
globs:
  - src/server/**/*.py
  - web/src/api/**/*.ts
  - web/src/stores/**/*.ts
  - tests/test_api_*.py
  - tests/test_websocket_handlers.py
  - tests/test_init_status_api.py
  - tests/test_game_init_integration.py
  - docs/specs/external-control-api.md
  - README.md
---

# 外接控制 API 规范 (External Control API)

本规范约束“面向外部 agent / Claw / 自动化脚本”的 API 设计与重构方向。目标不是继续堆前端私有接口，而是建立稳定、可扩展、可文档化的外部控制底盘。

## 1. 总体目标

- 本次方向允许**不向前兼容**旧接口命名与旧响应格式，优先保证新结构清晰。
- 以后新增 API 应只是新增 query/command，而不是继续把逻辑堆进 `src/server/main.py`。
- 对外 API 必须优先服务于“外部集成”场景，而不只是当前前端页面调用。

## 2. 分层约束

### 2.1 Runtime / Session 层

- 运行时状态应统一收敛到 runtime/session 抽象中，避免路由直接读写全局 `game_instance`。
- Runtime 应统一管理：
  - `world`
  - `sim`
  - `run_config`
  - `init_status`
  - `is_paused`
  - LLM 检查状态
- 生命周期操作（`start/reinit/reset/pause/resume/load/save`）优先通过 runtime + service 组合实现。

### 2.2 Service 层

- 新 API 的业务逻辑应优先落在 `src/server/services/*.py` 或后续新增的 runtime/service 模块中。
- 路由层负责参数校验、调用 service、返回 DTO；**禁止**在 endpoint 中直接展开复杂业务。
- 可复用的角色控制逻辑、世界控制逻辑、生命周期逻辑要收敛进对应 service，而不是散在多个 endpoint。
- service / handler / query builder 若依赖可被测试 patch、运行时 reload、或未来会继续拆分的函数与配置，优先注入 `get_*` getter 或在调用时动态读取；不要在模块初始化时把 `load_game`、`generate_*_draft`、`apply_runtime_content_locale`、`CONFIG.paths.saves` 这类依赖绑死。

### 2.3 路由层

- 外部稳定 API 应优先挂在新命名空间下，例如 `/api/v1/query/*` 与 `/api/v1/command/*`。
- 旧 `/api/state`、`/api/map`、`/api/detail`、`/api/init-status` 兼容层已移除；新语义禁止再挂旧命名空间。

## 3. Query / Command 边界

### 3.1 Query

- Query 只读、无副作用。
- Query 适合被外部 agent 高频调用。
- 典型 Query：
  - 世界快照
  - 地图
  - 详情
  - 事件分页
  - 榜单
  - 宗门关系
  - 当前运行配置

### 3.2 Command

- Command 有副作用，必须经过统一守卫与统一串行化入口。
- 不要设计“万能 patch 任意字段”的写接口；优先设计**有语义的命令**。
- 典型 Command：
  - 开始游戏
  - 暂停 / 恢复 / 重置 / 重新初始化
  - 设置长期目标
  - 设置天地灵机
  - 创建 / 删除角色
  - 调整角色装备、特质、头像等

## 4. 并发与串行化

- 所有 mutation 必须通过统一入口执行，避免与 `Simulator.step()` 并发修改 world。
- 推荐使用 runtime 内部的 `asyncio.Lock` 或等价串行化机制。
- 如果新增 Command，没有接入统一 mutation 锁，则视为架构违规。

## 4.1 动态依赖与配置读取

- 影响运行时语义的配置应按“调用时读取当前配置”处理，尤其是：
  - 存档目录
  - 数据根
  - settings/secrets 衍生配置
- 若代码路径既可能被 `main.CONFIG` patch，也可能被 `src.utils.config.CONFIG` reload 后的新对象影响，不要假设仓库里只有一个永远稳定的 `CONFIG` 引用。
- 涉及存档文件定位时，优先通过统一 helper 解析目标路径，必要时允许兼容多个候选 saves dir，而不是把目录拼接散落在多个 command/query 中。
- 这条规则的目的不是为了旧接口兼容，而是为了让外接 API 重构后的底盘在测试、Docker、数据根切换、后续继续拆模块时仍然稳。

## 5. 响应与错误契约

- 对外稳定 API 必须统一成功/失败响应格式。
- 不再新增 `200 + {"error": ...}` 风格的公共 API。
- 错误响应应包含稳定的 `error.code`，方便外部 skill 和脚本分支处理。
- 前端 `web/src/api/http.ts` 与对应 DTO/mapper 需要跟随统一契约调整，避免继续依赖零散 `detail` 文本。

## 6. DTO 与前端使用方式

- 外部稳定 API 返回结构必须有明确 DTO；不要让前端或第三方直接依赖“偶然长成”的 JSON。
- 前端消费新接口时，必须先更新 `web/src/types/api.ts`，再更新 `api/modules` 与 `api/mappers`。
- 如果前端仍然使用旧接口，新增功能优先接入新命名空间，不要继续扩大旧接口覆盖面。

## 7. 文档与 README

- 新增或调整外接控制 API 时，必须同步维护：
  - `docs/specs/external-control-api.md`
  - `README.md`
  - 相关测试
- README 需要明确说明项目支持外部 agent / Claw 接入游玩与观测。

## 8. 测试要求

- Runtime 重构必须补生命周期与串行化测试。
- Query API 必须补契约测试。
- Command API 必须补 happy path、状态守卫、错误码测试。
- 涉及初始化、读档、游戏循环的改动，要跑回归测试，避免把外接控制 API 建在不稳定基础上。

## 9. Vibe Coding 检查清单

1. 这是 Query 还是 Command？
2. 是否应该落在 service，而不是继续写进 `main.py`？
3. 是否复用了统一 runtime，而不是直接操作 `game_instance`？
4. 如果是 Command，是否走了统一 mutation 锁？
5. 返回结构是否是稳定 DTO，而不是随手拼的 dict？
6. 是否同步补了测试、文档和 README？
7. 是否把会被 patch / reload 的依赖提前绑定死了？
8. 是否在调用时读取了当前配置与存档目录，而不是假设某个全局 `CONFIG` 永远最新？
