# World Lore Rewrite Pipeline Spec

本文档记录“世界观与历史”开局塑形系统的目标设计。它用于替代当前 `WorldLoreManager` 中“地图 / 宗门 / 物品三个大 LLM 任务读取全局 CSV 并返回局部修改意见”的实现。

本方案不要求向前兼容旧世界观塑形输出结构。实现时以当前代码清晰、结果完整、等待时间可控为优先。

## 目标

世界观输入不应只是少量配置项的建议性改名，而应产出本局专属的静态文本快照。

当玩家在开局填写“世界观与历史”后，系统应根据当前选择的地图和该世界观，统一重写以下内容：

1. 当前地图实际存在的所有地点：
   - 城市区域
   - 普通区域
   - 修炼区域
   - 宗门驻地
2. 所有宗门本体：
   - `name`
   - `desc`
3. 所有功法：
   - `name`
   - `desc`
4. 所有兵器：
   - `name`
   - `desc`
5. 所有辅助装备：
   - `name`
   - `desc`

默认应全量重写物品文本。若后续确实需要产品级开关，可以加入 `world_lore.rewrite_items`，但架构主路径必须支持全量重写，不应再以“只让 LLM 挑部分修改项”为核心流程。

## 非目标

本系统只重写本局静态展示文本，不改变玩法数值和结构。

不做：

1. 不新增地图 region。
2. 不新增宗门、功法、装备。
3. 不修改功法属性、品阶、条件。
4. 不修改兵器类型、境界、价格、效果。
5. 不修改辅助装备境界、价格、效果。
6. 不让 LLM 直接写入存档或运行时对象。
7. 不要求兼容旧 `world_lore_snapshot` 结构。

## 当前问题

当前实现位于 `src/classes/world_lore.py`，开局初始化阶段由 `src/server/init_flow.py` 调用。

现状主要问题：

1. 只有 `world_lore_map`、`world_lore_sect`、`world_lore_item` 三个大任务。
2. 三个任务虽然并发，但每个任务 prompt 都很大，尤其 `world_lore_item` 会塞入完整 `technique.csv`、`weapon.csv`、`auxiliary.csv`。
3. 世界观任务传入 `max_retries=3`，底层语义是初次调用加最多 3 次重试；单次 HTTP timeout 当前为 120 秒，最坏等待时间过长。
4. prompt 要求输出 `thinking`，地图和物品模板还要求详细分析，增加输出 token 和 JSON 解析失败概率。
5. 地图任务读取全局 region CSV，而不是当前 `world.map`，因此不能真正理解当前地图预设、`wilderness_tile`、`region_overrides`、landmarks 和当前 region 位置语义。
6. 失败粒度太粗，一个大任务卡住或解析失败会拖慢整个初始化阶段。
7. 初始化状态只显示 `shaping_world_lore`，无法定位卡在地图、宗门、功法还是装备。

## 总体设计

新系统采用“全量分块重写 + 共享全局 LLM semaphore + 局部 fallback + 一次性应用”的 pipeline。

流程：

1. 从当前 `world` 和玩家输入的 `world_lore` 构建重写上下文。
2. 可选生成一个短 `style_guide`，用于统一所有分块任务的命名和描述风格。
3. 基于当前 world 构建 rewrite jobs：
   - 地点 jobs
   - 宗门组 jobs
   - 功法 jobs
   - 兵器 jobs
   - 辅助装备 jobs
4. 每个 job 处理一个 chunk，输入数量固定，输出数量必须相同。
5. 所有 job 走现有 `call_llm_with_task_name`，共用全局 LLM semaphore。
6. 每个 job 有独立时间预算、最多一次格式重试。
7. 失败、超时、校验不通过的 job 使用 fallback 补齐。
8. 所有结果汇总为 `WorldLoreRewriteDraft`。
9. 先校验 draft 覆盖所有目标实体，再一次性 apply 到 world 和全局 registries。
10. 构建新的 `world_lore_snapshot` 并随存档保存。

