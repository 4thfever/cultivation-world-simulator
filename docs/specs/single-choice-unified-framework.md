# `single_choice` 通用有限决策框架重构草案

本文档描述如何将当前仓库中的 `single_choice` 体系重构为一个“统一有限决策框架”，使其既能服务现有 LLM 自动选择，也能服务角色扮演模式下的玩家按钮选择。

本文档是 [avatar-roleplay-mode.md](</e:/projects/cultivation-world-simulator/docs/specs/avatar-roleplay-mode.md>) 的技术拆分文档，重点关注：

- `single_choice` 现状分析
- 通用决策模型设计
- 决策来源抽象
- continuation / resume 机制
- 与 roleplay runtime 的衔接
- 逐步迁移策略

## 1. 背景

当前仓库中的 `single_choice` 已经具备较好的基础抽象：

- `SingleChoiceRequest`
- `SingleChoiceDecision`
- `SingleChoiceScenario`
- `resolve_single_choice(scenario)`

典型调用路径为：

1. 业务场景构造 scenario
2. scenario 生成 request
3. 引擎调用 LLM 得到 decision
4. scenario 应用 decision，返回 outcome

这套结构已经明显优于“每个业务文件内手写一套 LLM prompt + parse + fallback”的旧写法。

但在引入角色扮演模式后，现有结构暴露出一个关键限制：

- 它默认“决策必须立即得到结果”

而玩家扮演下的有限选择并非立即返回，而是：

1. 创建一个 request
2. 挂起当前流程
3. 世界暂停
4. 等待玩家按钮点击
5. 再恢复原流程

也就是说，二期需要解决的问题不是“把选项渲染成按钮”，而是把 `single_choice` 从“同步拿到 decision 的调用风格”升级为“支持挂起与恢复的统一决策框架”。

## 2. 重构目标

本次重构的核心目标：

1. 保留现有 `request / decision / scenario` 基础模型。
2. 将“决策来源”从业务逻辑中抽离。
3. 让同一个 choice 场景可以由：
   - LLM 决策
   - 玩家扮演决策
   - fallback 决策
   统一完成。
4. 引入统一 continuation 机制，支持等待玩家后恢复原流程。
5. 让具体业务场景只负责：
   - 定义场景
   - 构造 request
   - 应用 decision
6. 不让业务场景负责：
   - 是否弹按钮
   - 是否暂停世界
   - 是否走 LLM
   - 如何恢复中断的流程

## 3. 非目标

本次重构明确不追求：

1. 不推翻重写 `single_choice` 的全部数据结构。
2. 不在本轮直接迁移所有现有 choice 场景。
3. 不把自由对话混入该框架。
4. 不做“任意复杂多步树状分支剧情编辑器”。
5. 不让前端直接承载业务逻辑判断。

## 4. 现状分析

## 4.1 当前模型

当前核心模型位于：

- `src/systems/single_choice/models.py`
- `src/systems/single_choice/scenario.py`
- `src/systems/single_choice/engine.py`

现有关键对象：

- `SingleChoiceOption`
- `SingleChoiceRequest`
- `SingleChoiceDecision`
- `SingleChoiceOutcome`
- `SingleChoiceScenario`

当前核心入口：

- `decide_single_choice(request)`
- `resolve_single_choice(scenario)`

## 4.2 当前优点

当前结构已经有几个明显优点：

1. 业务场景和引擎是分离的。
2. `build_request()` 与 `apply_decision()` 天然形成两段式结构。
3. fallback policy 已经被标准化。
4. 各业务场景的 request 内容相对清晰。

## 4.3 当前限制

当前最大限制有三点：

### 限制一：决策来源固定为 LLM/fallback

`resolve_single_choice()` 当前默认：

1. build request
2. call LLM
3. fallback
4. apply

没有把“玩家扮演”视为一类合法来源。

### 限制二：调用语义是“立刻返回”

当前所有调用点都默认：

- `await resolve_xxx(...)` 后立刻得到 outcome

但玩家决策不是立刻返回，而是会跨多个请求周期。

### 限制三：没有 continuation

当前没有统一机制来表示：

- 某个 choice 场景已经创建 request
- 当前流程已经挂起
- 玩家选择后应该恢复到哪里

这意味着如果不重构，业务层就会被迫各自手写挂起逻辑。

## 5. 设计原则

## 5.1 业务层只声明“这里有个有限决策”

业务侧只负责：

- 定义这个选择是什么；
- 给出选项；
- 在最终选定某个 key 后如何落地。

业务侧不负责：

- 由谁做这个选择；
- 什么时候暂停；
- 怎么恢复。

## 5.2 决策来源是框架层概念

“由谁做决策”应是框架层概念，而不是散落在业务层的 `if roleplay ... else ...`。

## 5.3 continuation 是二期核心基础设施

如果没有 continuation，就只能一个个场景硬编码暂停/恢复逻辑。  
那样做最终会破坏 `single_choice` 的抽象边界。

## 5.4 允许渐进迁移

本次重构不能要求所有旧场景一起迁移。  
新框架必须允许：

