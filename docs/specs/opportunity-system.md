# 机缘系统设计说明

本文档描述“机缘（opportunity）”系统的一期设计。机缘与现有 `fortune` 奇遇不同：`fortune` 是月度随机命中后即时结算的世界事件；机缘是先生成一条绑定单人的限时感应，角色之后通过移动或接近目标才触发结算。

当前设计目标是先把核心体验做稳：不新增动作，不做任务导航，不做复杂分层奖励，不做直接突破。

## 1. 目标

机缘系统希望表达修仙叙事中的“缘法牵引”：

1. 角色偶尔福至心灵，感应到某人或某地与自身缘法相牵。
2. 感应不是明确任务，也不是系统导航，只是一段模糊线索。
3. 角色是否追寻、如何追寻，交给现有 AI 决策。
4. 角色若在期限内抵达目标地或接近目标人，则触发结算。
5. 结算可能获得宝物、获得助益、空手而返，或遭遇凶险受伤乃至死亡。

## 2. 与现有系统的边界

### 2.1 与 fortune 的区别

现有 `fortune` 位于 `src/systems/fortune.py`，语义是“当月触发，当月结算”。

机缘不复用该语义：

- `fortune`：即时奇遇，触发后立刻给装备、功法、修为、灵石等结果。
- `opportunity`：限时线索，先进入 active state，之后靠角色移动命中目标再结算。

因此机缘应有独立概率、独立配置、独立状态与独立故事类型，不应继续挤入 `fortune_probability` 或 `StoryEventKind.WORLD_FORTUNE`。

### 2.2 与 hidden domain 的区别

秘境是世界级或 gathering 类内容，通常由系统开放并吸引多人参与。

机缘是一名角色自己的私有缘法：

- 不公开展示为世界入口。
- 不作为前端独立板块。
- 不允许多人共享同一条机缘状态。

### 2.3 与动作系统的关系

机缘一期不新增动作。

追寻机缘只复用现有行动：

- `MoveToDirection`
- `MoveToRegion`
- `MoveToAvatar`

系统不提供 `SearchOpportunity`、`FollowOpportunity` 等新动作。

## 3. 非目标

一期明确不做以下内容：

1. 不新增专用追寻机缘动作。
2. 不新增前端机缘板块。
3. 不做坐标型机缘。
4. 不做 direction 型目标；方向只可作为模糊感应文本的一部分。
5. 不做直接突破奖励。
6. 不做普通成功 / 巨大成功二级成功判定。
7. 不做复杂风险预告。
8. 不在 AI context 中提供 `suggested_search`、`risk_hint`、推荐动作或真实目标 ID。
9. 不把机缘做成可点击任务导航。

## 4. 核心模型

机缘是一条绑定单个 avatar 的限时世界状态。

建议新增一个 manager 或等价服务来维护 active opportunities，例如：

- `world.opportunity_manager`
- 或 `world.active_opportunities`

同一名角色最多同时拥有一条 active opportunity。

建议内部记录结构：

```python
{
    "id": "...",
    "avatar_id": "...",
    "target_type": "region|avatar",
    "target_id": "...",
    "hint_text": "...",
    "created_month": 1234,
    "expires_month": 1294,
}
```

其中：

- `target_type` 只允许 `region` 或 `avatar`。
- `target_id` 存真实 region id 或 avatar id。
- `hint_text` 是给角色和事件系统看的模糊文本。
- `created_month` 用于避免生成当月立刻触发。
- `expires_month` 用于过期清理。

如果未来需要扩展 reward profile 或 story archetype，可以在该 record 中追加字段，但一期不要求提前复杂化。

## 5. 目标类型

### 5.1 Region 目标

Region 目标表示机缘落在某个区域。

命中条件：

- 角色当前 tile 有 region；
- 且 `avatar.tile.region.id == opportunity.target_id`；
- 且 `current_month > created_month`。

进入目标 region 任意 tile 即可触发，不要求精确坐标。

生成约束：

- 不选择荒野 `-1`。
- 不选择角色当前所在 region。
- 不选择不存在的 region。
- 对敌宗总部等通常不可进入区域，应谨慎过滤，除非后续明确设计高风险机缘。

### 5.2 Avatar 目标

Avatar 目标表示机缘系于某个具体角色。

命中条件：

- 目标角色仍然存在；
- 目标角色未死亡；
- 目标进入 owner avatar 的观察范围；
- 且 `current_month > created_month`。

不要求同 tile。

目标角色后续移动、突破不影响机缘。目标死亡后，机缘散去。

当前没有改名机制，因此不需要为改名设计特殊规则；若未来新增改名，内部仍以 avatar id 为准。