## 模块拆分

不要继续把完整 pipeline 堆进 `src/classes/world_lore.py`。

建议结构：

```text
src/classes/world_lore.py
  WorldLore
  WorldLoreManager thin facade

src/systems/world_lore_rewrite/
  __init__.py
  models.py
  planner.py
  prompts.py
  runner.py
  validation.py
  fallback.py
  apply.py
```

职责：

1. `models.py`
   - 定义 context、job、chunk、draft、rewrite payload 等数据模型。
2. `planner.py`
   - 从当前 world 和 registries 构建 jobs。
   - 不读取全局 region CSV 原文作为地图输入。
3. `prompts.py`
   - 构造短 prompt infos。
   - 使用结构化 JSON 摘要，不传无关玩法字段。
4. `runner.py`
   - 调度 jobs。
   - 处理全局 deadline、job deadline、parse retry、取消、进度。
5. `validation.py`
   - 校验 LLM 输出 JSON、id 集合、字段长度和禁止内容。
6. `fallback.py`
   - 对失败 job 生成保底重写文本。
7. `apply.py`
   - 一次性应用 draft 到 world、sects、techniques、weapons、auxiliaries、ItemRegistry 和 name indexes。

`WorldLoreManager.apply_world_lore()` 应收束为门面：

```python
async def apply_world_lore(self, lore_text: str) -> None:
    context = build_world_lore_context(self.world, lore_text)
    draft = await WorldLoreRewriteRunner(context).run()
    apply_world_lore_rewrite(self.world, draft)
```

## 当前地图输入

地图重写必须基于当前 `world.map`，而不是全局 region CSV。

地图上下文至少包含：

1. `map_id`
2. `map_name`
3. `preset_version`
4. `width`
5. `height`
6. `wilderness_tile`
7. `landmarks`
8. `region_overrides`
9. 当前地图实际存在的 `regions`

每个 region 输入建议包含：

```json
{
  "id": 305,
  "type": "city",
  "name": "揽月港",
  "desc": "潮汐平稳的海港城，夜里月影落在长堤与船帆之间。",
  "tile_count": 23,
  "center": [50, 18],
  "landmark": {
    "x": 50,
    "y": 18,
    "asset": "city_305"
  },
  "map_override": true
}
```

不建议把完整 `region_rows` 传给 LLM。模型不擅长理解大型矩阵，且会显著增加 prompt 体积。若需要地图语义，应由代码预先生成摘要，例如：

1. 当前地图大面积荒野是海域还是平原。
2. region 所属类型。
3. region 是否使用地图局部覆盖名。
4. region landmark 是否为城市、宗门、洞府、遗迹等。
5. 可选的邻接地貌摘要。

## Job 类型

### Style Guide Job

可选前置任务，用于将玩家世界观压缩成短风格指南。

输出示例：

```json
{
  "world_tone": "末法、荒寒、宗门秩序崩坏",
  "naming_rules": [
    "地名偏残破、荒凉、古战场感",
    "功法名避免传统祥瑞词，偏灰烬、残阳、断脉"
  ],
  "forbidden_patterns": [
    "不要频繁使用太虚、玄天、九霄",
    "不要写数值加成"
  ],
  "description_style": "具体、可视化，不解释游戏机制"
}
```

该任务不得输出长思考。超时或失败时使用代码生成的默认 style guide。

### Region Rewrite Jobs

覆盖当前地图实际存在的所有 region，包括 sect regions。

输入 N 个 region，输出必须 N 个 region。

输出统一结构：

```json
{
  "entities": [
    {
      "id": 305,
      "name": "新的地点名",
      "desc": "新的地点描述"
    }
  ]
}
```

地点描述要求：

1. 匹配当前地图语义。
2. 侧重地貌、建筑、环境异象、生活氛围、修行氛围。
3. 不写玩家加成、数值效果、系统机制。
4. `desc` 默认 60 到 120 个中文字符左右。

