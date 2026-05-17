# 修行阶层别名系统设计说明

本文档描述“不同道统 / 种族使用不同阶层称呼”的设计方案。目标是在不破坏现有境界逻辑、存档、动作参数和外部 API 稳定性的前提下，让武道、儒道、佛道、妖族等体系拥有自己的修行称谓。

一句话原则：

> `Realm` 是世界底层秩序，阶层别名是角色所属体系下的显示语言。

## 1. 背景与目标

当前游戏底层修为体系由 `CultivationProgress.level` 推导：

- `QI_REFINEMENT`：练气
- `FOUNDATION_ESTABLISHMENT`：筑基
- `CORE_FORMATION`：金丹
- `NASCENT_SOUL`：元婴

每个大境界分：

- `EARLY_STAGE`：前期
- `MIDDLE_STAGE`：中期
- `LATE_STAGE`：后期

这套体系适合底层数值、突破、寿元、排行、物品品阶和动作限制，但在世界观表达上存在一个问题：

- 武道角色不一定应该自称“练气 / 筑基”。
- 儒道角色不一定应该自称“金丹 / 元婴”。
- 佛道、妖族也应有自己的修行话语。
- 玩家和 LLM 叙事中看到的称谓应体现所属体系，而不是所有人共用修仙标准名。

本功能目标：

1. 保留现有 `Realm` / `Stage` / `level` 作为唯一逻辑真源。
2. 新增按角色体系派生的显示别名。
3. 让角色详情、事件文本、LLM 上下文、世界信息可以使用风格化称呼。
4. 禁止别名进入存档、动作参数、物品配置和排序判断。
5. 为多语言翻译预留稳定结构，避免后续将中文别名硬编码到前端或 Python 逻辑中。

## 2. 非目标

本设计明确不做以下事情：

1. 不把 `Realm` 枚举值改成中文或别名。
2. 不让 `Realm.__str__()` 根据角色动态返回不同结果。
3. 不让动作参数接受所有自然语言别名作为主路径。
4. 不为每个道统建立一套独立升级曲线。
5. 不改变突破、寿元、战力、移动速度、排行分组、物品品阶等底层规则。
6. 不要求旧存档迁移出显示名，因为显示名可由当前配置重新派生。

## 3. 设计原则

### 3.1 ID 与显示名分离

所有跨模块契约优先使用稳定 ID：

- `realm_id`: `QI_REFINEMENT`
- `stage_id`: `EARLY_STAGE`
- `level`: `1`
- `profile_id`: `dao` / `sanxiu` / `wu` / `confucianism` / `buddhism` / `yao`

显示名只作为派生字段返回：

- `canonical_realm_name`: `练气`
- `canonical_stage_name`: `前期`
- `display_realm_name`: `淬体`
- `display_stage_name`: `初成`
- `display_full_name`: `淬体初成`

### 3.2 别名是角色上下文相关的

同样的 `Realm.Foundation_Establishment + Stage.Middle_Stage`，在不同角色身上可以显示为不同文本：

- 道家 / 散修：筑基中期
- 武道：易筋中成
- 儒道：明理中境
- 佛道：比丘中境
- 妖族：化形中期

因此别名解析函数必须接收角色或显式 profile，不允许只靠 `Realm` 自身决定。

### 3.3 逻辑层不读显示名

以下系统只能读 ID 或枚举，不得读别名：

- 存档 / 读档
- 动作参数解析
- `can_start` / `can_possibly_start`
- 物品、丹药、材料、秘境、宗门任务配置
- 排行榜分组
- 突破成功率
- 寿元效果
- 战力计算
- 移动距离
- 外部控制 API 的 command 请求

### 3.4 显示层可以自由使用别名

以下位置适合使用别名：

- 角色详情
- 角色卡片 / hover / 地图标记
- 关系列表里的对方修为
- 事件文本
- 小故事 prompt
- AI 决策上下文
- 扮演模式上下文
- World Info 说明
- Wiki / 帮助面板

但这些位置仍应同时保留标准 ID 或 canonical 名称，方便系统、玩家和外部 agent 理解“等价关系”。

## 4. 核心领域模型

### 4.1 标准境界仍是唯一逻辑真源

现有结构保持不变：