## 6. 线索文本

线索文本只表达角色主观感应，不提供系统建议。

允许文本中包含：

- 大致方向；
- 模糊地貌；
- 模糊人物特征；
- 模糊因果意象；
- 期限感。

不允许文本中包含：

- 真实目标 ID；
- 明确推荐动作；
- `MoveToDirection` / `MoveToRegion` / `MoveToAvatar` 等动作名；
- “你应该去……”这类系统指令；
- 风险等级提示。

推荐形式：

```text
某某福至心灵，隐约感到一线机缘与东南水泽间某处相牵。
```

```text
某某心有所感，似有一线机缘系于北方某位金丹剑修。
```

```text
某某近日屡梦残钟，似有机缘落在西方一座古城之中。
```

AI context 中也应只暴露这类自然语言，例如：

```text
机缘感应：近日心神偶动，似有一线机缘牵系于北方某位金丹剑修。此感应约还可维持三年余。
```

不要额外提供 `suggested_search` 或 `risk_hint`。

## 7. 生成规则

### 7.1 触发时机

机缘生成可以放在月度世界事件阶段，与 fortune / misfortune 类似，但使用独立概率。

生成前应检查：

1. 角色存活。
2. 角色可以触发世界事件。
3. 角色当前没有 active opportunity。
4. 角色不在 opportunity cooldown 中。
5. 随机概率命中。

### 7.2 配置建议

建议在 `static/config.yml` 中新增：

```yaml
world:
  opportunity:
    probability: 0.001
    duration_months: 60
    cooldown_months_after_dissipated: 12
    cooldown_months_after_resolved: 60
    target_weights:
      region: 70
      avatar: 30
    outcome_weights:
      equipment: 35
      boon: 35
      empty: 20
      injury: 10
```

这些字段属于版本内置静态平衡配置，应放在 `static/config.yml`，不属于用户设置或 `RunConfig`。

### 7.3 概率修正

机缘触发概率应独立于 `fortune_probability`。

建议新增 effect 字段：

- `extra_opportunity_probability`

该字段用于修正机缘生成概率。

气运、goldfinger、persona 等可通过现有 effect 系统提供该字段。是否额外让 luck 派生 opportunity 概率，可在实现时按平衡需求决定，但命名上不应复用 `extra_fortune_probability` 作为机缘唯一入口。

一期暂不新增复杂的成功率、危险率、结果权重 effect，避免过早发散。

## 8. AI 决策上下文

角色有 active opportunity 时，AI 决策上下文应包含该感应。

推荐只以自然语言暴露：

```text
机缘感应：某某福至心灵，隐约感到一线机缘与东南水泽间某处相牵。此感应约还可维持四年。
```

不建议暴露结构化攻略字段。

允许内部使用结构化字段管理状态，但给 LLM 的内容应保持“角色主观感应”语义。

persona 对追寻行为的影响分两类：

1. 数值影响：通过 effect 修正触发概率。
2. 行为影响：在 persona / goldfinger 的叙事提示中体现追逐或回避机缘的倾向。

例如：

- 冒险性格可在行为提示中说明“更愿意追逐未知机缘”。
- 保守性格可说明“不轻易为模糊机缘涉险”。

这类行为影响交给 LLM 决策，不做硬编码动作选择。

## 9. 检测与清理

### 9.1 命中检测

命中检测放在动作执行后。

原因：

- `MoveToDirection` 当月移动到目标 region 后可以触发。
- `MoveToRegion` 到达目标 region 后可以触发。
- `MoveToAvatar` 或自然移动接近目标后可以触发。
- 避免行动前莫名结算。

检测时应跳过生成当月的机缘，即 `current_month <= created_month` 时不触发。

### 9.2 过期清理

当 `current_month >= expires_month` 时，机缘散去。

散去后：

- 清理 active opportunity。
- 记录 cooldown。
- 生成普通事件。

推荐事件：

```text
某某心头那缕机缘感应渐渐散去，终究未能寻得。
```

### 9.3 目标失效

目标失效时，机缘散去。

Region 目标失效：

- target region 不存在。

Avatar 目标失效：

- target avatar 不存在；
- target avatar 已死亡。

推荐事件：

```text
某某心头那缕机缘感应骤然断绝，终究无从寻起。
```

### 9.4 Owner 死亡

机缘 owner 死亡时，清理 active opportunity。

不强制额外生成散去事件；死亡事件本身已经足够表达重大事实。

## 10. 结算结果

一期 outcome 只包含四种：

- `equipment`
- `boon`
- `empty`
- `injury`

死亡不是独立 outcome，而是 `injury` 扣减 HP 后自然导致的结果。