- 旧逻辑继续运行；
- 新逻辑逐个切换；
- 两种调用方式在过渡期共存。

## 6. 目标架构

建议将重构后的 `single_choice` 抽象为四层：

### A. Scenario 层

职责：

- 描述一个具体有限决策场景；
- 产出 request；
- 应用 decision。

典型接口：

- `build_request()`
- `apply_decision(decision)`

这一层尽量保留现有 `SingleChoiceScenario` 习惯。

### B. Resolver 层

职责：

- 统一决定此次 choice 的决策来源。

候选来源：

- `llm`
- `player_roleplay`
- `fallback`

这一层是新的核心变化。

### C. Continuation 层

职责：

- 当 resolver 决定将本次 choice 交给玩家时，负责：
  - 创建 runtime pending request
  - 注册 continuation
  - 挂起当前流程
  - 在玩家提交后恢复流程

### D. Runtime / Roleplay Integration 层

职责：

- 管理当前活跃的 roleplay session
- 管理当前挂起中的 choice continuation
- 暴露 query / command API

## 7. 建议的数据模型

## 7.1 ChoiceRequest

建议新增统一 request 模型：

```python
@dataclass(slots=True)
class ChoiceRequest:
    request_id: str
    avatar_id: str
    task_name: str
    template_path: Path
    situation: str
    options: list[ChoiceOption]
    fallback_policy: FallbackPolicy
    context: dict[str, Any] = field(default_factory=dict)
    decision_mode: str = "auto"
```

说明：

- 它可以由当前 `SingleChoiceRequest` 平滑演进而来；
- `avatar_id` 与 `request_id` 建议显式化，不只依赖 runtime 包装；
- `decision_mode` 用于标识当前模式，例如：
  - `auto`
  - `llm_only`
  - `roleplay_preferred`
  - `fallback_only`

## 7.2 ChoiceDecision

建议将当前 `SingleChoiceDecision` 保留并扩展来源语义：

```python
class DecisionSource(Enum):
    LLM = "llm"
    PLAYER_ROLEPLAY = "player_roleplay"
    FALLBACK = "fallback"
```

建议字段：

- `selected_key`
- `thinking`
- `source`
- `raw_response`
- `used_fallback`
- `fallback_reason`

## 7.3 ChoiceContinuation

建议新增 continuation 模型：

```python
@dataclass(slots=True)
class ChoiceContinuation:
    continuation_token: str
    request_id: str
    avatar_id: str
    scenario_type: str
    created_at: float
    resume_handler: Callable[[ChoiceDecision], Awaitable[Any] | Any]
```

注意：

- `resume_handler` 不一定要直接存可执行闭包，最终实现可以换成 registry + token；
- 但从设计语义上，必须存在一个“拿到 decision 后恢复原流程”的唯一入口。

## 7.4 Runtime Pending Choice

建议 runtime 中的挂起数据至少包括：

- `request_id`
- `avatar_id`
- `type = choice`
- `title`
- `description`
- `options`
- `continuation_token`

其中：

- 前端只需要 `request_id/type/title/description/options`
- continuation token 可以不直接暴露给前端，但 runtime 需要保留它来恢复流程

## 8. 统一调用链

## 8.1 当前调用链

```text
business scenario
-> build_request
-> decide_single_choice
-> apply_decision
-> outcome
```

## 8.2 目标调用链

```text
business scenario
-> build_request
-> resolve_choice(scenario, runtime)
   -> choice resolver
      -> llm decision
      -> or player roleplay pending request
      -> or fallback
-> apply_decision
-> outcome
```

## 8.3 在玩家模式下的展开

```text
business scenario
-> build_request
-> resolve_choice(scenario, runtime)
   -> detect player-controlled avatar
   -> create pending roleplay choice request
   -> register continuation
   -> pause world
   -> suspend

player submits selected_key
-> submit_roleplay_choice
-> resolve continuation
-> reconstruct ChoiceDecision(source=PLAYER_ROLEPLAY)
-> scenario.apply_decision(decision)
-> continue original flow
```

## 9. 推荐的模块拆分

建议新增或调整如下模块：

- `src/systems/single_choice/models.py`
  - 扩展 request / decision 模型
- `src/systems/single_choice/resolver.py`
  - 新增 `resolve_choice(...)`
- `src/systems/single_choice/continuation.py`
  - 管理 continuation 注册与恢复
- `src/systems/single_choice/engine.py`
  - 保留 LLM/fallback 决策逻辑
- `src/server/services/roleplay_service.py`
  - 与 runtime / API 对接

## 10. Resolver 设计

## 10.1 `resolve_choice(...)`

建议入口：

```python
async def resolve_choice(
    scenario: ChoiceScenario[OutcomeT],
    *,
    runtime,
) -> OutcomeT:
    ...
```

职责：

1. 构建 request
2. 选择决策来源
3. 在必要时挂起并等待恢复
4. 最终统一调用 `scenario.apply_decision(...)`

## 10.2 来源判定规则

建议规则：

1. 若 request avatar 不是当前玩家扮演角色：
   - 走现有 LLM/fallback 流程