```python
class Realm(Enum):
    Qi_Refinement = "QI_REFINEMENT"
    Foundation_Establishment = "FOUNDATION_ESTABLISHMENT"
    Core_Formation = "CORE_FORMATION"
    Nascent_Soul = "NASCENT_SOUL"
```

`CultivationProgress.level` 继续通过 `REALM_ORDER` / `STAGE_ORDER` 推导当前境界和阶段。

### 4.2 新增显示 Profile

新增一个“阶层显示体系”概念，建议命名为 `CultivationAliasProfile` 或轻量字符串 `profile_id`。

初始 profile：

| profile_id | 来源 | 说明 |
|---|---|---|
| `dao` | 道家宗门 | 标准修仙称谓 |
| `sanxiu` | 散修 | 默认沿用标准修仙称谓 |
| `wu` | 武道 | 锻体、武学、宗师风格 |
| `confucianism` | 儒道 | 读书、养气、明理、立命风格 |
| `buddhism` | 佛道 | 沙弥、比丘、罗汉、菩萨风格 |
| `yao` | 妖族 | 开灵、化形、妖丹、妖王风格 |

### 4.3 Profile 选择规则

建议集中实现一个 resolver：

```python
def resolve_cultivation_alias_profile(avatar: Avatar) -> str:
    ...
```

初始推荐规则：

1. 若角色是妖族，优先使用 `yao`。
2. 否则若角色有 `orthodoxy.id`，使用对应道统 ID。
3. 否则回退到 `sanxiu`。
4. 若 profile 配置缺失，回退到 `dao`。

这里有一个世界观选择点：

- 方案 A：妖族永远使用妖族阶层名，即使加入人族宗门。
- 方案 B：妖族在加入特定人族宗门后，按宗门道统称谓显示。

本设计推荐先采用方案 A。原因是“妖族”在玩家认知中比宗门道统更强，且 AGENTS 规则中已将种族视为前后端 i18n 契约。若后续需要混合表达，可扩展为：

```text
妖族称谓：化形中期
宗门等价：筑基中期
```

## 5. 别名建议表

以下是中文风格建议。最终可在实现时通过配置和 i18n 微调。

### 5.1 道家 / 散修

道家和散修默认沿用现有标准名，降低玩家理解成本。

| realm_id | realm 别名 | stage 别名 |
|---|---|---|
| `QI_REFINEMENT` | 练气 | 前期 / 中期 / 后期 |
| `FOUNDATION_ESTABLISHMENT` | 筑基 | 前期 / 中期 / 后期 |
| `CORE_FORMATION` | 金丹 | 前期 / 中期 / 后期 |
| `NASCENT_SOUL` | 元婴 | 前期 / 中期 / 后期 |

### 5.2 武道

武道应体现肉身、筋骨、内劲、宗师感，不宜直接使用“气海 / 金丹”这类修仙器官词。

| realm_id | realm 别名 | 推荐完整阶段 |
|---|---|---|
| `QI_REFINEMENT` | 淬体 | 淬体初成 / 淬体中成 / 淬体大成 |
| `FOUNDATION_ESTABLISHMENT` | 易筋 | 易筋初成 / 易筋中成 / 易筋大成 |
| `CORE_FORMATION` | 宗师 | 宗师初境 / 宗师中境 / 宗师圆满 |
| `NASCENT_SOUL` | 武圣 | 武圣初境 / 武圣中境 / 武圣圆满 |

备选：

- `QI_REFINEMENT`: 炼体
- `FOUNDATION_ESTABLISHMENT`: 换血
- `CORE_FORMATION`: 大宗师
- `NASCENT_SOUL`: 武道圣者

当前推荐使用“淬体 / 易筋 / 宗师 / 武圣”，简洁、辨识度高，适合 UI 展示。

### 5.3 儒道

儒道应体现读书、养浩然气、明理、立命、圣贤秩序。不要直接照搬科举官阶，否则容易与王朝官职系统混淆。

| realm_id | realm 别名 | 推荐完整阶段 |
|---|---|---|
| `QI_REFINEMENT` | 养气 | 养气初境 / 养气中境 / 养气圆满 |
| `FOUNDATION_ESTABLISHMENT` | 明理 | 明理初境 / 明理中境 / 明理圆满 |
| `CORE_FORMATION` | 立命 | 立命初境 / 立命中境 / 立命圆满 |
| `NASCENT_SOUL` | 大儒 | 大儒初境 / 大儒中境 / 大儒圆满 |