### Sect Group Rewrite Jobs

宗门本体和对应宗门驻地应尽量在同一个宗门组 job 中处理，避免宗门描述和驻地描述脱节。

输入：

1. N 个 sects。
2. 对应 N 个 sect regions。

输出：

```json
{
  "sects": [
    {
      "id": 1,
      "name": "新宗门名",
      "desc": "新宗门描述"
    }
  ],
  "sect_regions": [
    {
      "id": 401,
      "name": "新驻地名",
      "desc": "新驻地描述"
    }
  ]
}
```

宗门本体描述要求：

1. 侧重宗门定位、修行方式、组织气质、内部结构、潜在矛盾。
2. 不重复驻地地貌。
3. 不复述门规、禁令、惩罚逻辑。
4. 不写玩家加成、数值效果、系统机制。

宗门驻地描述要求：

1. 侧重地貌、建筑、空间层次、环境异象、动态景象和感官氛围。
2. 与宗门本体语义互相配合，但不重复同一批信息。

### Technique Rewrite Jobs

全量重写所有功法 `name/desc`。

输入每个 technique 的必要字段：

```json
{
  "id": 1,
  "name": "混元金身",
  "desc": "旧描述",
  "attribute": "GOLD",
  "grade": "LOWER"
}
```

输出：

```json
{
  "entities": [
    {
      "id": 1,
      "name": "新功法名",
      "desc": "新功法描述"
    }
  ]
}
```

要求：

1. 保持原本属性和品阶定位。
2. 描述修行路径、气息、风险、意象。
3. 不写具体伤害、加成或游戏机制。
4. 不修改条件、权重、效果等字段。

### Weapon Rewrite Jobs

全量重写所有兵器 `name/desc`。

输入每个 weapon 的必要字段：

```json
{
  "id": 1001,
  "name": "旧兵器名",
  "desc": "旧描述",
  "weapon_type": "SWORD",
  "realm": "Qi_Refinement"
}
```

要求：

1. 保持原本武器类型和境界定位。
2. 描述材质、形制、来历、使用气质。
3. 不写数值加成。
4. 不改变武器类型语义。

### Auxiliary Rewrite Jobs

全量重写所有辅助装备 `name/desc`。

输入每个 auxiliary 的必要字段：

```json
{
  "id": 2001,
  "name": "旧辅助装备名",
  "desc": "旧描述",
  "realm": "Qi_Refinement"
}
```

要求：

1. 保持原本境界和辅助定位。
2. 描述佩戴方式、法器性质、护持或辅助意象。
3. 不写数值加成。
4. 不承诺不存在的机制。

## Prompt 约束

所有 rewrite prompt 都应短、强约束、无 thinking。

通用要求：

1. 只输出 JSON。
2. 不要输出 markdown。
3. 不要输出 thinking。
4. 输入多少个实体，输出多少个实体。
5. id 必须完全保留。
6. 不允许新增 id。
7. 不允许遗漏 id。
8. 只返回允许字段。
9. 不写游戏机制、数值、玩家加成。
10. 世界观风格要明显，但不要所有名称重复同一个词。

示意：

```text
你是仙侠世界设定编辑。根据世界观和风格指南，重写输入实体的 name 和 desc。

必须遵守：
- 输入多少个实体，输出多少个实体。
- id 必须完全保留。
- 只输出 JSON，不要解释，不要 markdown。
- 不要输出 thinking。
- 不要写游戏机制、数值、玩家加成。
- name 简洁，desc 具体、可视化。
- 保留实体原本的类别和玩法定位。
- 世界观风格要明显，但不要所有名称重复同一个词。

世界观：
{world_lore}

风格指南：
{style_guide}

当前地图摘要：
{map_summary}

实体：
{entities_json}

返回：
{
  "entities": [
    {"id": 1, "name": "...", "desc": "..."}
  ]
}
```

