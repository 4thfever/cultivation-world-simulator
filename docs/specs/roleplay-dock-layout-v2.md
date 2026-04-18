# 扮演模式界面布局 V2

## 1. 背景

当前扮演模式已经具备：

- 底部 dock 作为统一扮演工作台
- 决策 / 选项 / 对话三种请求类型
- 扮演交互历史流
- 右侧全局事件栏

但目前仍存在一个明显问题：

- 底部右侧和右侧栏都在展示“事件”，语义重复
- 用户在扮演时，需要同时理解“底部事件流”和“右侧事件栏”两套相近面板
- 底部左侧同时承载“当前请求”和“交互历史”，空间竞争较强

因此本次调整目标是进一步统一信息分工。

## 2. 目标

扮演模式下，将界面语义收束为三块：

1. 右侧事件栏：只负责该角色的长期事件流
2. 底部左侧：只负责玩家当前交互
3. 底部右侧：只负责本次扮演过程中的输入 / 输出 / 中间结果

不再在底部右侧重复展示“事件流”。

## 3. 新布局

### 3.1 扮演前

- 右侧事件栏保持当前全局行为
- 底部扮演栏隐藏

### 3.2 扮演后

- 右侧事件栏自动切换为当前扮演 avatar 的事件过滤视图
- 底部扮演栏继续显示
- 底部扮演栏拆成左右两块：
  - 左侧：当前请求区
  - 右侧：扮演交互流

## 4. 三块区域职责

### 4.1 右侧事件栏

职责：

- 展示当前扮演角色的长期事件
- 保持现有高密度事件栏样式
- 不再和底部栏重复

行为：

- 进入扮演时，自动将 filter avatar 设置为当前扮演角色
- 切换扮演角色时，自动切到新的角色
- 退出扮演时，恢复到进入扮演前的事件栏筛选状态

说明：

- 右侧事件栏仍是 event stream，不是 interaction stream
- 不承载玩家输入、动作链、按钮选择、即时对话来回等内容

### 4.2 底部左侧：当前请求区

职责：

- 只展示当前正在等待玩家处理的请求

内容：

- `decision`：文本输入 + 提交
- `choice`：选项按钮
- `conversation`：对话主区 + 输入框 + 结束按钮
- `observing`：空态提示

约束：

- 不再在左侧混放历史交互流
- 左侧优先保证“当前可以做什么”清晰可见

### 4.3 底部右侧：扮演交互流

职责：

- 展示本次扮演过程中的即时输入与输出

内容：

- 玩家决策文本
- 决策解析出的动作链
- 玩家选择结果
- 对话时玩家发言
- 对话时对方回复
- 对话结束后的 summary
- 解析失败 / 提交失败提示

说明：

- 这是 interaction stream
- 不是 world event stream
- 它记录的是“这一轮扮演过程中发生了什么交互”

### 4.4 interaction stream 展示原则

- 高密度
- 单行优先
- 最近记录优先
- 与世界事件视觉上有区分，但信息密度要接近

建议格式：

- `>` 玩家决策输入
- `=` 动作链 token 串
- `?` 一次性选择结果
- `你` 玩家对话发言
- `彼` 对方回复
- `#` 对话 summary
- `!` 错误或失败提示

## 5. 事件栏 filter 语义

### 5.1 进入扮演

- 记录当前右侧事件栏筛选状态为 `pre_roleplay_event_filter`
- 自动切换为 `avatar_id = controlled_avatar_id`

### 5.2 扮演中切换角色

- 更新右侧事件栏 filter 为新 avatar
- 不保留旧 avatar filter

### 5.3 退出扮演

- 若存在 `pre_roleplay_event_filter`，恢复该状态
- 若不存在，则恢复为默认全局事件视图

### 5.4 非目标

本次不新增多角色并列事件视图。

## 6. 前端实现建议

### 6.1 RoleplayDock

当前 `RoleplayDock` 建议改为固定两栏：

- 左：`ActiveRequestPane`
- 右：`InteractionStreamPane`

其中：

- 左侧根据 `decision / choice / conversation / observing` 切 request body
- 右侧始终渲染 `RoleplayInteractionHistory`

### 6.2 EventPanel

右侧事件栏需要支持一种“由扮演状态自动驱动 filter”的模式。

建议：

- 不要直接在 `EventPanel` 内部写死 roleplay 逻辑
- 由外层 store / composable 提供：
  - 当前是否处于 roleplay
  - 当前 controlled avatar id
  - 进入扮演前的旧筛选状态

### 6.3 Store / Composable

建议新增一个轻量状态：

- `preRoleplayEventFilter`

触发逻辑：

- start roleplay 时保存当前事件栏 filter
- controlled avatar 变化时同步事件栏 filter
- stop roleplay 时恢复

## 7. 边界情况

### 7.1 扮演角色死亡 / 失效

- 自动退出扮演
- 右侧事件栏恢复到扮演前筛选状态

### 7.2 读档 / 重开 / reset

- roleplay session 清空
- interaction stream 清空
- 右侧事件栏退出 roleplay 自动 filter

### 7.3 用户手动改了右侧事件栏筛选

建议一期策略：

- 扮演期间，右侧栏 filter 由 roleplay 强绑定控制
- 不允许用户在扮演期间把右侧栏改成别的 avatar

后续若要支持更复杂行为，再单独设计。

## 8. 非目标

本次不处理：

- interaction stream 持久化进存档
- interaction stream 与 event stream 合并成一套数据源
- 多角色扮演
- 扮演期间手动编辑右侧栏 filter 的高级行为

## 9. 实施顺序建议

1. 先移除底部右侧 world event stream，改成 interaction stream 固定区
2. 再接右侧事件栏的 roleplay 自动 filter
3. 再补退出扮演后的筛选恢复
4. 最后补前端回归测试

## 10. 测试建议

前端至少补：

- 进入扮演后，右侧事件栏自动变为当前 avatar filter
- 退出扮演后，右侧事件栏恢复旧 filter
- 底部右侧始终显示 interaction stream
- 底部左侧在 `observing` 时不丢失右侧 interaction stream
- `decision / choice / conversation` 三种状态切换时，左侧只切当前请求区

后端无需新增协议，仅复用现有：

- roleplay session query
- events query by avatar