备选：

- `QI_REFINEMENT`: 开蒙
- `FOUNDATION_ESTABLISHMENT`: 修身
- `CORE_FORMATION`: 正心
- `NASCENT_SOUL`: 圣贤

当前推荐使用“养气 / 明理 / 立命 / 大儒”，原因是它更像修行层级，不会和凡俗科举、官职直接重叠。

### 5.4 佛道

佛道应体现修戒、禅定、果位、慈悲与金身。注意不要让早期称谓过强。

| realm_id | realm 别名 | 推荐完整阶段 |
|---|---|---|
| `QI_REFINEMENT` | 沙弥 | 沙弥初境 / 沙弥中境 / 沙弥圆满 |
| `FOUNDATION_ESTABLISHMENT` | 比丘 | 比丘初境 / 比丘中境 / 比丘圆满 |
| `CORE_FORMATION` | 罗汉 | 罗汉初境 / 罗汉中境 / 罗汉圆满 |
| `NASCENT_SOUL` | 菩萨 | 菩萨初境 / 菩萨中境 / 菩萨圆满 |

备选：

- `QI_REFINEMENT`: 持戒
- `FOUNDATION_ESTABLISHMENT`: 入定
- `CORE_FORMATION`: 金身
- `NASCENT_SOUL`: 菩提

当前推荐“沙弥 / 比丘 / 罗汉 / 菩萨”，辨识度强，但要注意宗教术语在不同语言中的翻译一致性。

### 5.5 妖族

妖族应体现开智、化形、妖丹、妖王之路。它不是某个道统，而是种族修行称谓。

| realm_id | realm 别名 | 推荐完整阶段 |
|---|---|---|
| `QI_REFINEMENT` | 开灵 | 开灵初期 / 开灵中期 / 开灵后期 |
| `FOUNDATION_ESTABLISHMENT` | 化形 | 化形初期 / 化形中期 / 化形后期 |
| `CORE_FORMATION` | 妖丹 | 妖丹初期 / 妖丹中期 / 妖丹后期 |
| `NASCENT_SOUL` | 妖王 | 妖王初期 / 妖王中期 / 妖王后期 |

备选：

- `QI_REFINEMENT`: 启灵
- `FOUNDATION_ESTABLISHMENT`: 炼形
- `CORE_FORMATION`: 凝丹
- `NASCENT_SOUL`: 大妖

当前推荐“开灵 / 化形 / 妖丹 / 妖王”，信息密度高，玩家易懂。

## 6. 数据配置设计

### 6.1 推荐新增配置文件

建议新增：

- `static/game_configs/cultivation_alias.csv`

推荐字段：

```csv
profile_id,realm_id,stage_id,realm_name_id,stage_name_id,full_name_id,sort_order
```

字段含义：

| 字段 | 说明 |
|---|---|
| `profile_id` | 显示体系 ID，如 `wu`、`yao` |
| `realm_id` | 标准境界 ID |
| `stage_id` | 标准阶段 ID，可为空表示该行仅定义大境界名 |
| `realm_name_id` | 大境界显示名 i18n key |
| `stage_name_id` | 阶段显示名 i18n key |
| `full_name_id` | 完整显示名 i18n key，允许覆盖 `{realm}{stage}` 拼接 |
| `sort_order` | 可选，仅用于 wiki / 配置展示 |

### 6.2 为什么允许 full_name_id

不同体系的阶段拼接不一定都适合“境界 + 前中后”。

例如：

- 道家：筑基中期，适合拼接。
- 武道：宗师中境，比“宗师中期”更有味道。
- 儒道：养气圆满，比“养气后期”更适合儒道语感。
- 英文：`Middle Tendon-Tempering` 可能比 `Tendon-Tempering Middle Stage` 更自然，取决于目标语言。

因此规则应是：

1. 若存在 `full_name_id`，优先使用完整翻译。
2. 否则使用 `{realm_name}{stage_name}` 或按 locale 配置的模板拼接。

### 6.3 i18n key 命名建议

建议新增模块：

