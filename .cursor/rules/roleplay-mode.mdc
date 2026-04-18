---
description: 角色扮演模式（默认上帝视角下的单角色接管）实现与重构规范
globs:
  - src/server/**/*.py
  - src/systems/single_choice/**/*.py
  - src/classes/mutual_action/**/*.py
  - src/sim/**/*.py
  - web/src/components/game/**/*.vue
  - web/src/stores/roleplay.ts
  - web/src/api/modules/avatar.ts
  - web/src/types/api.ts
  - tests/test_public_api_v1.py
  - tests/test_single_choice.py
  - tests/test_action_social.py
  - tests/test_mutual_actions.py
  - web/src/__tests__/components/game/**/*.test.ts
  - docs/specs/avatar-roleplay-mode.md
  - docs/specs/single-choice-unified-framework.md
---

# 角色扮演模式规范 (Roleplay Mode)

本规范约束“默认上帝视角 + 可接管单个角色扮演”的整体设计与后续重构方向，覆盖一期文本决策、二期有限选择、三期自由对话。

## 1. 总体定位

- 不单独新建“个人模式”和“上帝模式”两套全局模式；默认始终是上帝视角。
- 扮演模式的本质是：玩家在上帝视角下，临时接管一个角色的决策来源。
- 同一时刻最多只能扮演一个角色。
- 玩家扮演时仍保留完整世界信息，不做视野收窄或信息降级。

## 2. 核心运行时语义

### 2.1 决策边界暂停

- 玩家不能打断已执行到一半的动作链。
- 只允许在“当前动作为空 + planned actions 为空，需要新决策”的边界暂停。
- 扮演角色若仍有动作链在执行，世界继续运行，roleplay session 应处于 `observing` 而非阻塞态。

### 2.2 扮演态是纯 runtime 状态

- `RoleplaySession`、`pending_request`、`conversation_session`、choice continuation 都不进入 world，不进入 save。
- `load / reinit / reset / start new game` 后必须显式清空扮演态与 pending continuation。
- 前端 roleplay store 也必须在这些生命周期点显式 reset，不要只靠被动重新拉 session 收敛。

### 2.3 暂停语义要细分

- 不要再只靠单个 `is_paused` 布尔值表达所有暂停原因。
- roleplay 至少需要能区分：
  - `roleplay_waiting_decision`
  - `roleplay_waiting_choice`
  - `roleplay_conversation`
- 对外 query / runtime status 应能暴露当前主要暂停原因。

## 3. 一期：文本决策接管

- 一期的 request 类型是 `decision`。
- 玩家输入的是意图文本，不是内部 action DSL。
- 后端应复用现有 AI 决策 prompt 与动作合法性校验；若玩家要求前往未知地点，应优先转为探索而非报错。
- 无效输入不应让世界恢复运行；应保持暂停并允许继续输入。

## 4. 二期：通用有限决策框架

- 二期不要按业务场景一个个硬接按钮；优先把 `single_choice` 重构成统一有限决策框架。
- 业务层只负责：
  - `build_request()`
  - `apply_decision(...)`
- 业务层不负责判断“当前是否玩家扮演”。

### 4.1 决策来源统一抽象

- 二期的统一决策来源至少包含：
  - `llm`
  - `player_roleplay`
  - `fallback`
- 推荐通过统一入口 `resolve_choice(...)` 或等价 resolver 完成来源分发。

### 4.2 continuation / resume

- 二期最大的技术难点是“暂停后恢复原业务流程”，不是按钮本身。
- roleplay choice 必须有统一 continuation 机制；禁止每个场景各写一套挂起/恢复逻辑。
- 同一时刻只允许一个活跃中的 roleplay continuation；若已有 pending request，不允许新 request 覆盖旧 request。

### 4.3 迁移策略

- 优先迁移 `item_exchange`、`sect_recruitment`、mutual action 的 `RESPONSE_ACTIONS`。
- mutual action 的有限响应应先包装成统一 choice request，再交给 resolver；不要在每个动作子类里散落 roleplay 分支。

## 5. 三期：自由对话

- 三期对话必须依附现有 `Conversation` 动作触发，不新增脱离动作语义的自由聊天入口。
- 对话采用“玩家控制扮演角色发一句，对方由 LLM 回一句”的单边接管模式。
- 结束权以玩家为准，LLM 不能主动结束会话。
- 原始聊天记录只保存在 runtime `conversation_session`，不进存档，不直接进入长期事件流。

### 5.1 summary 落地

- 对话结束后必须经过 summary 服务压缩。
- 长期结果至少包括：
  - 摘要事件
  - 可选 relation hint
  - 可选 story hint
- 不要把逐轮原始 chat message 直接写进正式事件存储。

## 6. API / 前端约束

- roleplay 能力应继续走 `/api/v1/query/*` 与 `/api/v1/command/*` 稳定命名空间。
- 所有 mutation 必须串行化，不得绕过统一 mutation 入口直接改 world。
- 前端应以统一 `pending_request.type = decision | choice | conversation` 渲染底部 `RoleplayDock`，而不是为每种模式重新造整页结构。
- `RoleplayDock` 的推荐骨架是：
  - Header
  - Active Request
  - Activity Stream

## 7. 测试要求

- 一期至少覆盖：
  - start / stop / submit-decision
  - 动作链结束时创建 pending request
  - 无效 request_id / avatar_id 的稳定错误
- 二期至少覆盖：
  - non-roleplay 下保持原有 LLM/fallback 行为
  - roleplay 下创建 `choice` request
  - continuation 恢复后调用 `apply_decision(...)`
  - load/reset/reinit 后旧 request 与 continuation 失效
- 三期至少覆盖：
  - `Conversation` 动作进入 roleplay conversation session
  - 多轮 send / reply
  - end 后 summary 入事件
  - relation/story hint 接入后续结算
- 前端至少覆盖：
  - `RoleplayPanel`
  - `RoleplayDock`
  - 拆出的 roleplay 子组件

## 8. 文档锚点

- 总体方案与分期：`docs/specs/avatar-roleplay-mode.md`
- 二期通用 choice 技术底盘：`docs/specs/single-choice-unified-framework.md`
