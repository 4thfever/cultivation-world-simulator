# Issue #195：开发模式 ready 后前端停在进入游戏阶段

本文档记录 2026-05 针对 issue #195 的现象分析、LLM 关系判断与后续修复方案。

## 1. 用户现象

用户反馈：

1. 开发模式启动。
2. 点击进入游戏后界面不再推进。
3. F12 Network 中一直看到 `runtime/status` 轮询。
4. `runtime/status` 返回：

```json
{
  "ok": true,
  "data": {
    "status": "ready",
    "phase": 6,
    "phase_name": "generating_initial_events",
    "progress": 100,
    "error": null,
    "llm_check_failed": false,
    "llm_error_message": "",
    "is_paused": false
  }
}
```

关键判断：这不是“后端初始化还没结束”的典型状态。`status=ready` 与 `progress=100` 表明服务端已经认为世界初始化完成。

## 2. 当前初始化链路

服务端初始化顺序在 `src/server/init_flow.py`：

1. phase 0：扫描资源。
2. phase 1：加载地图。
3. phase 2：生成世界背景。
4. phase 3：初始化宗门。
5. phase 4：生成角色。
6. phase 5：检查 LLM。
7. phase 6：生成初始事件。
8. `runtime.finish_initialization()` 将 `init_status` 置为 `ready`，并将进度置为 100。

前端初始化顺序在 `web/src/composables/useGameInit.ts`：

1. 每秒轮询 `/api/v1/query/runtime/status`。
2. 在若干 phase 提前预加载地图、角色和纹理。
3. 当状态从非 `ready` 变为 `ready`，且 `isInitialized=false` 时，执行 `initializeGame()`。
4. `initializeGame()` 会连接 Socket、加载世界快照、地图、基础纹理、事件和宗门领地。
5. 只有 `systemStore.setInitialized(true)` 后，`useAppShell` 才会从 `initializing` 切到 `game`。

因此本问题的高概率位置不是服务端开局任务，而是前端 ready 后的二段初始化。

## 3. 可疑点

### 3.1 phase_name 残留造成误判

服务端 `finish_initialization()` 当前只保证 `status=ready` 和 `progress=100`，不会强制把 `phase_name` 清理成 `complete`。

所以 `status=ready` 同时 `phase_name=generating_initial_events` 是可解释的残留状态，不应单独判定为后端卡死。

改进方向：

1. ready 后将 `phase_name` 设为 `complete`。
2. 前端展示和逻辑只以 `status` 作为完成判断，不能让 phase 文案误导。

### 3.2 ready 跃迁只触发一次

`useGameInit.ts` 当前只在以下条件成立时执行 `initializeGame()`：

```ts
prevStatus !== 'ready' && res.status === 'ready' && !isInitialized.value
```

这会导致几个边界问题：

1. 如果 ready 那一次执行了 `initializeGame()`，但内部某个请求失败、挂起或被浏览器取消，后续轮询仍是 ready，却不会再次重试。
2. 如果前端首次看到的状态已经是 ready，但前端内部状态没有正确进入 initialized，也可能错过可恢复机会。
3. 用户只看 Network 会看到 `runtime/status` 正常轮询，但页面一直停留在初始化壳层。

改进方向：

1. 将触发条件改成 `res.status === 'ready' && !isInitialized.value && !isInitializingFrontend.value`。
2. 新增前端初始化 guard，避免并发重复初始化。
3. 初始化失败时释放 guard，并记录清晰错误上下文。
4. 对 ready 后前端初始化增加可重试策略。

### 3.3 前端初始化内部吞错

`worldStore.initialize()` 当前 catch 后只记录错误，不向上抛出。调用方无法知道世界是否真的初始化成功。

风险：

1. `world/state`、地图、事件、宗门领地或资源请求失败时，调用方可能继续执行。
2. 错误可能只出现在 console，而页面没有明确错误态。
3. 如果某个 fetch 一直 pending，由于 HTTP client 没有超时，`initializeGame()` 会长期不返回。

改进方向：

1. `worldStore.initialize()` 失败后返回明确结果或重新抛出。
2. `initializeGame()` 在设置 `isInitialized=true` 前校验 `worldStore.isLoaded`。
3. HTTP client 增加可配置超时，避免初始化请求无限 pending。
4. loading overlay 在 ready 但前端初始化超过阈值时显示“正在加载世界数据/资源”，并提供可诊断错误信息。

## 4. LLM 关系判断