## 并发设计

世界观重写任务应共用现有 LLM 全局 semaphore。

现有 `src/utils/llm/client.py` 中 `call_llm()` 已通过 `_get_semaphore()` 控制外部请求并发。World Lore rewrite jobs 必须继续走 `call_llm_with_task_name`，不要���过该入口。

原则：

1. `max_concurrent_requests` 是唯一真实外部 LLM 请求并发上限。
2. 不新增 world lore 专用 HTTP 并发上限。
3. World Lore runner 可以维护 pending window，限制本地同时调度的 chunk task 数量。
4. pending window 不是服务商并发设置，只是避免一次性创建过多 coroutine。
5. 后续如果初始化或 step 中存在其他 LLM 任务，全局 semaphore 会统一保护服务商并发额度。

推荐 pending window：

```text
pending_window = max(current_llm_max_concurrent_requests * 2, 8)
```

若 jobs 总数小于 pending window，可一次调度全部 jobs。若后续实体数量扩大，则按窗口批量推进。

## Timeout 和 Retry

世界观重写是批处理任务，失败可以局部 fallback，因此不应沿用通用 LLM 的长等待和多次重试策略。

推荐默认配置：

```yaml
world_lore:
  total_timeout_seconds: 240
  task_timeout_seconds: 60
  min_retry_budget_seconds: 20
  max_parse_retries: 1
  max_transport_retries: 0
```

可收紧配置：

```yaml
world_lore:
  total_timeout_seconds: 180
  task_timeout_seconds: 45
  min_retry_budget_seconds: 15
  max_parse_retries: 1
  max_transport_retries: 0
```

语义：

1. `total_timeout_seconds`
   - 整个 world lore rewrite 的硬预算。
   - 到点后取消未完成 jobs。
   - 已完成结果保留。
   - 未完成 jobs 用 fallback 补齐。
   - 不中断初始化。
2. `task_timeout_seconds`
   - 单个 chunk job 从开始到成功、重试或 fallback 的总预算。
   - 不是单次请求预算。
3. `min_retry_budget_seconds`
   - 剩余预算低于该值时，不再发起 parse retry。
4. `max_parse_retries`
   - JSON 解析失败、id 缺失、输出数量不匹配、字段非法时最多重试一次。
   - 第二次 prompt 应附带上一次校验错误。
5. `max_transport_retries`
   - 网络超时、连接失败、HTTP 错误默认不重试。
   - 这类失败直接 fallback，避免拖垮初始化。

不建议：

```yaml
task_timeout_seconds: 120
max_parse_retries: 3
```

这会复现当前 300 秒以上等待的问题。

## Validation

LLM 输出必须通过严格校验后才能进入 draft。

通用校验：

1. 输出必须是 JSON object。
2. 必须包含约定字段。
3. 输出 id 集合必须等于输入 id 集合。
4. 输出数量必须等于输入数量。
5. `name` 必须非空。
6. `desc` 必须非空。
7. `name` 和 `desc` 长度必须在合理范围内。
8. 不允许写明显游戏机制或数值加成。
9. 不允许出现 markdown 代码块。
10. 额外字段应丢弃，不应应用。

校验失败后：

1. 若还有 parse retry 预算，则重试一次。
2. 若重试仍失败，则该 job 使用 fallback。
3. fallback 结果也必须通过基础非空和 id 校验。

## Fallback

Fallback 的目标不是产出最佳文案，而是保证本局世界观快照完整。

触发场景：

1. style guide 失败。
2. job 超时。
3. 网络或 HTTP 失败。
4. JSON 解析失败且重试耗尽。
5. 输出 id 缺失或数量错误且重试耗尽。
6. total timeout 到达后仍未完成的 jobs。

Fallback 策略：

1. 使用世界观关键词、实体旧名、实体类型生成轻量改写。
2. 不保留完全原文作为主 fallback。
3. 不写数值或机制。
4. 保持 id、类型、品阶、境界、武器类型等玩法语义。
5. 标记结果来源为 `fallback`，用于日志和统计。

