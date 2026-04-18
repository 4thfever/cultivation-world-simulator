# 底部扮演栏左侧：输入记录与动作链展示 Spec

本文档聚焦角色扮演模式下，底部 `RoleplayDock` 左侧区域的结构设计，重点解决以下三个问题：

1. 玩家提交过的决策文本不要每次都清空到“无痕”，而要以某种形式保留下来。
2. 玩家输入被后端翻译成动作链后，应在前端以当前语言可读地展示出来。
3. 展示形式尽量接近 `['移动到', '某地']` 这种高信息密度的结构化片段，且尽量少引入额外文本配置工作。

该设计默认服务于一期文本决策，也兼容二期 `choice` 和三期 `conversation` 在同一 dock 骨架下继续扩展。

---

## 1. 目标

### 1.1 交互目标

底部扮演栏左侧不应只是一个“当前输入框”，而应逐步形成一个轻量的“操作记录流”：

- 玩家输入过什么意图
- 系统把它翻译成了什么动作链
- 当前是否已经开始执行

这样玩家不会有“我刚说了什么、系统到底理解成什么”的断裂感。

### 1.2 展示目标

动作链展示不追求自然语言长句，而追求：

- 高信息密度
- 一眼扫过能看懂
- 和事件流、聊天流并存时不显臃肿

因此更推荐“片段化 token 展示”，而不是大段说明文字。

### 1.3 实现目标

优先复用现有动作系统中的：

- `ACTION_NAME_ID`
- `PARAMS`
- 参数原值

避免为了显示动作链而要求每个动作再手写一套新的多语言描述模板。

---

## 2. 非目标

本次不追求：

1. 不把动作链展示做成完整的计划编辑器。
2. 不允许玩家直接在前端逐条修改 action plan。
3. 不要求把每个动作都翻译成特别自然的完整句子。
4. 不为每个 action 新增专门的 `ROLEPLAY_DOCK_DESC_ID` 一类配置。
5. 不把这套历史记录写进存档。

---

## 3. 用户体验设计

## 3.1 左侧区域的新结构

建议将 `RoleplayDock` 左侧 `Active Request` 区进一步拆成上下两段：

1. 上方：当前请求输入区
   - `decision`：文本框 + 提交
   - `choice`：按钮
   - `conversation`：聊天输入
2. 下方：最近操作记录流

其中“最近操作记录流”是本次新增重点。

---

## 3.2 最近操作记录流的记录类型

建议统一抽象为 `RoleplayInteractionRecord`，至少支持以下类型：

### A. `decision_input`

表示玩家刚刚提交的文本意图。

示例：

- 我先调息恢复，再去附近探索。
- 去拜访阴长生，看看能不能交谈。

### B. `decision_resolved`

表示系统已经把玩家意图翻译成动作链。

示例展示：

- 调息
- 移动到 青石谷
- 探索附近

或更紧凑地显示为一串 token 块。

### C. `decision_rejected`

表示系统未能生成有效动作链。

示例：

- 无法从本次输入生成有效行动计划

### D. `choice_selected`

二期兼容：记录玩家点击了哪个选项。

### E. `conversation_turn`

三期兼容：只在需要时可复用，不是本次重点。

---

## 3.3 输入框不要“消失无痕”

当前行为是：

- 玩家输入
- 提交成功
- 输入框被清空

这个行为本身可以保留，但必须补一个“已提交记录”：

- 输入框可以清空，方便继续下一次输入
- 但刚提交的文本要立即进入最近操作记录流

也就是说：

- 清空输入框是可以的
- 清空“用户痕迹”是不可以的

---

## 3.4 推荐显示形式

推荐每条记录都尽量短，类似终端或工作流日志，而不是卡片。

### 玩家输入

```text
> 我先调息恢复，再去附近探索。
```

### 系统翻译后的动作链

```text
= 调息
= 移动到 青石谷
= 探索附近
```

或更结构化：

```text
= [调息]
= [移动到] [青石谷]
= [探索] [附近]
```

其中：

- `>` 表示玩家输入
- `=` 表示系统解析结果

这样信息密度高，也不会和右侧事件流混淆。

---

## 4. 数据模型建议

## 4.1 运行时记录

建议在 `RoleplaySession` 中新增纯 runtime 字段：

- `interaction_history`

建议结构：

```python
interaction_history: list[dict]
```

每条记录示例：

```python
{
    "id": "roleplay-record-123",
    "type": "decision_input",
    "avatar_id": "avatar-1",
    "content": "我先调息恢复，再去附近探索。",
    "created_at": 1710000000.0,
}
```

