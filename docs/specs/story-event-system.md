# 小故事系统重构说明

> 本文档描述当前仓库已经落地的小故事（Story Event）机制。
>
> 当前实现请优先参考以下代码：
>
> - `src/classes/story_event_service.py`
> - `src/systems/battle.py`
> - `src/systems/fortune.py`
> - `src/classes/action/**/*.py`
> - `src/classes/mutual_action/**/*.py`
> - `src/classes/gathering/**/*.py`
> - `static/config.yml`

## 目标

本次重构的目标是把“小故事”从“在若干业务文件中直接调用 LLM 并产出事件”改成“统一故事入口服务 + 按类型配置概率”的结构。

这样做主要解决三个问题：

1. 以前许多入口会无条件出小故事，频率过高，容易重复。
2. 概率逻辑分散在不同文件里，不容易维护，也难以统一调参。
3. `gathering`、战斗、社交、奇遇等不同来源的故事语义不统一，后续代理改动时容易继续扩散。

## 设计原则

### 1. 小故事是结果事件的附加层

所有动作、系统、聚会都应当先完成业务结算，再生成基础结果事件。  
小故事只是在结果事件之后“尝试展开”的一层文本扩展。

因此标准流程是：

1. 结算状态变化
2. 生成基础事件
3. 调用 `StoryEventService.maybe_create_story(...)`
4. 命中则追加故事事件，未命中则跳过

### 2. 统一入口，避免散落

所有故事生成统一通过 `StoryEventService`：

- `maybe_create_story(...)`
- `maybe_create_gathering_story(...)`

业务层不再自己决定概率，也尽量不直接构造 `Event(..., is_story=True)`。

### 3. `gathering` 固定 100%

聚会类事件的故事概率固定为 `100%`，不再参与普通概率抽签。  
这类事件发生频率本就受外部系统控制，且天然适合用一段长文本来总结群体事件。

## 故事类型分类

当前通过 `StoryEventKind` 对故事来源做统一分类：

- `combat`
- `relationship_major`
- `cultivation_major`
- `crafting`
- `daily_social`
- `world_fortune`
- `world_misfortune`
- `gathering`

这些类型的概率配置统一放在：

- `static/config.yml -> game.story.probabilities`

## 事件语义约定

### 基础事件

基础结果事件继续保留原有语义：

- `is_major=True`：重大事实，进入长期记忆
- `is_major=False`：普通事实，进入短期记忆

### 小故事事件

所有由 LLM 展开的“正文型故事”统一使用：

- `is_story=True`

这些事件仍然会：

- 进入事件栏
- 进入事件分页接口

但它们不应替代基础事实事件本身。

## 当前接入范围

### 已重构为统一故事入口的旧路径

- 战斗收尾
- 暗杀成功
- 突破
- 闭关
- 表白
- 双修
- 结拜
- 切磋
- 奇遇
- 霉运

### 新增的低概率故事入口

- 茶会
- 下棋
- 送礼
- 传道
- 交谈
- 铸造
- 炼丹
- 御兽

### 固定 100% 出故事的 Gathering

- 拍卖会
- 秘境
- 天下武道会
- 宗门传道大会

## 测试策略

与小故事相关的测试应遵守以下原则：

1. 使用 `StoryEventService.should_trigger(...)` 控制是否出故事。
2. 不直接依赖真实随机数。
3. 业务测试分成两类：
   - 验证基础结果事件仍然正确
   - 验证命中或未命中故事时，事件列表结构符合预期
4. Gathering 测试应验证其故事事件为 `is_story=True`。

## 后续维护建议

后续如果新增小故事入口，应优先判断它是否满足以下条件：

- 是否有明确的“结果事件”可作为故事展开的锚点
- 是否具备足够叙事张力，而不是高频流水行为
- 是否能归入已有 `StoryEventKind`

若只是高频、重复、机械性的动作，不建议直接接入小故事，以免重新回到事件栏刷屏的问题。