- `static/locales/<lang>/modules/cultivation_alias.po`

key 示例：

```po
msgid "cultivation_alias.profile.wu"
msgstr "武道"

msgid "cultivation_alias.wu.realm.qi_refinement"
msgstr "淬体"

msgid "cultivation_alias.wu.stage.early"
msgstr "初成"

msgid "cultivation_alias.wu.full.qi_refinement.early"
msgstr "淬体初成"
```

注意：

- `.po` 的 `msgid` 不得直接使用中文。
- 中文只能放在 `msgstr`。
- 日常开发默认 Phase 1 可只补 `zh-CN`，但若明确进入 Phase 2，应按 `static/locales/registry.json` 补齐启用语言。

## 7. 后端服务设计

### 7.1 新增显示构造服务

建议新增：

- `src/systems/cultivation_display.py`

核心函数：

```python
def build_cultivation_display(
    cultivation_progress: CultivationProgress,
    *,
    profile_id: str,
) -> dict[str, Any]:
    ...

def build_avatar_cultivation_display(avatar: Avatar) -> dict[str, Any]:
    ...
```

返回结构：

```json
{
  "profile_id": "wu",
  "profile_name": "武道",
  "realm_id": "FOUNDATION_ESTABLISHMENT",
  "stage_id": "MIDDLE_STAGE",
  "level": 42,
  "canonical_realm_name": "筑基",
  "canonical_stage_name": "中期",
  "canonical_full_name": "筑基中期",
  "display_realm_name": "易筋",
  "display_stage_name": "中成",
  "display_full_name": "易筋中成"
}
```

### 7.2 与 `CultivationProgress` 的边界

`CultivationProgress` 继续只负责：

- `level`
- `exp`
- `realm`
- `stage`
- 突破
- 经验
- 境界效果

不要把 avatar、race、orthodoxy 引入 `CultivationProgress`。  
显示别名是外部 presentation/service 层职责。

### 7.3 `Realm.__str__()` 不改为动态别名

`Realm.__str__()` 仍返回当前 locale 下的标准名，例如“筑基”。  
这是全局 canonical name，不是角色显示名。

若业务需要别名，必须显式调用：

```python
build_avatar_cultivation_display(avatar)["display_full_name"]
```

## 8. API / DTO 设计

### 8.1 角色详情

在 avatar detail 中新增结构化字段：

```json
{
  "realm": "筑基 中期",
  "realm_id": "FOUNDATION_ESTABLISHMENT",
  "level": 42,
  "cultivation": {
    "profile_id": "wu",
    "profile_name": "武道",
    "realm_id": "FOUNDATION_ESTABLISHMENT",
    "stage_id": "MIDDLE_STAGE",
    "level": 42,
    "canonical_full_name": "筑基中期",
    "display_full_name": "易筋中成"
  }
}
```

说明：

- `realm` 暂时保留，避免前端一次性大迁移。
- 新代码优先读 `cultivation.display_full_name`。
- 需要筛选、排序、传参时读 `realm_id` / `stage_id` / `level`。

### 8.2 世界状态与 websocket

地图头像列表、tick update 当前可以继续返回 `realm` 为标准 ID：

```json
{
  "realm": "FOUNDATION_ESTABLISHMENT"
}
```

若前端需要在卡片上直接显示别名，可增量返回：

```json
{
  "realm": "FOUNDATION_ESTABLISHMENT",
  "cultivation_display": "易筋中成"
}
```

不建议把原字段 `realm` 改成别名。

### 8.3 外部控制 API

外部 agent / Claw 集成需要稳定契约：

- query 可以返回别名作为辅助字段。
- command 必须继续接受标准 ID。
- 文档中应明确 `display_full_name` 不可作为命令参数。

示例：

```json
{
  "realm_id": "CORE_FORMATION",
  "display_full_name": "罗汉圆满",
  "canonical_full_name": "金丹后期"
}
```

若外部 agent 要创建物品或选择目标境界，应传：

```json
{
  "realm": "CORE_FORMATION"
}
```

而不是：

```json
{
  "realm": "罗汉"
}
```

## 9. 前端设计

### 9.1 类型

在 `web/src/types/core.ts` 中为 `AvatarDetail` 增加：