Draft 中可以保留来源：

```python
source: Literal["llm", "fallback"]
```

该字段不一定进入存档，但应进入日志统计。

## Apply 语义

LLM job 不应直接修改 world 或全局 registry。

应先汇总 draft：

```python
@dataclass
class WorldLoreRewriteDraft:
    regions: dict[int, EntityRewrite]
    sects: dict[int, EntityRewrite]
    techniques: dict[int, EntityRewrite]
    weapons: dict[int, EntityRewrite]
    auxiliaries: dict[int, EntityRewrite]
```

然后统一 apply：

1. 更新当前 `world.map.regions` 中的 region `name/desc`。
2. 更新 `sects_by_id` 中的 sect `name/desc`。
3. sect 改名后更新 `sects_by_name`。
4. 更新 `techniques_by_id` 中的 technique `name/desc`。
5. technique 改名后更新 `techniques_by_name`。
6. 更新 weapons 和 auxiliaries。
7. item 改名后更新对应 by-name index。
8. 更新 `ItemRegistry`。
9. 调用 `sync_world_sect_metadata(world)`，确保宗门和驻地链接一致。
10. 构建新的 `world_lore_snapshot`。

Apply 前应校验 draft 覆盖所有目标实体。若缺失，先 fallback 补齐，不允许应用半成品 draft。

## Snapshot

新的 `world_lore_snapshot` 建议使用 schema v2。

结构示例：

```json
{
  "schema_version": 2,
  "lore_text": "玩家输入的世界观与历史",
  "map_id": "island_seas",
  "map_name": "群岛海域",
  "preset_version": 2,
  "rewrite_config": {
    "rewrite_items": true,
    "chunk_size": {
      "regions": 10,
      "sect_groups": 6,
      "techniques": 10,
      "weapons": 10,
      "auxiliaries": 10
    }
  },
  "stats": {
    "llm_count": 142,
    "fallback_count": 10,
    "elapsed_seconds": 93.2
  },
  "regions": {
    "305": {
      "name": "新地点名",
      "desc": "新地点描述"
    }
  },
  "sects": {},
  "techniques": {},
  "weapons": {},
  "auxiliaries": {}
}
```

读档时只需要按 v2 snapshot 应用当前文本。开发阶段不需要为旧 snapshot 增加复杂兼容路径。

## 配置

建议在 `static/config.yml` 增加：

```yaml
world_lore:
  rewrite_items: true
  total_timeout_seconds: 240
  task_timeout_seconds: 60
  min_retry_budget_seconds: 20
  max_parse_retries: 1
  max_transport_retries: 0
  chunk_size:
    regions: 10
    sect_groups: 6
    techniques: 10
    weapons: 10
    auxiliaries: 10
  desc_limits:
    region: [60, 120]
    sect: [80, 150]
    technique: [50, 110]
    weapon: [45, 100]
    auxiliary: [45, 100]
```

同时在 `llm.default_modes` 增加：

```yaml
llm:
  default_modes:
    world_lore_style_guide: "fast"
    world_lore_region_rewrite: "fast"
    world_lore_sect_group_rewrite: "fast"
    world_lore_technique_rewrite: "fast"
    world_lore_weapon_rewrite: "fast"
    world_lore_auxiliary_rewrite: "fast"
```

`max_concurrent_requests` 仍来自 LLM 设置，不在 `world_lore` 中重复配置。

## 初始化进度

初始化阶段仍可保留 `shaping_world_lore` 作为大 phase，但 runtime 应记录更细的世界观进度。

建议状态：

```json
{
  "phase": "shaping_world_lore",
  "world_lore": {
    "total_jobs": 24,
    "finished_jobs": 17,
    "failed_jobs": 1,
    "fallback_count": 3,
    "current": "rewriting techniques 30/62"
  }
}
```

