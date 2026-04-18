# 角色扮演模式（个人模式）设计说明

本文档描述“默认上帝视角 + 可接管单个角色扮演”的完整设计方案，覆盖三期范围。

目标不是额外做一个与上帝模式并列的新模式，而是在现有观察世界、查看信息、控制时间流逝的框架上，引入一个轻量、清晰、可中断于“决策边界”而非“动作执行中途”的玩家扮演能力。

## 1. 背景与目标

当前游戏的主体验是：

- 玩家以上帝视角观察世界。
- 角色默认由 AI 决策并执行动作链。
- 玩家可以通过系统菜单、角色详情、天地异象等接口进行有限干预。

这套结构已经适合“观察”和“轻干预”，但还缺少一种更强的代入方式：

- 玩家可以任选一个角色进行扮演。
- 玩家扮演时仍保留完整世界信息，不降级为传统“迷雾中的第一人称”。
- 玩家可以在关键决策点输入意图，而不是每月被迫逐指令操作。

本设计的核心目标：

1. 默认仍是上帝视角，不再单独切出“个人模式”和“上帝模式”两套全局模式。
2. 玩家可以随时选择一个角色进入扮演态，但同一时间最多只能扮演一个角色。
3. 玩家扮演时，角色在“已有动作链执行期间”不允许被强行打断。
4. 仅在该角色需要新一步决策时，世界自动暂停并无限等待玩家输入。
5. 扮演态是纯运行时状态，不进入存档，不改变现有 save/load 技术形状。
6. 一期先做“文本决策接管”，二期做“一次性选择与邀约响应”，三期做“自由对话”。

## 2. 设计原则

### 2.1 默认仍是上帝视角

本功能的定位是“上帝视角下的局部角色接管”，而不是新的全局游玩模式。

因此：

- 玩家即使进入扮演态，仍可自由查看地图、事件栏、其他角色详情、宗门态势等信息。
- 不收窄信息，不额外引入基于角色感知范围的 UI 限制。
- 不把玩家锁进角色镜头或角色专属页面。

### 2.2 决策边界暂停，而不是动作中途暂停

玩家不能打断一个已经开始执行的动作链条。

允许暂停的唯一标准边界是：

- 当前扮演角色没有正在执行的动作；
- 且没有待提交的 planned actions；
- 因而需要产生下一轮新决策。

这保证：

- 与现有动作链模型一致；
- 不破坏动作内部的多步执行语义；
- 不需要实现“半动作回滚”或“动作中途换脑”。

### 2.3 运行时扮演态不进存档

扮演态是一个 UI/Runtime 层状态，而不是世界状态。

因此：

- 不写入 world；
- 不写入 save 文件；
- 读档、重开、重置、reinit 后自动清空。

### 2.4 复用现有系统，不平行新造一套

本功能优先复用：

- 现有 AI 决策 prompt 与动作链装载机制；
- 现有 `single_choice` 体系；
- 现有 mutual action 响应动作模型；
- 现有事件栏与详情面板；
- 现有 `/api/v1/query/*` 与 `/api/v1/command/*` 稳定接口分层。

不建议额外发明一套“roleplay-only world loop”“roleplay-only event log”“roleplay-only action engine”。

### 2.5 二期优先做“通用有限决策框架”，而不是按场景逐个补按钮

二期若按“某个业务点单独加一套按钮 UI + 接口 + 暂停点”的方式推进，短期看似简单，长期会迅速失控：

- 每个场景都要重复接入暂停、恢复、状态查询、按钮渲染、错误处理；
- 业务层会不断散落“如果是玩家扮演就弹按钮，否则走 LLM”的分支；
- 后续新增一次性选择、邀约响应、有限对话时会重复造轮子。

因此二期的正确目标不是“多加几个按钮场景”，而是：

1. 把现有 `single_choice` 升级为统一的“有限决策框架”。
2. 把“玩家扮演”视为一种新的决策来源，而不是新的业务系统。
3. 让业务层只声明“这里需要一个有限决策”，而不关心这次决策最终来自 LLM、玩家还是 fallback。

## 3. 非目标

本次设计明确不包含以下目标：

1. 不做传统 RPG 式信息遮蔽或战争迷雾。
2. 不做同时扮演多个角色。
3. 不做动作执行中途强制改指令。
4. 不做“万能自然语言控制一切世界对象”的通用代理接口。
5. 不把扮演态写进存档，也不要求读档后恢复到扮演中的上下文。
6. 一期不做完整的自由对话多轮会话。

## 4. 核心体验概览

### 4.1 玩家视角

玩家的常规体验保持不变：

- 世界正常运行；
- 玩家观察地图与事件；
- 玩家点开某个 avatar 的 info panel。

在 avatar info panel 中新增“扮演模式”区域：

- 可进入扮演；
- 可退出扮演；
- 若当前已扮演其他角色，则不可同时接管第二个角色。

进入扮演后：