```ts
interface CultivationDisplay {
  profile_id: string
  profile_name: string
  realm_id: string
  stage_id: string
  level: number
  canonical_realm_name: string
  canonical_stage_name: string
  canonical_full_name: string
  display_realm_name: string
  display_stage_name: string
  display_full_name: string
}
```

`AvatarDetail`：

```ts
cultivation?: CultivationDisplay
```

### 9.2 展示优先级

前端展示时建议：

1. 有 `cultivation.display_full_name`：显示别名。
2. 有 `cultivation.canonical_full_name`：可作为 tooltip 或副文本。
3. 只有旧字段 `realm`：走现有 `formatCultivationText`。

角色详情页推荐显示：

```text
易筋中成
等价：筑基中期
```

紧凑卡片可只显示：

```text
易筋中成
```

筛选、颜色、排序继续使用 `realm_id` 或 `level`。

### 9.3 不再扩大前端 alias map

`web/src/utils/cultivationText.ts` 当前维护标准境界 alias map。  
后续不应把所有武道、儒道、佛道、妖族别名继续塞进这个 map。

原因：

- 这是显示派生，不是前端解析真源。
- 多语言下别名会膨胀。
- 同一个别名可能在不同 profile 中含义不同。

新 UI 应优先消费后端结构化 DTO。

## 10. LLM 上下文设计

LLM 既需要风味称谓，也需要标准等价关系。  
推荐上下文结构：

```json
{
  "cultivation": {
    "display": "易筋中成",
    "canonical": "筑基中期",
    "realm_id": "FOUNDATION_ESTABLISHMENT",
    "stage_id": "MIDDLE_STAGE",
    "profile_id": "wu"
  }
}
```

Prompt 中可明确：

```text
该角色属于武道体系，当前阶层称作“易筋中成”，等价标准境界为“筑基中期”。
叙事可以使用“易筋中成”，但动作参数、物品品阶、目标境界必须使用标准 realm_id。
```

这能避免 LLM 在行动规划中输出：

```json
{"target_realm": "易筋"}
```

而应输出：

```json
{"target_realm": "FOUNDATION_ESTABLISHMENT"}
```

## 11. World Info 设计

### 11.1 新增一条世界信息

应在 `static/game_configs/world_info.csv` 中新增一条，解释不同道统 / 种族阶层别名之间的等价关系。

建议条目：

```csv
阶层别名,WORLD_INFO_CULTIVATION_ALIAS_TITLE,WORLD_INFO_CULTIVATION_ALIAS_NAME,WORLD_INFO_CULTIVATION_ALIAS_DESC,同一修行阶层在不同体系中有各自名目：道家与散修为练气、筑基、金丹、元婴；武道为淬体、易筋、宗师、武圣；儒道为养气、明理、立命、大儒；佛道为沙弥、比丘、罗汉、菩萨；妖族为开灵、化形、妖丹、妖王。它们彼此对应的是同一套底层境界序列，只改变叙事与界面称谓，不改变突破、战力、寿元、物品品阶等规则。
```

### 11.2 World Info 的作用

这条信息同时服务三类用户：

1. 玩家：理解为什么同等级角色显示不同称谓。
2. LLM：在故事、目标、称号生成时知道别名不是独立升级线。
3. 外部 agent：理解 display name 与 canonical realm 的关系。

### 11.3 多语言同步

由于 `world_info.csv` 已由前端读取，并通过 `game_configs_modules/world_info.po` / 前端 locale namespace 翻译，新增条目时需要同步：

- `static/locales/zh-CN/game_configs_modules/world_info.po`
- Phase 2 时同步 `en-US`、`zh-TW`、`vi-VN`、`ja-JP` 等启用语言
- 前端 `web/src/locales/<lang>/world_info.json`
- 运行 `python tools/i18n/build_mo.py`
- 覆盖 `tests/test_frontend_locales.py` / `tests/test_backend_locales.py` 相关检查

日常 Phase 1 若只落中文，也不能在非中文 locale 中用中文 `msgstr` 伪装翻译。

## 12. 多语言翻译策略

修仙风格词汇不是普通 UI 翻译，不能只做逐字直译。翻译策略应按语言分别设计。

### 12.1 总体策略

每个 locale 应同时保留两层信息：