动作链解析结果：

```python
{
    "id": "roleplay-record-124",
    "type": "decision_resolved",
    "avatar_id": "avatar-1",
    "source_request_id": "roleplay-decision-xxx",
    "actions": [
        {"action_name": "Respire", "params": {}},
        {"action_name": "MoveToRegion", "params": {"region": "青石谷"}},
    ],
    "created_at": 1710000001.0,
}
```

### 语义要求

- 这是 runtime UI 辅助信息，不进入存档。
- `load / reset / reinit / start` 后一起清空。
- 建议只保留最近 `20~40` 条，避免无限膨胀。

---

## 4.2 为什么建议放 runtime，而不是纯前端本地

纯前端本地也能做，但不够稳。

放 runtime 的好处：

1. 切换详情面板、切换 UI 视图后不会丢。
2. websocket / query 刷新后仍可恢复。
3. 多个组件可共享，不需要自己猜状态。

因此推荐：

- 真源：runtime `interaction_history`
- 前端 store：只做缓存映射

---

## 5. 动作链翻译显示设计

## 5.1 输入来源

一期后端已经拿到了：

- `action_name_params_pairs`

也就是：

```python
[
    ("Respire", {}),
    ("MoveToRegion", {"region": "青石谷"}),
]
```

这已经足够支持一个“少配置”的显示方案。

---

## 5.2 最小成本方案

建议直接基于动作类已有元数据生成可显示片段：

1. 用 `ActionRegistry.get(action_name)` 找到动作类
2. 读取其 `ACTION_NAME_ID`
3. 用当前语言的 `t(ACTION_NAME_ID)` 作为主动作名
4. 读取 `PARAMS`
5. 根据参数类型和值，生成附加 token

这样大部分动作不需要额外配置。

---

## 5.3 推荐的显示中间层

建议新增一个统一 view model：

```python
ActionDisplayToken = {
    "kind": "verb" | "arg" | "sep" | "fallback",
    "text": str,
}
```

每个 action 最终渲染成：

```python
{
    "action_name": "MoveToRegion",
    "tokens": [
        {"kind": "verb", "text": "移动到"},
        {"kind": "arg", "text": "青石谷"},
    ]
}
```

前端只负责按 token 排列渲染，不负责重新理解 action 语义。

---

## 5.4 参数翻译策略

为了避免给每个动作都新增专门文案，建议采用“动作名 + 参数格式器”的统一方案。

### 第一层：直接复用动作名翻译

动作名来自：

- `ACTION_NAME_ID`

例如：

- `move_to_region_action_name -> 移动到`
- `respire_action_name -> 调息`
- `talk_action_name -> 攀谈`

这部分仓库里已经有，不新增配置。

### 第二层：参数使用通用 formatter

参数显示优先按参数类型或参数 key 走统一 formatter：

#### 按参数类型

- `AvatarName` -> 直接显示目标角色名
- `RegionName` / `region_name` -> 直接显示地区名
- `str` -> 直接显示原值
- `int/float` -> 直接显示原值

#### 按特殊 key 做少量全局映射

只建议新增一小张共享映射表，不要每个 action 自己配：

- `direction`
  - `north -> 北`
  - `south -> 南`
  - `east -> 东`
  - `west -> 西`
- `target_realm`
  - 走现有 realm 翻译
- `delta_x / delta_y`
  - 转成方向或“偏移”文本

也就是说：

- 新增的是“少量全局参数格式器”
- 不是“每个动作新增一套 dock 文案”

---

## 5.5 fallback 策略

若无法优雅翻译某个 action：

### 第一层 fallback

显示：

```text
[动作名] [参数值]
```

### 第二层 fallback

若连动作名 key 都拿不到，则显示：

```text
[MoveToRegion] [region=青石谷]
```

确保：

- 永远有东西看
- 不会因为缺少配置导致整条动作链空白

---

## 6. 一个“少配置”的推荐实现方案

## 6.1 后端新增 action display builder

建议新增统一 helper，例如：

- `src/server/services/roleplay_action_display.py`

职责：

1. 接收 `action_name_params_pairs`
2. 查动作类元数据
3. 输出 `ActionDisplayToken` 列表

建议接口：

```python
build_roleplay_action_display_pairs(
    action_name_params_pairs,
    language_manager,
) -> list[dict]
```

输出：