- 下方出现一个类似命令行的输入区；
- 扮演角色的最近事件列表显示在该区域中；
- 事件列表内容与右侧全局事件栏针对该角色筛选后的结果一致。

### 4.2 运行中的停顿行为

进入扮演后，世界不会立刻无条件暂停。

标准行为应为：

1. 若该角色当前仍有动作链在执行，世界照常推进。
2. 当该角色动作链执行完毕、需要新决策时，系统自动进入“等待玩家输入”状态。
3. 进入该状态后，世界自动暂停，并无限等待玩家提交决策。
4. 玩家提交成功后，系统装载该角色的新动作链并恢复世界运行。

### 4.3 信息展示

扮演态下应同时展示两类信息：

- 全局信息：世界时间、其他角色、地图、全局事件栏、宗门态势；
- 局部信息：当前扮演角色的事件流、当前等待决策的提示、输入框或选项按钮。

### 4.4 退出行为

玩家应可主动退出扮演。

退出后：

- 该角色恢复 AI 接管；
- 后续再次需要决策时，不再等待玩家；
- 若退出时正处于等待玩家输入状态，应在确认后恢复 AI 决策或解除该等待请求。

## 5. 三期范围

## 5.1 一期：文本决策接管

一期只解决“当角色需要新一步动作规划时，由玩家输入文本意图”。

### 一期包含

- 进入/退出扮演态。
- 同时最多扮演一个角色。
- 角色动作链执行完后暂停世界并等待玩家输入。
- 玩家通过文本输入下一步意图。
- 服务端复用现有决策 prompt，将玩家输入转换为动作链。
- 右侧全局事件栏继续工作。
- info panel 中展示该角色的局部事件流。

### 一期不包含

- 一次性选择按钮；
- 邀约接受/拒绝按钮；
- 多轮自由对话；
- 对动作链中途插入新决策；
- 复杂的“可编辑计划队列 UI”。

### 一期 prompt 约束

玩家输入是“意图描述”，不是直接的内部 action DSL。

服务端应在 prompt 中加入以下约束：

- 优先根据玩家意图生成合理动作链；
- 若玩家要求前往角色未知位置，不报错，而是自动转化为“探索/前往可探索方向”的行为；
- 若玩家意图不满足当前条件，应生成最接近且可执行的动作链；
- 仍保留当前 AI 决策 prompt 中的安全约束、世界规则与动作合法性校验。

## 5.2 二期：一次性选择与双人事件邀约

二期处理“本质上不是自由文本规划，而是有限选项决策”的场景。

### 二期包含

- 将现有 `single_choice` 体系升级为统一的“有限决策框架”。
- 将一次性选择场景暴露为按钮选项，而不是文本框。
- 将双人/多人互动中的邀约响应接入同一套决策框架，而不是每个动作各写一套专用按钮逻辑。
- 前端只需渲染统一 `choice` 请求，不要求每个业务点拥有独立 UI。

### 二期来源

优先复用现有机制：

- `single_choice`
- mutual action 的 `RESPONSE_ACTIONS`

二期不是重新设计选择系统，而是把原本由 LLM 或固定逻辑处理的“有限决策位”，改为在“当前扮演角色是决策主体”时转交给玩家。

更准确地说，二期的核心不是“按钮”，而是：

- `single_choice` request 统一建模；
- 决策来源统一解析；
- 玩家选择暂停/恢复统一托管；
- 前端统一渲染 `choice` 型 request。

### 二期限制

- 仍不支持长文本自由对话。
- 仍不支持同一时刻多个扮演角色同时等待不同选择。
- 按钮数应保持克制，优先二选一或有限选项，不做复杂树状对话 UI。
- 二期不追求一口气接完所有现有场景，应先完成通用框架，再逐步把具体业务迁移到统一入口。

## 5.3 三期：自由对话

三期处理“角色作为社交主体，与其他角色发生多轮对话”的复杂场景。

### 三期目标

- 玩家可以在对话上下文中扮演角色进行自由发言。
- 可连续多轮交互，直到玩家主动结束。
- 对话结果最终压缩为抽象叙述事件，而不是把全部原始聊天记录灌入长期事件流。
- 对话必须依附现有 `Conversation` 动作触发，不新增“脱离世界动作语义的自由聊天入口”。
- 对话中只有玩家扮演侧由玩家输入，另一侧仍由 LLM 回复。

### 三期必须新增的能力

- 一个独立的“对话会话态”；
- 对话轮次缓存；
- 对话结束后的 summary 服务；
- 将 summary 结果写入事件系统。

### 三期事件落地规则

不论中间有多少轮聊天，最终进入事件栏的应是：

- 叙述化 summary；
- 相关角色 ID；
- 必要的情绪/关系/后续动作影响。
- 可选的故事扩展事件；

不建议长期保存原始逐轮对话文本到事件存储中，以避免：

- 事件栏刷屏；
- 存储膨胀；
- 后续上下文重复注入成本过高。

## 6. 术语与状态定义