1. **风味称谓**：尽量让目标语言玩家读起来像一种修行体系。
2. **标准等价**：必要时显示 canonical 或 tooltip，避免玩家不知道它对应哪个强度等级。

推荐 UI：

```text
易筋中成（筑基中期）
```

英文：

```text
Tendon-Tempering, Mid Attainment (Foundation Establishment)
```

日文：

```text
易筋・中成（築基中期）
```

越南文：

```text
Dịch Cân trung thành (Trúc Cơ trung kỳ)
```

### 12.2 zh-CN

中文简体是源风格语言，应优先保证韵味和简洁。

原则：

- 道家 / 散修沿用现有修仙标准名。
- 武道使用偏武侠和肉身修炼的词。
- 儒道使用“养气、明理、立命、大儒”这类文气词。
- 佛道使用大众可识别的佛门层级。
- 妖族使用“开灵、化形、妖丹、妖王”这类玄幻常见词。

不建议：

- 把儒道翻成“童生、秀才、举人、进士”，会与王朝 / 官职 / 科举想象强绑定。
- 把佛道早期叫“佛陀”或“菩提”，早期称谓过强。
- 把武道全称写得过长，地图和卡片会拥挤。

### 12.3 zh-TW

繁体中文应尽量保留中文修仙语感，但做字形和常用词差异处理。

建议：

- 练气 -> 練氣
- 筑基 -> 築基
- 金丹 -> 金丹
- 元婴 -> 元嬰
- 淬体 -> 淬體
- 易筋 -> 易筋
- 宗师 -> 宗師
- 武圣 -> 武聖
- 养气 -> 養氣
- 明理 -> 明理
- 立命 -> 立命
- 大儒 -> 大儒
- 沙弥 -> 沙彌
- 比丘 -> 比丘
- 罗汉 -> 羅漢
- 菩萨 -> 菩薩
- 开灵 -> 開靈
- 化形 -> 化形
- 妖丹 -> 妖丹
- 妖王 -> 妖王

阶段：

- 初成 / 中成 / 大成 可转为 初成 / 中成 / 大成
- 初境 / 中境 / 圓滿
- 前期 / 中期 / 後期

### 12.4 en-US

英文不宜机械音译所有词，否则可读性会很差；也不宜全部意译成普通 fantasy rank，否则会丢掉修仙风味。推荐“关键体系意译 + 必要术语保留”的混合策略。

标准修仙：

| zh-CN | en-US 推荐 |
|---|---|
| 练气 | Qi Refinement |
| 筑基 | Foundation Establishment |
| 金丹 | Core Formation |
| 元婴 | Nascent Soul |

武道：

| zh-CN | en-US 推荐 |
|---|---|
| 淬体 | Body Tempering |
| 易筋 | Tendon-Tempering |
| 宗师 | Martial Master |
| 武圣 | Martial Saint |

儒道：

| zh-CN | en-US 推荐 |
|---|---|
| 养气 | Vital Qi Cultivation |
| 明理 | Principle Illumination |
| 立命 | Mandate Establishment |
| 大儒 | Great Scholar |

佛道：

| zh-CN | en-US 推荐 |
|---|---|
| 沙弥 | Novice Monk |
| 比丘 | Monk |
| 罗汉 | Arhat |
| 菩萨 | Bodhisattva |

妖族：

| zh-CN | en-US 推荐 |
|---|---|
| 开灵 | Spirit Awakening |
| 化形 | Form Transformation |
| 妖丹 | Demon Core |
| 妖王 | Demon King |

阶段：

| zh-CN | en-US 推荐 |
|---|---|
| 前期 | Early Stage |
| 中期 | Middle Stage |
| 后期 | Late Stage |
| 初成 | Initial Attainment |
| 中成 | Mid Attainment |
| 大成 | Great Attainment |
| 初境 | Early Realm |
| 中境 | Middle Realm |
| 圆满 | Completion |

英文 UI 建议优先用完整配置 `full_name_id`，因为英文语序不一定适合中文式直接拼接。

示例：

- `Body Tempering, Initial Attainment`
- `Tendon-Tempering, Mid Attainment`
- `Martial Saint, Completion`
- `Arhat, Middle Realm`

### 12.5 ja-JP