从用户给出的返回看，本问题大概率不是 LLM 配置或 LLM 调用失败导致。

原因：

1. LLM 检查发生在 phase 5：`checking_llm`。
2. 即使 LLM 连通性检查失败，服务端也只是设置：
   - `llm_check_failed=true`
   - `llm_error_message=<错误信息>`
   然后继续进入 phase 6。
3. 用户返回里 `llm_check_failed=false` 且 `llm_error_message=""`，表示服务端认为 LLM 检查通过。
4. 用户返回里已经是 `status=ready` 和 `progress=100`，说明服务端已经越过 LLM 检查和初始事件生成阶段。

LLM 仍可能造成的影响：

1. 如果 LLM 响应很慢，可能拖慢 phase 5 或 phase 6 的耗时。
2. phase 6 会执行一次 `sim.step()` 生成初始事件，某些动作、小故事或系统可能间接触发 LLM。
3. 但只要最终已经返回 `ready`，LLM 就不再是“进不了游戏”的直接阻塞点。

后续排查 LLM 的证据标准：

1. 如果状态长期停在 `checking_llm` 或 `generating_initial_events` 且 `status=in_progress`，才优先怀疑 LLM 或初始事件生成。
2. 如果状态是 `ready`，优先排查前端 ready 后的世界快照、地图、事件、宗门领地、纹理资源和 Socket 初始化。
3. 如果 `llm_check_failed=true`，这是配置提醒路径，不应导致 ready 后前端卡死。

## 5. 建议让用户补充的排查信息

请 issue 作者在 F12 中补充：

1. Console 是否有红色错误。
2. Network 中除 `runtime/status` 外，以下请求是否 pending、失败或 404：
   - `/api/v1/query/world/state`
   - `/api/v1/query/map`
   - `/api/v1/query/events`
   - `/api/v1/query/sects/territories`
   - `/api/v1/query/avatars/meta`
   - `tiles/*.png`
   - `males/*.png`
   - `females/*.png`
3. 当前页面是否仍显示 loading overlay，还是黑屏/空壳层。
4. 是否使用了非根路径、代理、Electron dev、反向代理或自定义 `VITE_API_TARGET`。

## 6. 修复计划

### 6.1 服务端状态语义收口

1. 初始化完成时将 `phase_name` 设为 `complete`。
2. 保持 `status=ready` 作为唯一完成语义。
3. 增加测试覆盖：ready 状态不再保留 `generating_initial_events` 作为当前阶段名。

### 6.2 前端 ready 后初始化可恢复

1. 在 `useGameInit` 中新增 `isInitializingFrontend`。
2. 当 `res.status === 'ready' && !isInitialized.value` 时尝试初始化。
3. 初始化中不重复启动第二次初始化。
4. 初始化失败后记录错误、释放 guard，并允许下次轮询重试。
5. 初始化成功后再设置 `isInitialized=true`。

### 6.3 世界初始化错误显性化

1. `worldStore.initialize()` 不再静默吞掉致命初始化错误。
2. 初始化调用方根据错误设置前端初始化错误态。
3. loading overlay 在 ready 但前端初始化失败时显示可读错误，而不是无限转圈或空壳。

### 6.4 HTTP 超时与诊断

1. `httpClient` 支持默认超时。
2. 初始化关键请求可给出更明确的错误标签。
3. Console 日志需要能区分：
   - status 轮询失败
   - 世界快照失败
   - 地图失败
   - 事件分页失败
   - 宗门领地失败
   - 纹理资源失败

## 7. 验证策略

前端测试：

1. 首次轮询直接返回 ready 时，应执行 `initializeGame()`。
2. ready 后前端初始化失败时，下次轮询应能重试。
3. 初始化进行中时，连续 ready 轮询不应并发调用 `initializeGame()`。
4. 初始化成功后不再重复初始化。
5. `worldStore.initialize()` 失败时不应设置 `isInitialized=true`。

后端测试：

1. 初始化完成后 `status=ready`、`progress=100`。
2. 初始化完成后 `phase_name=complete` 或等价完成态。
3. LLM 检查失败时仍可进入 ready，但 `llm_check_failed=true` 保留。

手工验证：

1. `cd web && npm run test`。
2. `pytest tests/test_init_status_api.py tests/test_game_init_integration.py`。
3. 开发模式启动，正常新开局进入游戏。
4. 人为让 `world/state` 返回失败，确认页面不会永久无诊断卡住。