为避免把多种语义都压到单个 `is_paused` 布尔值上，建议引入更细的运行时概念。

### 6.1 扮演会话

建议引入运行时对象：

- `RoleplaySession`

建议字段：

- `controlled_avatar_id: str | None`
- `status: inactive | observing | awaiting_decision | awaiting_choice | conversing | submitting`
- `pending_request: dict | None`
- `started_at: float | None`
- `last_prompt_context: dict | None`
- `conversation_session: dict | None`

语义：

- `inactive`：当前无扮演角色。
- `observing`：已扮演该角色，但暂未阻塞世界等待玩家。
- `awaiting_decision`：一期文本决策等待中。
- `awaiting_choice`：二期选项等待中。
- `conversing`：三期自由对话会话中。
- `submitting`：前端已提交，服务端正在解析或装载结果。

### 6.1.1 三期对话会话态

建议在 `RoleplaySession` 中新增运行时字段：

- `conversation_session`

建议字段：

- `session_id`
- `request_id`
- `avatar_id`
- `target_avatar_id`
- `initiator_avatar_id`
- `status: awaiting_player | generating_reply | awaiting_continue | completed | cancelled`
- `messages`
- `started_at`
- `last_summary`

语义要求：

- 该结构是纯 runtime 状态，不写入 world，不写入 save；
- `messages` 保存本次会话逐轮聊天记录，仅用于本轮对话上下文和结束后的 summary；
- `last_summary` 仅作为本轮结束态的临时缓存，不作为长期事实来源。

### 6.2 暂停原因

建议将“暂停”从单一布尔值提升为“聚合状态 + 原因”。

建议新增：

- `pause_reasons`
- `pause_reason_detail`

候选原因包括：

- `manual_pause`
- `init_pending`
- `auto_control_no_client`
- `roleplay_waiting_decision`
- `roleplay_waiting_choice`
- `roleplay_conversation`

聚合规则：

- 只要存在任一阻塞型 pause reason，`is_paused = true`。
- UI 应展示最关键的当前原因，而不是只显示“已暂停”。

### 6.3 扮演请求

建议统一抽象为：

- `RoleplayPromptRequest`

建议字段：

- `request_id`
- `type: decision | choice | conversation`
- `avatar_id`
- `target_avatar_id`
- `title`
- `description`
- `context`
- `options`
- `messages`
- `can_end`
- `created_at`

其中：

- `decision` 对应一期文本输入；
- `choice` 对应二期按钮选择；
- `conversation` 对应三期会话输入。

三期约束：

- `conversation` 请求必须绑定一个已经进入中的 `Conversation` 动作；
- 不允许前端脱离动作链凭空创建自由聊天会话；
- `messages` 仅用于前端渲染当前会话，不进入正式事件存储。

### 6.4 通用有限决策请求

建议在二期显式引入统一概念：

- `ChoiceRequest`
- `ChoiceDecision`
- `ChoiceResolver`

其中 `ChoiceRequest` 可以直接由现有 `SingleChoiceRequest` 演进而来。

建议字段：

- `request_id`
- `avatar_id`
- `task_name`
- `template_path`
- `situation`
- `options`
- `fallback_policy`
- `context`
- `decision_mode`

语义说明：

- `request_id`：运行时唯一标识；
- `avatar_id`：当前决策主体；
- `task_name/template_path`：兼容当前 LLM 决策链；
- `situation/options/fallback_policy/context`：沿用当前 `single_choice` 模型；
- `decision_mode`：用于标注当前是 `llm`、`roleplay_player`、`fallback_only` 等模式。

### 6.5 决策来源

建议将“决策从哪里来”统一抽象为：

- `DecisionSource`

二期至少包含：

- `llm`
- `player_roleplay`
- `fallback`

关键原则：

- 业务层不直接判断“当前是不是玩家在扮演”；
- 业务层只创建 request，然后交给统一 resolver；
- resolver 再根据当前 runtime/session 决定由谁来完成此次决策。

### 6.6 Continuation / Resume Token

二期最大的技术难点不是按钮渲染，而是“暂停后怎么恢复原业务流程”。

当前很多 `single_choice` 场景是在一段异步结算流程中直接 `await resolve_xxx()`：

1. 构建 request
2. 立即得到 decision
3. 立即 apply
4. 继续后续逻辑

若该 decision 改由玩家提供，中间就会出现跨 tick / 跨请求的等待。  
因此需要引入统一的 continuation 语义。

建议字段：

- `continuation_token`

其职责不是暴露给前端做业务判断，而是：

- 标识这次 choice 对应哪个挂起中的决策 continuation；
- 在玩家提交后恢复到原本等待 decision 的流程；
- 避免业务层自己手写“挂起半个结算流程”的散乱逻辑。

## 7. 一期详细流程

### 7.1 开始扮演

玩家在 avatar info panel 中点击“开始扮演”：