日文可以大量保留汉字词，辅以日式阶段词。不要全部片假名化。

标准修仙：

| zh-CN | ja-JP 推荐 |
|---|---|
| 练气 | 練気 |
| 筑基 | 築基 |
| 金丹 | 金丹 |
| 元婴 | 元嬰 |

武道：

| zh-CN | ja-JP 推荐 |
|---|---|
| 淬体 | 鍛体 |
| 易筋 | 易筋 |
| 宗师 | 宗師 |
| 武圣 | 武聖 |

儒道：

| zh-CN | ja-JP 推荐 |
|---|---|
| 养气 | 養気 |
| 明理 | 明理 |
| 立命 | 立命 |
| 大儒 | 大儒 |

佛道：

| zh-CN | ja-JP 推荐 |
|---|---|
| 沙弥 | 沙弥 |
| 比丘 | 比丘 |
| 罗汉 | 羅漢 |
| 菩萨 | 菩薩 |

妖族：

| zh-CN | ja-JP 推荐 |
|---|---|
| 开灵 | 開霊 |
| 化形 | 化形 |
| 妖丹 | 妖丹 |
| 妖王 | 妖王 |

阶段：

- 前期 / 中期 / 後期
- 初成 / 中成 / 大成
- 初境 / 中境 / 円満

示例：

- `鍛体初成`
- `易筋中成`
- `宗師円満`
- `開霊前期`

### 12.6 vi-VN

越南文可采用“汉越词 + 少量解释性词”的策略。若全部意译，修仙风格会变淡；若全部保留汉越词，玩家可能需要等价提示。

标准修仙：

| zh-CN | vi-VN 推荐 |
|---|---|
| 练气 | Luyện Khí |
| 筑基 | Trúc Cơ |
| 金丹 | Kim Đan |
| 元婴 | Nguyên Anh |

武道：

| zh-CN | vi-VN 推荐 |
|---|---|
| 淬体 | Thối Thể |
| 易筋 | Dịch Cân |
| 宗师 | Tông Sư |
| 武圣 | Võ Thánh |

儒道：

| zh-CN | vi-VN 推荐 |
|---|---|
| 养气 | Dưỡng Khí |
| 明理 | Minh Lý |
| 立命 | Lập Mệnh |
| 大儒 | Đại Nho |

佛道：

| zh-CN | vi-VN 推荐 |
|---|---|
| 沙弥 | Sa Di |
| 比丘 | Tỳ Kheo |
| 罗汉 | La Hán |
| 菩萨 | Bồ Tát |

妖族：

| zh-CN | vi-VN 推荐 |
|---|---|
| 开灵 | Khai Linh |
| 化形 | Hóa Hình |
| 妖丹 | Yêu Đan |
| 妖王 | Yêu Vương |

阶段：

- sơ kỳ / trung kỳ / hậu kỳ
- sơ thành / trung thành / đại thành
- sơ cảnh / trung cảnh / viên mãn

示例：

- `Thối Thể sơ thành`
- `Dịch Cân trung thành`
- `La Hán viên mãn`
- `Yêu Đan trung kỳ`

### 12.7 缺译策略

若某 locale 缺少别名翻译：

1. 优先回退到该 locale 的 canonical realm/stage。
2. 再回退到 `en-US`。
3. 最后才回退到 ID。

不要回退到中文，除非当前 locale 是中文系。

## 13. 存档与兼容

存档只保存：

- `level`
- `exp`
- 当前已有的 `realm` / `stage` 枚举信息
- 角色 `race_id`
- 宗门 / orthodoxy 关系

不保存：

- `display_realm_name`
- `display_stage_name`
- `display_full_name`
- `profile_name`

原因：

- 显示名是配置和 locale 的派生结果。
- 用户切换语言后应重新显示目标语言。
- 后续修改别名表后，旧存档应自动使用新显示名。

## 14. 测试策略

### 14.1 后端单元测试

新增测试建议：

- `tests/test_cultivation_display.py`

覆盖：

1. 同一个 `level` 在不同 profile 下返回不同 `display_full_name`。
2. `realm_id` / `stage_id` 始终是标准 ID。
3. 妖族角色优先使用 `yao` profile。
4. 人族宗门成员按 `orthodoxy.id` 使用 profile。
5. 缺失 profile 时回退到 `dao` 或 canonical。
6. `CultivationProgress` 本体不依赖 avatar / orthodoxy / race。