至少日志必须包含：

```text
[WorldLore] style guide done
[WorldLore] planned jobs: regions=4 sect_groups=2 techniques=7 weapons=5 auxiliaries=4
[WorldLore] job techniques#3 done in 12.4s
[WorldLore] job weapons#2 parse failed, retrying
[WorldLore] job auxiliaries#1 timeout, fallback applied
[WorldLore] rewrite complete: llm=142 fallback=10 elapsed=93.2s
```

## 与 Step 的关系

世界观重写在开局初始化阶段执行，位于生成初始 NPC 和角色 profile 之前。

并发方面：

1. 所有 world lore jobs 共用全局 LLM semaphore。
2. 当前初始化顺序下，world lore 阶段通常不会与初始 backstory / long-term objective 并发抢 LLM。
3. 即便未来初始化阶段并行化，统一 semaphore 也能保护服务商并发额度。
4. 世界观重写不应在 `Simulator.step()` 中触发。
5. 读档时只应用 snapshot，不重新调用 LLM。

## 测试契约

需要补充或调整以下测试：

1. `test_world_lore_planner_uses_current_map`
   - 验证 planner 从 `world.map.regions` 构建 region 输入。
   - 验证不读取全局 region CSV 作为地图 prompt 主输入。
2. `test_world_lore_planner_includes_map_context`
   - 验证 `map_id`、`map_name`、`wilderness_tile`、`region_overrides`、`landmarks` 进入 context。
3. `test_world_lore_chunks_all_entities`
   - 验证所有 region、sect、technique、weapon、auxiliary 都被分配到 jobs。
4. `test_world_lore_runner_uses_global_llm_entrypoint`
   - mock `call_llm_with_task_name`，验证 jobs 通过统一 LLM 调用入口。
5. `test_world_lore_runner_limits_pending_window`
   - 验证本地 pending tasks 不超过 pending window。
6. `test_world_lore_validation_rejects_missing_ids`
   - LLM 少返回 id 时触发 retry 或 fallback。
7. `test_world_lore_validation_rejects_mechanics_text`
   - 输出包含明显数值加成或机制说明时被拒绝。
8. `test_world_lore_runner_applies_fallback_on_timeout`
   - 单 job 超时后最终 draft 仍包含该 job 全部实体。
9. `test_world_lore_total_timeout_fills_unfinished_jobs`
   - 总 timeout 到达后未完成 jobs 用 fallback 补齐。
10. `test_world_lore_apply_updates_indexes`
    - 宗门、功法、武器改名后 by-name index 正确更新。
11. `test_world_lore_snapshot_v2_roundtrip`
    - 保存读档后文本保持一致。
12. `test_world_lore_multi_map_uses_overrides`
    - 群岛或山脉地图的 region override 进入 prompt，并作为当前文本来源。
13. `test_init_world_lore_timeout_does_not_abort_initialization`
    - 世界观超时不导致初始化失败。

涉及地图上下文时，应结合 `docs/specs/region-first-map-system.md` 的约束，确保使用当前地图的 `region_rows` 派生结果、`wilderness_tile`、`landmarks` 和 `region_overrides`。

## 实施完成标准

实现完成后应满足：

1. 输入世界观后，地点、宗门、功法、兵器、辅助装备都有本局专属文本。
2. 当前选择不同地图时，世界观重写基于不同地图上下文。
3. 不再把全量 region CSV 作为地图重写主输入。
4. 不再要求 LLM 输出详细 thinking。
5. 单 chunk 超时和整体超时均可控。
6. JSON 格式错误最多重试一次。
7. 网络失败和超时不会中断初始化。
8. 失败 chunk 使用 fallback 补齐，最终 draft 完整。
9. apply 前后 indexes 和 ItemRegistry 保持一致。
10. 存档和读档通过 v2 snapshot 保留重写结果。
11. 日志能定位慢任务、失败任务和 fallback 数量。