1. 后端检查当前是否已有正在扮演的角色。
2. 若已有且不是当前角色，则拒绝并返回明确错误。
3. 若当前角色有效，则创建/更新 `RoleplaySession`。
4. 若此时角色已有动作链，则 `status = observing`。
5. 若此时角色已处于“无当前动作且无计划”的决策边界，则立刻创建 `pending_request` 并进入等待状态。

### 7.2 世界推进过程中的触发

在模拟器的“补决策”阶段，若检测到某角色满足：

- 是当前被扮演角色；
- 当前动作为空；
- planned actions 为空；

则不走普通 LLM 决策，而是：

1. 创建决策请求；
2. 记录到 runtime 的 roleplay session；
3. 设置对应 pause reason；
4. 结束当前 tick 的后续推进或在下一轮 loop 中停住。

### 7.3 玩家提交文本意图

玩家输入例如：

- 去附近探索机缘
- 找某人交谈，看看能不能结交
- 先调息恢复，再继续突破

后端处理：

1. 校验当前 `pending_request` 仍有效。
2. 校验提交者面向的 avatar 与当前扮演角色一致。
3. 调用“玩家决策转动作链”的服务。
4. 服务复用 AI prompt 与动作合法性校验。
5. 成功后把结果装载到该 avatar 的 planned actions。
6. 清除 `pending_request` 与对应 pause reason。
7. 将会话状态切回 `observing`。

### 7.4 玩家无效输入

无效输入不应直接让世界恢复运行。

应优先：

1. 返回错误或提示信息；
2. 保持世界暂停；
3. 允许玩家继续输入。

如果模型生成了不可执行动作链，则走现有合法性过滤逻辑；若最终无有效动作，应回到等待状态，并给出更明确的失败提示。

## 8. 二期详细流程

二期不建议按“某个场景先临时补一个按钮入口”的方式逐个推进。  
推荐先把 `single_choice` 重构为统一有限决策框架，再逐步迁移已有业务场景。

### 8.1 二期总目标

二期应先完成以下框架目标：

1. 统一 `build request -> resolve -> apply` 流程。
2. 统一有限决策来源：
   - LLM
   - 玩家扮演
   - fallback
3. 统一 runtime 中的 `choice` 挂起态。
4. 统一前端 choice 请求显示和按钮提交流程。
5. 统一 continuation / resume 机制。

### 8.2 `single_choice` 重构方向

当前 `single_choice` 已经具备两个良好基础：

- request 模型清晰；
- scenario 拥有 `build_request()` 与 `apply_decision()` 的天然两段式结构。

建议不要推翻现有结构，而是在其上升级：

#### 当前模型

- `SingleChoiceScenario.build_request()`
- `decide_single_choice(request)`
- `resolve_single_choice(scenario) -> decision -> apply`

#### 目标模型

- `ChoiceScenario.build_request()`
- `resolve_choice(request, runtime, scenario)`
- `ChoiceResolver` 决定：
  - 直接调用 LLM
  - 转交玩家并挂起
  - 使用 fallback
- 在拿到 `ChoiceDecision` 后再统一调用 `scenario.apply_decision(...)`

也就是说，业务层保留“构建 request + 应用 decision”的职责，但不再负责“这次决策从哪来”。

### 8.3 建议的统一入口

建议新增一个统一入口，例如：

- `resolve_choice(scenario, runtime)`

它的行为应为：

1. 调用 `scenario.build_request()`
2. 判断当前 request 的 avatar 是否是玩家扮演对象
3. 若不是玩家扮演对象：
   - 沿用当前 LLM/fallback 流程
4. 若是玩家扮演对象：
   - 创建 `RoleplayPromptRequest(type=choice)`
   - 写入 runtime
   - 进入等待态
   - 通过 continuation token 挂起当前流程
5. 玩家提交后：
   - 恢复该流程
   - 构造统一的 `ChoiceDecision`
   - 调用 `scenario.apply_decision(...)`

### 8.4 一次性选择

当扮演角色遇到一个有限选择场景时：

当扮演角色遇到一个 `single_choice` 场景时：

1. 若该角色未被玩家扮演，则维持现有自动逻辑。
2. 若该角色正被玩家扮演，则由统一 `ChoiceResolver` 接管。
3. Resolver 创建 `RoleplayPromptRequest(type=choice)`。
4. 世界暂停，前端显示统一选项按钮。
5. 玩家点击按钮后，系统恢复该 choice continuation。
6. 恢复后统一调用 `scenario.apply_decision(...)`。

### 8.5 双人邀约响应

当扮演角色是某个 mutual action 的响应方时：

1. 若该动作暴露有限 `RESPONSE_ACTIONS`；
2. 则应优先把这些响应包装成统一的 `ChoiceRequest`；
3. 而不是直接在动作类里硬编码“玩家模式显示哪些按钮”；
4. 玩家选中后，仍通过统一 resolver -> continuation -> apply 流程恢复。

### 8.6 现有场景迁移顺序建议

不建议一次性迁移所有有限选择场景。建议按以下顺序推进：