### 14.2 API 测试

覆盖：

1. Avatar detail 返回 `cultivation` 结构。
2. `realm_id` 与 `cultivation.realm_id` 一致。
3. 旧字段 `realm` 暂时仍存在。
4. 外部 query 返回别名但 command 参数仍要求标准 ID。

### 14.3 动作参数测试

覆盖：

1. `param_options.target_realm.value` 仍为 `Realm.value`。
2. `param_options.target_realm.id` 仍为 `Realm.value`。
3. `can_start("FOUNDATION_ESTABLISHMENT")` 仍成功。
4. 不要求 `can_start("易筋")` 成为主路径。

### 14.4 前端测试

覆盖：

1. 角色详情优先显示 `cultivation.display_full_name`。
2. tooltip / 副文本可显示 `canonical_full_name`。
3. 缺少 `cultivation` 时回退到现有 `formatCultivationText`。
4. 类型定义不使用 `any`。

### 14.5 i18n 测试

覆盖：

1. `zh-CN` 的 `cultivation_alias.po` key 完整。
2. 新增 world info 条目在前端 locale namespace 中存在。
3. Phase 2 时所有启用 locale 不得用中文 `msgstr` 伪装翻译。
4. 编译 `.mo` 后后端可读。

## 15. 推荐落地顺序

### 第一期：结构化显示

1. 新增 `cultivation_alias.csv`。
2. 新增 `cultivation_alias.po` 的 `zh-CN` 条目。
3. 新增 `src/systems/cultivation_display.py`。
4. Avatar detail 增加 `cultivation` 结构。
5. 角色详情页显示别名，保留 canonical 作为副文本。
6. 新增 world info 条目，解释等价关系。
7. 补后端 display 测试和前端详情测试。

### 第二期：叙事接入

1. AI 决策上下文加入 `cultivation` 结构。
2. 小故事 / roleplay / nickname / long-term objective prompt 可使用 display + canonical。
3. 事件文本中角色修为优先使用 display。
4. LLM prompt 明确“动作参数使用 realm_id”。

### 第三期：全局展示入口

1. 地图卡片 / hover 使用 display。
2. 关系列表使用 display。
3. 排行榜显示 display，但分组仍按 `Realm`。
4. 前端逐步减少对 `formatCultivationText` 的新依赖。
5. 外部 API 文档补充 display/canonical 语义。

## 16. 风险与规避

### 16.1 风险：显示名被误用为逻辑值

规避：

- DTO 同时返回 `realm_id` 和 `display_full_name`。
- command 参数文档明确只接受 ID。
- 测试确保 `param_options.value` 是 ID。

### 16.2 风险：LLM 输出别名导致动作失败

规避：

- LLM 上下文同时给 display 和 realm_id。
- prompt 明确动作参数必须使用 `realm_id`。
- 动作层不扩大自然语言别名解析主路径。

### 16.3 风险：多语言风格不一致

规避：

- 使用 `full_name_id`，不要强依赖拼接。
- 各 locale 单独设计术语表。
- 非中文 locale 不得直接复制中文。

### 16.4 风险：前端继续靠字符串猜境界

规避：

- 新增结构化 `cultivation` 类型。
- 新 UI 优先读结构化字段。
- `formatCultivationText` 仅作为旧数据兜底。

### 16.5 风险：妖族和宗门道统冲突

规避：

- 一期明确妖族优先。
- 如后续需要，可在 UI 中显示“妖族称谓 + 宗门等价”。

## 17. 开发守则摘要

1. 新增显示别名，不改 `Realm` 枚举值。
2. 不让 `Realm.__str__()` 依赖 avatar。
3. 别名不进存档。
4. 动作参数继续使用 `Realm.value`。
5. API 新增结构化字段，不把旧 `realm` 字段改成别名。
6. LLM 上下文同时给 display 和 canonical。
7. World Info 必须解释别名等价关系。
8. 多语言翻译应按修仙风格设计，不做机械直译。
9. 前端不继续扩大境界 alias map。
10. 测试必须覆盖“别名显示变化但底层 ID 不变”。