### 10.1 Equipment

装备奖励规则：

1. 奖励装备品阶为角色当前境界 +1 阶。
2. 封顶最高境界。
3. 不做 +2 阶。
4. 不做普通成功 / 巨大成功二级判定。
5. 装备类型包含 weapon 与 auxiliary。
6. 优先补角色短板：
   - 无 weapon 或 weapon 低于当前境界时，提高 weapon 权重。
   - 无 auxiliary 或 auxiliary 低于当前境界时，提高 auxiliary 权重。
   - 两者都不缺时，可随机或转为 boon。
7. 获得装备时应复用现有 item exchange 逻辑，避免静默覆盖已有装备。

推荐事件：

```text
某某循着机缘而至，得获古修遗物：{item_name}。
```

### 10.2 Boon

巨大加成应优先复用现有 effect 系统，不新造平行属性系统。

建议通过配表驱动 boon，而不是把加成规则写死在业务代码中。

可选配表字段：

```csv
id,effects,duration_months,weight,min_realm,max_realm,title_id,desc_id
```

示例：

```csv
1,"{extra_luck: 1}",0,10,QI_REFINEMENT,NASCENT_SOUL,...
2,"{extra_max_lifespan: 10}",0,10,QI_REFINEMENT,NASCENT_SOUL,...
3,"{extra_respire_exp_multiplier: 0.5}",60,10,QI_REFINEMENT,NASCENT_SOUL,...
4,"{extra_battle_strength_points: 2}",60,10,QI_REFINEMENT,NASCENT_SOUL,...
```

其中：

- `duration_months = 0` 表示永久效果，写入 `persistent_effects`。
- `duration_months > 0` 表示限时效果，写入 `temporary_effects`。

添加效果后必须重算角色 effects。

推荐事件：

```text
某某循着机缘有所悟，气机洗练，获得了新的助益。
```

### 10.3 Empty

无事发生表示角色找到了感应源头，但机缘已经散尽或并未成真。

推荐事件：

```text
某某循着感应而至，却只见灵机散尽，终究无所得。
```

该结果仍然视为已结算，清理 active opportunity，并进入 resolved cooldown。

### 10.4 Injury

受伤表示角色追寻机缘时遭遇凶险。

伤害建议按最大 HP 百分比计算，避免固定值在不同境界上失衡。

若扣减后 HP 小于或等于 0，则按现有死亡流程处理。死亡不需要独立 outcome。

推荐事件：

```text
某某循着机缘而至，却遭残留凶险反噬，受伤 {damage} 点。
```

若死亡：

```text
某某循着机缘而至，却遭残留凶险反噬，身死道消。
```

## 11. 事件语义

### 11.1 感应事件

生成 active opportunity 时，写入一条普通事实事件。

建议：

- `is_major=False`
- `is_story=False`
- `related_avatars=[owner.id]`

### 11.2 散去事件

过期或目标失效时，写入普通事实事件。

建议：

- `is_major=False`
- `is_story=False`
- `related_avatars=[owner.id]`

### 11.3 结算事件

命中后写入结算事实事件。

建议：

- equipment / boon / injury death 可设为 `is_major=True`
- empty / non-lethal injury 可设为 `is_major=False`
- `related_avatars` 至少包含 owner id
- avatar 目标命中时包含 target avatar id

### 11.4 故事事件

感应和散去不走 LLM。

命中结算后可按概率尝试追加故事事件。

建议新增：

- `StoryEventKind.OPPORTUNITY`
- `static/config.yml -> world.story.probabilities.opportunity`

故事事件仍遵守现有小故事系统规则：

- 先生成基础事实事件。
- 再尝试通过 `StoryEventService.maybe_create_story(...)` 追加故事。
- LLM 展开的正文事件使用 `is_story=True`。
- 默认 `allow_relation_changes=False`。

## 12. 存档结构

active opportunities 是世界长期状态，应进入存档。

不应只写入事件数据库，也不应视为 runtime 临时状态。

建议存档结构：

```json
"opportunities": {
  "active": {
    "avatar_id": {
      "id": "...",
      "avatar_id": "...",
      "target_type": "region",
      "target_id": "201",
      "hint_text": "...",
      "created_month": 1234,
      "expires_month": 1294
    }
  },
  "cooldowns": {
    "avatar_id": 1354
  }
}
```

读档后应恢复 active opportunities 与 cooldowns。

开发阶段不要求为旧存档付出复杂兼容成本；若零代价可 `.get` 兜底，则可顺带处理。

## 13. Cooldown 规则

建议 cooldown 分两类：

1. 散去 cooldown：12 个月。
2. 已结算 cooldown：60 个月。