1. `item_exchange`
   - 炼丹、奇遇、战利品等获得新物品后的“保留还是卖出/替换”
   - 原因：现有 `single_choice` 结构最完整、验证价值最高
2. `sect_recruitment`
   - 语义明确、按钮稳定
3. mutual action 的有限响应
   - `Accept / Reject`
   - `Yield / Reject`
   - `Talk / Reject`

### 8.7 二期与一期的关系

二期不是替代一期，而是新增另一种请求类型：

- 文本决策继续用于开放式意图；
- 选项按钮用于有限响应。

二者共享：

- roleplay session；
- pause reason；
- prompt request；
- 前端强提示容器。

二者在更高层上都属于：

- “统一角色决策请求”

只是：

- 一期是开放式文本决策；
- 二期是有限选项决策。

## 9. 三期详细流程

### 9.1 触发原则

三期对话必须依附现有 `Conversation` 动作触发。

不建议新增“玩家点一个按钮就和任意角色自由聊天”的独立入口。  
原因：

1. `Conversation` 已经是世界中的正式动作语义；
2. 这样可以保持动作链、事件、关系变化、故事系统语义一致；
3. 可以避免“UI 上发生了聊天，但世界里并没有对应动作”的割裂。

因此推荐路径是：

1. 玩家通过一期文本决策或二期有限响应，让角色执行 `Talk` / `Conversation` 相关动作；
2. 当动作链推进到 `Conversation` 时：
   - 若当前不是玩家扮演：沿用现有 AI 对话逻辑；
   - 若当前是玩家扮演：进入三期 `conversation` 型 request；
3. 对话结束后，`Conversation` 动作完成并进入结算。

### 9.2 对话会话启动

当 `Conversation` 动作检测到“当前对话主体是玩家扮演角色”时：

1. 创建 `RoleplayPromptRequest(type=conversation)`；
2. 构建 `conversation_session`；
3. 进入 `conversing` 状态；
4. 世界暂停；
5. 底部 dock 切换为 chat 界面。

### 9.3 多轮聊天

多轮对话期间采用“玩家一侧输入，目标角色由 LLM 回复”的单边接管模式。

这意味着：

- 玩家只控制当前扮演角色的发言；
- 对方角色不由玩家代打，不支持双边手动输入；
- 每次玩家发送一句，系统生成目标角色一句回复；
- 逐轮追加到 runtime `messages`；
- 原始消息不直接写入正式事件系统。

### 9.4 三期 prompt 设计

三期需要单独的 conversation prompt，不建议复用一期开放式动作规划 prompt。

建议 prompt 上下文至少分四段：

1. 双方角色信息
   - 姓名、境界、立场、关系、当前状态、近期目标
2. 历史交互摘要
   - 近期共同事件
   - 关系变化
   - 之前重要往来
3. 本次对话上下文
   - 谁发起
   - 为什么开始
   - 所在地点
   - 当前时间
4. 本轮前文
   - 最近若干轮 message history

建议 LLM 输出固定结构：

- `reply_content`
- `speaker_thinking`
- `conversation_state`
- `summary_hint`
- `relation_hint`

额外约束：

- LLM 不能主动结束会话；
- 会话结束权只属于玩家显式点击“结束对话”；
- 若 LLM 认为话题已尽，可通过 `conversation_state` 或 `summary_hint` 表达“适合收尾”，但不得直接终止。

### 9.5 结束对话

结束权以玩家为准。

允许的结束方式：

- 玩家主动点击“结束对话”；
- 目标角色失效、死亡、离场等导致被迫中断。

不允许：

- LLM 自主判定并结束对话。

结束后：

1. 调用 summary 服务；
2. 生成摘要事件；
3. 可选生成关系变化 hint；
4. 可选生成故事扩展事件；
5. 清空临时对话缓存；
6. 恢复 `observing` 或继续后续动作链。

### 9.6 Summary 设计

三期 summary 服务建议输出三层结果：

1. `conversation_brief_summary`
   - 面向事件栏
   - 一至两句叙述文本
2. `conversation_relation_hint`
   - 面向关系变化计算
   - 可以是结构化 hint
3. `conversation_story_hint`
   - 面向后续小故事扩展
   - 可选

其中：

- 正式事件流至少写入 `conversation_brief_summary`；
- 原始聊天记录不进入长期事件存储；
- summary 本身也不要求进存档，最终长期事实以入库后的事件和关系变化结果为准。

## 10. 后端架构建议

## 10.1 新增 service 模块

建议新增独立 service，而不是把逻辑继续堆回 `src/server/main.py`：

- `src/server/services/roleplay_service.py`
- `src/server/services/roleplay_queries.py`
- `src/server/services/choice_resolver.py`
- `src/server/services/choice_continuation.py`

职责建议：

- 管理 `RoleplaySession` 生命周期；
- 创建、读取、清除 `RoleplayPromptRequest`；
- 执行玩家提交；
- 处理失效 avatar、退出、冲突检测；
- 提供运行时查询 DTO。