```python
[
    {
        "action_name": "Respire",
        "tokens": [{"kind": "verb", "text": "调息"}],
    },
    {
        "action_name": "MoveToRegion",
        "tokens": [
            {"kind": "verb", "text": "移动到"},
            {"kind": "arg", "text": "青石谷"},
        ],
    },
]
```

---

## 6.2 在一期提交流程中写入 interaction history

在 `submit_roleplay_decision(...)` 成功时，追加两条记录：

1. `decision_input`
2. `decision_resolved`

失败时追加：

1. `decision_input`
2. `decision_rejected`

这样左侧记录流会天然形成成对结构：

```text
> 我先调息恢复，再去附近探索。
= 调息
= 探索附近
```

---

## 6.3 前端渲染

建议在 `RoleplayDock` 左侧请求区内，输入区下面新增：

- `RoleplayInteractionHistory.vue`

职责：

- 渲染 `interaction_history`
- 不做业务逻辑判断
- 只按 `type` 和 token 列表渲染

显示顺序建议：

- 最新记录在下方
- 自动滚动到底部

---

## 7. UI 结构建议

## 7.1 `decision` 模式

左侧结构建议：

```text
[请求标题]
[请求说明]
[输入框]
[提交按钮]
[最近操作记录流]
```

其中最近操作记录流默认展示最近 5~10 条即可。

---

## 7.2 样式建议

不要再做大卡片。

建议更像终端日志：

- 玩家输入：弱高亮
- 系统动作链：普通亮色 token
- 错误：偏红

例如：

```text
> 我先调息恢复，再去附近探索。
= [调息]
= [探索附近]
! 未能生成有效行动计划
```

---

## 8. 与多语言的关系

## 8.1 目标

动作链展示要“尽量本地化”，但不要把 i18n 工作量放大成每个动作都补一套新模板。

### 推荐复用顺序

1. `ACTION_NAME_ID`
2. 现有实体名 / 地区名 / 角色名
3. 少量共享参数 formatter
4. fallback 文本

---

## 8.2 不建议的方案

不建议让每个 action 额外新增：

- `ROLEPLAY_DOCK_TEXT_ID`
- `ROLEPLAY_DOCK_TEMPLATE`

原因：

- 维护成本高
- 极易漏配
- 会把一个展示问题变成动作系统大规模补配置

---

## 9. 边界情况

### 9.1 多个 action 连续展示太长

若单次动作链过长：

- 默认全部记录
- UI 只展开前 `3~5` 条
- 剩余显示 `+N`

### 9.2 参数是复杂对象

若参数不是简单字符串：

- 优先抽取名称字段
- 不行就 fallback 为简短 JSON 片段

### 9.3 locale 切换

由于展示 tokens 基于当前语言生成，建议：

- interaction history 原始保留 `action_name + params`
- query 返回时或前端映射时按当前语言重新生成显示文本

不要只保存已经渲染好的中文字符串，否则切语言后会混乱。

---

## 10. 实现分步建议

### 第一步

先实现一期最小闭环：

- runtime 增加 `interaction_history`
- `submit_roleplay_decision` 成功/失败写记录
- 后端 action display builder
- 前端左侧记录流渲染

### 第二步

补通用参数 formatter：

- direction
- realm
- avatar / region / item 名称

### 第三步

再考虑把二期 `choice_selected` 和三期 `conversation_turn` 也并入同一条左侧交互历史流

---

## 11. 测试建议

### 后端

1. 提交 decision 后会写入 `decision_input`
2. 成功解析后会写入 `decision_resolved`
3. `decision_resolved` 中包含 token 化动作链
4. 缺少翻译时会 fallback，但不会空白

### 前端

1. 提交后输入框清空，但历史记录保留
2. 历史记录正确显示玩家输入
3. 历史记录正确显示动作链 token
4. 长动作链可折叠或截断显示

---

## 12. 结论

底部扮演栏左侧不应该只是“当前输入框”，而应该升级为一个轻量的“操作记录流”：

- 玩家输入保留痕迹
- 系统解析结果可见
- 动作链按当前语言显示

最推荐的实现路线是：

1. 保留输入框提交后清空的行为
2. 在 runtime 中记录 `interaction_history`
3. 复用动作类已有 `ACTION_NAME_ID`
4. 用少量共享参数 formatter 把 `action_name_params_pairs` 转成 token 化展示
5. 前端用高密度日志形式渲染

这样可以在尽量少增加配置的前提下，把“玩家说了什么 / 系统理解成什么”这件事清晰地展示出来。