2. 若 request avatar 是当前玩家扮演角色，且当前 roleplay session 允许 choice：
   - 创建 player choice request
   - 注册 continuation
   - 挂起
3. 若 roleplay session 不可用或 continuation 注册失败：
   - 回退为明确错误或 fallback，具体由策略控制

## 10.3 Auto Accept 场景

像 `item_exchange.should_auto_accept()` 这种可直接自动接受的场景，不应强行进入 continuation。

建议规则：

- 如果业务场景明确可自动确定结果，则直接构造 `ChoiceDecision` 并 apply；
- 不创建 roleplay request。

## 11. Continuation 设计

## 11.1 为什么必须有 continuation

因为很多业务逻辑在调用 choice 后还会继续执行，比如：

- 生成结果事件
- 追加故事事件
- 更新角色状态

若玩家选择不是即时返回，原调用链就需要“恢复点”。

## 11.2 不建议直接存 Python 闭包到持久层

continuation 是纯运行时对象，不进存档。

建议：

- 只在内存中维护；
- 用 token + registry 管理；
- 在 load/reset/reinit 时统一清空。

## 11.3 两种实现路径

### 路线 A：In-Memory Continuation Registry

形式：

- `continuation_token -> resume handler`

优点：

- 最直观
- 最适合当前阶段快速落地

缺点：

- 生命周期完全依赖进程内存
- 必须严格在 reset/load 时清理

### 路线 B：Scenario Resume Descriptor

形式：

- continuation 只存“场景类型 + 最小必要状态”
- 恢复时重新构建 scenario，再 apply

优点：

- 更可控
- 更少直接依赖闭包

缺点：

- 需要设计每个场景的 resume payload

### 建议

先用路线 B 作为目标方向，允许实现上暂时以 A 过渡。  
原因是：

- 仓库正在做结构收口；
- 长期看，descriptor 比闭包更利于维护和测试。

## 12. 与 roleplay runtime 的对接

## 12.1 Runtime 中需要的最小能力

runtime 应至少支持：

- 保存当前 `RoleplayPromptRequest(type=choice)`
- 保存当前活跃 continuation token
- 查询当前扮演 avatar
- 在玩家提交 choice 后取回 pending request

## 12.2 提交接口的职责

`submit_roleplay_choice` 不应该直接承载业务逻辑。

它只应负责：

1. 校验 request_id
2. 校验 avatar_id
3. 取回 continuation
4. 生成 `ChoiceDecision(source=PLAYER_ROLEPLAY)`
5. 调 continuation 恢复原流程

也就是说：

- API 层不负责“选择 ACCEPT 后到底卖不卖旧武器”
- 这些语义仍属于 scenario.apply_decision()

## 13. 对现有场景的影响

## 13.1 `item_exchange`

这是最适合第一批迁移的场景。

原因：

- 已有清晰的 `ItemExchangeScenario`
- 已有 `should_auto_accept()`
- 业务边界清晰
- 按钮选项稳定

目标迁移方式：

- 让 `resolve_item_exchange()` 内部改用 `resolve_choice(...)`
- 保持 `ItemExchangeScenario` 基本不变

## 13.2 `sect_recruitment`

也是较适合的第二批迁移场景。

原因：

- 选项语义简单
- 没有复杂多层后续逻辑

## 13.3 mutual action 响应

迁移时应优先包装成统一 scenario，而不是在每个 mutual action 子类里直接塞 roleplay 分支。

建议方向：

- 将 `RESPONSE_ACTIONS` 转换为 `ChoiceRequest.options`
- 统一交给 resolver

## 14. 迁移策略

建议分三步迁移：

### 第一步：框架接入但不改旧业务

- 新增 `resolve_choice(...)`
- 新增 continuation registry / descriptor
- 旧 `resolve_single_choice(...)` 暂时保留

### 第二步：迁移一个验证场景

- 先迁移 `item_exchange`
- 跑通 player choice -> continuation -> apply -> outcome

### 第三步：逐步替换旧入口

- `sect_recruitment`
- mutual action 响应
- 其他有限决策场景

## 15. 测试建议

建议新增以下测试：

1. `resolve_choice()` 在非 roleplay 模式下与旧行为一致。
2. roleplay 模式下会创建 pending choice request，而不是立即调用 LLM。
3. continuation 恢复后会调用原 scenario 的 `apply_decision(...)`。
4. `item_exchange` 迁移后自动接受逻辑仍正常。
5. load/reset/reinit 后 continuation registry 被清空。
6. 旧 request_id 提交会返回稳定错误。
7. simultaneous pending choice 不允许覆盖。

## 16. 结论

二期若想避免“每个业务点手写一套玩家按钮逻辑”的碎片化实现，就必须把 `single_choice` 提升为统一有限决策框架。

这次重构的关键不是按钮，也不是前端，而是：

- 决策来源统一抽象
- continuation / resume 机制
- 业务层只负责场景定义和 decision 应用

按这条路线推进，后续的一次性选择、邀约响应、有限对话都会有统一底盘，而不会演变成越来越难维护的分支地狱。