其中二期新增职责建议为：

- `choice_resolver.py`
  - 决定某次有限决策由 LLM、玩家还是 fallback 完成
- `choice_continuation.py`
  - 管理被玩家接管时的挂起与恢复

## 10.2 Runtime 层扩展

建议在当前 runtime session 上扩展以下内容：

- roleplay session 状态；
- pause reasons；
- 统一 pause 聚合逻辑。

不要把这些状态分散保存在：

- 前端本地 store 单边假设；
- world 对象；
- 模块级全局变量。

## 10.3 决策注入点

一期的最佳注入点应在“角色需要补决策”的地方，而不是动作执行层内部。

推荐位置：

- 模拟器决策相位；
- 或其上层调用的 service/adapter。

目标是做到：

- 对扮演角色：转为创建 `pending_request`；
- 对非扮演角色：维持现有 `llm_ai.decide(...)`。

### 10.4 二期的有限决策注入点

二期的注入点不应散落在每个业务场景中各写一套 `if roleplay then ...`。

建议统一在：

- `single_choice` 的统一入口 resolver

也就是说：

- 业务只负责 `build_request` 与 `apply_decision`
- resolver 负责判断是否转为玩家 choice request
- continuation 负责恢复原流程

## 10.5 三期 summary 服务

三期建议额外新增：

- `src/server/services/roleplay_conversation_summary.py`
- `src/server/services/roleplay_conversation_service.py`

职责：

- `roleplay_conversation_service.py`
  - 创建 / 读取 / 推进 `conversation_session`
  - 处理玩家发送发言
  - 调用 LLM 生成目标角色回复
  - 在结束时触发 summary
- `roleplay_conversation_summary.py`
  - 接收临时对话轮次
  - 输出叙述型事件文本
  - 控制摘要长度与风格
  - 提供关系 / 故事 hint
  - 不直接耦合 UI 层

## 11. API 设计建议

本功能应遵循现有 public v1 query/command 分层。

## 11.1 Query

建议新增：

### `GET /api/v1/query/roleplay/session`

返回当前扮演会话：

- 当前扮演角色；
- 当前状态；
- 当前 pending request；
- 当前 pause reason；
- 是否允许提交；
- 最近角色事件过滤参数。

### 扩展 `GET /api/v1/query/runtime/status`

建议补充：

- `pause_reason`
- `pause_reason_detail`
- `roleplay_status`
- `roleplay_avatar_id`

这样前端顶部状态栏和强提示层可以直接复用 runtime status，而不是额外拼接多个接口结果。

## 11.2 Command

建议新增：

### `POST /api/v1/command/roleplay/start`

请求：

- `avatar_id`

行为：

- 开始扮演指定角色；
- 若已有其他角色正在扮演，则返回冲突错误。

### `POST /api/v1/command/roleplay/stop`

请求：

- 可为空，或带 `avatar_id` 作一致性校验。

行为：

- 结束当前扮演；
- 清空 pending request；
- 清除 roleplay pause reason。

### `POST /api/v1/command/roleplay/submit-decision`

请求：

- `request_id`
- `avatar_id`
- `command_text`

行为：

- 将玩家文本转为动作链并装载。

### `POST /api/v1/command/roleplay/submit-choice`

二期使用：

- `request_id`
- `avatar_id`
- `selected_key`

说明：

- 该接口不应直接承载业务语义；
- 它只负责把“玩家选择了哪个 key”交回统一 continuation；
- 由 continuation 恢复原流程并调用对应场景的 `apply_decision(...)`。

### `POST /api/v1/command/roleplay/conversation/send`

三期使用：

- `request_id`
- `avatar_id`
- `message`

行为：

- 将玩家本轮发言追加到 `conversation_session`
- 调用 conversation prompt 生成目标角色回复
- 返回最新消息列表或最新增量消息
- 维持世界暂停

### `POST /api/v1/command/roleplay/conversation/end`

三期使用：

- 主动结束对话并触发 summary。

行为：

- 仅允许玩家显式触发；
- 触发 summary；
- 完成 `Conversation` 动作；
- 清空 runtime 对话缓存。

## 11.3 错误码建议

建议显式定义若干稳定错误：

- `ROLEPLAY_ALREADY_ACTIVE`
- `ROLEPLAY_AVATAR_NOT_FOUND`
- `ROLEPLAY_TARGET_MISMATCH`
- `ROLEPLAY_REQUEST_NOT_FOUND`
- `ROLEPLAY_REQUEST_EXPIRED`
- `ROLEPLAY_SUBMIT_NOT_ALLOWED`
- `ROLEPLAY_CONVERSATION_NOT_ACTIVE`

## 12. 前端设计建议

## 12.1 信息面板挂载点

挂载点建议放在 avatar info panel 内，但作为独立子组件，而不是把逻辑全部塞进当前 detail 组件。

建议新增：

- `web/src/components/game/panels/info/components/RoleplayPanel.vue`

主要职责：