其中已结算包括：

- equipment
- boon
- empty
- injury
- injury 后死亡

目标 avatar 死亡导致散去，按散去 cooldown。

## 14. World Info

应在 `static/game_configs/world_info.csv` 中新增“机缘”通用说明。

说明只描述世界概念，不暴露机制数字。

推荐文案：

```text
修士偶有福至心灵，感应到某人或某地与自身缘法相牵。若循感应而去，或得宝物与助益，或空手而返，亦可能遭逢凶险；若迟迟未寻，机缘也会自行散去。
```

## 15. i18n

新增文本应遵守当前 i18n 规则：

1. 日常开发默认 Phase 1，可优先只补 `zh-CN`。
2. 若进入正式多语言补全，应按 `static/locales/registry.json` 中启用语言统一处理。
3. `.po` 中 `msgid` 不得直接写中文。
4. 中文内容放在 `msgstr`。
5. 不要直接修改 `LC_MESSAGES/*.po` 合并产物；优先维护 `modules/` 或 `game_configs_modules/`。
6. 改完源文件后运行 `python tools/i18n/build_mo.py`。

建议新增模块：

- `static/locales/<lang>/modules/opportunity.po`

若新增 opportunity / boon 配表，则对应新增：

- `static/locales/<lang>/game_configs_modules/opportunity.po`
- 或按最终配表文件名拆分。

## 16. 前端

一期不新增前端独立机缘板块。

允许通过以下已有路径体现机缘：

1. 事件栏显示感应、散去、结算事件。
2. 角色详情或 AI context 中显示当前机缘感应文本。
3. Roleplay 场景下，玩家接管角色时应能看到当前机缘感应。

如果角色详情展示 active opportunity，也应保持克制，只显示一行自然语言感应，不做任务面板、倒计时任务卡或导航按钮。

## 17. 建议实现位置

后续实现时建议新增独立模块，避免继续扩散到 `src/server/main.py` 或 fortune 文件中。

可能位置：

- `src/systems/opportunity.py`
- `src/systems/opportunity_types.py`
- `src/systems/opportunity_loader.py`
- `src/systems/opportunity_service.py`

接入 phase：

- 月度生成：world passive/world event phase。
- 命中检测：action execution 之后的新 phase。
- 过期清理：可在月度 passive phase 或命中检测 phase 中统一处理。

若新增 manager：

- 可挂载在 `World` 上；
- 存档时序列化到 `world_data["opportunities"]`；
- 读档时恢复。

## 18. 测试建议

至少应覆盖：

1. 没有 active opportunity 且概率命中时生成机缘。
2. 有 active opportunity 时不再生成新机缘。
3. cooldown 中不生成新机缘。
4. region 目标进入任意 tile 后触发结算。
5. avatar 目标进入观察范围后触发结算。
6. 生成当月不立刻触发。
7. 过期后写入散去事件并清理 active opportunity。
8. target avatar 死亡后写入断绝事件并清理 active opportunity。
9. owner 死亡后清理 active opportunity。
10. equipment outcome 给当前境界 +1 阶装备，并复用 item exchange。
11. boon outcome 写入 temporary / persistent effects，并重算 effects。
12. empty outcome 清理 opportunity 并进入 resolved cooldown。
13. injury outcome 扣减 HP。
14. injury 导致 HP <= 0 时走死亡流程。
15. active opportunities 与 cooldowns 可存档和读档恢复。
16. AI context 只暴露模糊感应文本，不暴露 target id、suggested action 或 risk hint。
17. 新增 `StoryEventKind.OPPORTUNITY` 后，故事事件仍使用 `is_story=True`。
18. world info 包含机缘通用说明。

## 19. 当前拍板结论

本轮需求确认后的最终结论：

1. 机缘与 fortune 分离，是独立限时状态。
2. 机缘目标只有 region 和 avatar。
3. Region 命中范围是任意目标 region tile。
4. Avatar 命中范围是 owner 的观察范围。
5. 命中检测放在动作执行后。
6. 机缘线索不提供 suggested search、risk hint 或动作推荐。
7. AI 只看到自然语言的模糊感应和剩余时间。
8. 角色是否追寻由现有 AI 决策。
9. 一期奖励只有越一阶装备和巨大加成。
10. 不做直接突破。
11. 不做普通成功 / 巨大成功。
12. 受伤可能自然导致死亡；死亡不是独立 outcome。
13. 感应、散去、结算都写入事件系统。
14. 感应和散去不走 LLM；结算可选走小故事。
15. active opportunities 与 cooldowns 进入存档。
16. 前端不新增独立机缘板块。