- 显示当前是否可进入扮演；
- 显示进入/退出按钮。

三期的主要交互面不再放在 avatar info panel 内，而是继续使用主界面底部 dock。

## 12.2 Store

建议新增：

- `web/src/stores/roleplay.ts`

职责：

- 拉取/缓存当前 roleplay session；
- 负责 start/stop/submit；
- 管理正在提交、错误提示、局部 UI loading；
- 与 runtime status 联动。

## 12.3 事件流展示

不要单独造一套 roleplay event backend。

应复用现有事件接口，通过 `avatar_id` 过滤加载该角色事件流。

实现建议：

- 右侧全局事件栏继续保留；
- RoleplayPanel 内复用同一套事件渲染逻辑；
- 最好提取共享的 `EventTimelineList` 组件，避免维护两套 event item UI。

## 12.4 强提示

当世界因为 roleplay 请求而暂停时，需要明显提示。

建议至少包含：

- 当前是哪个角色正在等待玩家；
- 当前等待类型：文本决策 / 选项选择 / 对话输入；
- “世界已暂停，等待你的操作”；
- 明确的提交入口。

一期二期可用 dock 顶部状态栏承担强提示；三期对话期间则由 chat 头部承担。

### 12.5 三期对话 UI

三期不建议新开弹窗或独立页面，继续复用当前底部 `RoleplayDock`。

建议在 dock 中新增第三种模式：

- `decision`
- `choice`
- `conversation`

其中 `conversation` 模式建议采用 chat 布局：

1. 顶部一行
   - 当前角色
   - 对话对象
   - 当前状态
   - “结束对话”按钮
2. 中部主区
   - 消息流
   - 左右区分说话双方
3. 底部输入区
   - 输入框
   - 发送按钮

界面约束：

- 信息密度优先，不做大面积空白区；
- 顶部工具栏保持紧凑；
- 对话进行中可以同时显示 chat 与事件摘要区，但 chat 是主内容区；
- 会话结束后 dock 恢复普通事件流视图。

## 13. 读档、存档与生命周期

## 13.1 存档

扮演态不写入存档。

原因：

- 它不是世界长期状态；
- 恢复成本高；
- 容易引入“读档后请求上下文已失效”的一致性问题。

## 13.2 读档

每次 load game 后应：

1. 清空 roleplay session；
2. 清空所有 roleplay pause reason；
3. 清空 pending request；
4. 前端收到新运行时状态后重置 roleplay store。

## 13.3 其他生命周期节点

以下操作后也应执行相同清理：

- start game
- reinit game
- reset game

## 14. 边界情况与兜底

至少需要覆盖以下边界情况：

### 14.1 被扮演角色死亡

若扮演角色死亡：

- 自动退出扮演；
- 清空 pending request；
- 广播 toast 或提示。

### 14.2 被扮演角色被删除或不存在

若角色失效：

- roleplay session 自动失效；
- 不允许继续提交旧请求。

### 14.3 玩家提交过慢

本设计允许无限等待，不做超时自动 AI 接管。

但请求对象仍应具备版本或 request_id，以防：

- 玩家页面滞后；
- 重复提交旧请求；
- 读档后旧前端仍在提交。

### 14.4 退出时正处于等待输入

建议行为：

- 弹确认；
- 确认后结束扮演并交还 AI 接管；
- 不保留旧请求。

### 14.5 扮演期间切换查看其他角色

允许。

这是“上帝视角下局部接管”的核心设计要求，不应限制玩家只能看当前角色。

### 14.6 挂起中的 choice 在存档/重置/读档后失效

由于扮演态与 continuation 都不进存档，因此：

- 所有挂起中的 `choice` continuation 在 load/reinit/reset 后都必须失效；
- 前端提交旧 `request_id` 时应收到稳定错误；
- 不允许在读档后尝试恢复旧 continuation。

### 14.7 同一时间仅允许一个挂起中的 roleplay continuation

二期仍维持“最多扮演一个角色”的约束，因此：

- 同一时刻只允许一个活跃中的 roleplay continuation；
- 不支持多个 choice 同时等待；
- 若某流程已在等待 choice，不允许新的 roleplay request 覆盖旧 request。

## 15. 对现有系统的影响

## 15.1 动作系统

影响较小。

原因：

- 现有动作链本就支持“链条执行完后再补新决策”；
- 扮演模式只是在补决策的入口处替换决策来源。

## 15.2 single_choice

二期需要做结构性重构，但不是推翻重写。

建议改造目标：

1. 保留现有 `request / decision / scenario` 思路；
2. 新增统一 resolver；
3. 新增 continuation；
4. 让业务层停止直接关心“决策来自 LLM 还是玩家”。

这是二期最关键的基础设施变更。

## 15.3 mutual action

二期需要把部分 `RESPONSE_ACTIONS` 暴露为玩家选项，但底层响应落地逻辑仍应复用原实现。

## 15.4 事件系统

一期和二期影响较小，只是新增局部展示。

三期会引入：

- 对话 summary 生成；
- summary 写入事件系统；
- 原始对话不上正式事件流。

## 16. 测试建议

## 16.1 后端

建议新增以下测试方向：

1. 进入扮演后，同一时刻不可扮演第二个角色。
2. 扮演角色有动作链时不会立刻暂停。
3. 扮演角色动作链结束时会创建 pending request。
4. pending request 存在时世界暂停且不会继续推进。
5. 提交有效文本后会装载计划并恢复运行。
6. 提交无效 request_id 会返回稳定错误。
7. load/reinit/reset 后 roleplay session 被清空。
8. 角色死亡后自动退出扮演。
9. 二期 choice 提交会复用原有选择应用逻辑。
10. 三期对话结束后只写入 summary 事件。

二期还应新增以下专项测试：

11. `single_choice` 在非 roleplay 模式下仍保持原有 LLM/fallback 行为。
12. `single_choice` 在 roleplay 模式下会创建统一 `choice` request，而不是立即返回 LLM decision。
13. 玩家提交 `selected_key` 后会恢复 continuation，并调用对应场景的 `apply_decision(...)`。
14. continuation 在 load/reset/reinit 后自动失效。

## 16.2 前端

建议新增以下测试方向：

1. AvatarDetail 中正确显示进入/退出扮演按钮。
2. 正在扮演其他角色时，当前面板显示不可接管状态。
3. roleplay session 为等待状态时显示强提示。
4. 文本提交成功后输入框清空并收起等待态。
5. roleplay 局部事件流正确按 avatar_id 加载。
6. load game 后 roleplay store 自动重置。
7. 三期 conversation request 能正确渲染 chat UI。
8. 玩家发送一轮消息后会出现 LLM 回复。
9. 点击结束对话后会关闭 conversation 状态并恢复普通事件流。

## 17. 分期落地建议

建议按以下顺序实施：

### 第一步

先做 runtime 扩展：

- roleplay session
- pause reasons
- runtime status/query 扩展

### 第二步

做一期最小闭环：

- start/stop/submit-decision API
- 决策注入点
- 前端 RoleplayPanel
- 强提示

### 第三步

做二期第一阶段：

- 重构 `single_choice` 统一入口
- 引入 `ChoiceResolver`
- 引入 continuation / resume token
- 前端统一 `choice` request UI

### 第四步

做二期第二阶段：

- 先迁移 `item_exchange`
- 再迁移 `sect_recruitment`
- 最后迁移 mutual action 响应

### 第五步

做三期：

- 以 `Conversation` 动作为唯一触发入口接入玩家对话
- conversation session
- conversation prompt
- conversation summary service
- 对话 UI
- 关系 / 故事 hint 结算

## 18. 结论

“个人模式”最合理的落地方式不是新建一个与上帝模式并列的全局模式，而是：

- 默认始终是上帝视角；
- 允许玩家在上帝视角下接管一个角色；
- 只在决策边界暂停世界等待玩家；
- 一期做文本决策；
- 二期先做通用有限决策框架，再在其上承载选项与邀约响应；
- 三期继续依附 `Conversation` 动作实现玩家自由对话，并以 summary 入事件。

这条路线对现有架构最友好，也最符合当前仓库已经成型的 runtime / public v1 API / 事件系统 / 动作链体系。

## 19. 三期最终拍板结论

本轮需求确认后，三期按以下结论执行：

1. 对话必须依附现有 `Conversation` 动作触发，不新增独立自由聊天入口。
2. 对话采用“玩家说一句，目标角色由 LLM 回一句”的单边接管模式。
3. 结束权以玩家为准，LLM 不能主动结束对话。
4. 原始聊天记录不进存档；对话会话态完全属于 runtime。
5. Summary 可以输出“摘要事件 + 关系 hint + 可选故事扩展”三层结果。
6. 底部 dock 在对话进行中允许同时展示 chat 与事件区域，但应以 chat 为主。

## 20. 三期实现计划

建议按以下顺序落地：

### 20.1 后端 runtime 与协议层

- 扩展 `RoleplaySession` 支持 `conversation_session`
- 扩展 `RoleplayPromptRequest(type=conversation)`
- 扩展 runtime status / query DTO
- 新增 conversation send / end command

### 20.2 动作层接入

- 以 `Conversation` 动作为唯一入口
- 非扮演角色继续走现有自动对话逻辑
- 扮演角色进入 `conversation_session`

### 20.3 LLM 层

- 新增 conversation prompt
- 新增 conversation summary prompt
- 先实现稳定的“玩家一句 -> LLM 一句 -> 玩家决定是否继续”

### 20.4 前端层

- 在 `RoleplayDock` 中新增 `conversation` 模式
- 实现消息流、发送、结束对话
- 对话结束后回切普通事件流

### 20.5 测试层

- 后端会话创建、推进、结束、失效
- summary 入事件
- reset/load/stop 后会话清空
- 前端 dock chat 模式渲染与交互
