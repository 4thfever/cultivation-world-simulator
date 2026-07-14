# 背景板 NPC / 凡人场景系统设计说明

本文档描述“背景板 NPC”一期设计。这里的 NPC 不是 `Avatar`，也不是会长期存在的世界实体，而是用于填充世界烟火气的无名凡人画像与预写场景事件。

一期目标是用低成本、配置驱动的方式，让城市、港口、山岭、宗门山下、官府、坊市等场景里出现凡俗生活的回声，同时允许不同身份的 Avatar 遇到不同凡人片段。系统不调用在线 LLM，不改变世界状态，不引入 NPC 生命周期。

## 1. 目标

背景板 NPC 系统解决三个问题：

1. 让世界不只由 Avatar 之间的慢速 LLM 互动构成，也有低成本的凡俗背景事件。
2. 让 Avatar 的种族、阵营、境界、宗门身份、官职等能被凡人世界“看见”，但不改变数值。
3. 让部分 Avatar 小事和行动结果能附带一条凡人反馈，增强修仙者压过人间的叙事感。

一期的标准体验是：

- 城市里有药材商、药铺伙计、茶馆说书人、巡街差役等无名职业剪影。
- 港口里有船老大、水手、潮汐引路人、港口税吏等无名职业剪影。
- 宗门山下有山门守童、外门杂役、求仙父母、采买人等无名职业剪影。
- 妖族、邪道、高境界修士、有官职者、宗门弟子等遇到的凡人反应可以不同。
- 背景板 NPC 不产生关系、不进存档、不成为可对话实体。

## 2. 设计原则

### 2.1 背景板 NPC 不是 Avatar

背景板 NPC 一期不进入：

1. `AvatarManager`
2. 行动系统
3. 关系系统
4. 宗门成员系统
5. 死亡、年龄、背包、境界、位置等实体生命周期

它们只作为“画像 + 预写事件模板”的配置素材存在。

### 2.2 所有背景 NPC 都无名

一期禁止给背景板 NPC 起具体姓名。

推荐写法：

- `药材商`
- `茶棚老人`
- `驿卒`
- `山门守童`
- `船老大`
- `更夫`
- `黑市掮客`
- `几个码头脚夫`
- `年老的采药人`
- `守在山门外的童子`

不推荐写法：

- `老陈头`
- `赵账房`
- `柳掌柜`
- `某某船老大`

原因是一期不支持二次出场。职业身份重复是合理的，具体姓名重复会让玩家误以为同一个人反复出现。

### 2.3 只做背景，不改变状态

一期背景板 NPC 事件不应直接改变：

1. Avatar 属性、资源、关系、行动计划
2. 城市人口、经济、商品、治安
3. 宗门收入、关系、战争、库存
4. 朝廷、官府、地图、POI、机缘、秘境等世界状态

所有事件只生成 `Event`。

可以预留配置字段表达未来效果，但一期 loader / service 不执行这些字段。

### 2.4 不在线调用 LLM

事件正文全部使用预写模板。运行时只做：

1. 条件过滤
2. 权重抽样
3. 变量替换
4. 生成 `Event`

开发期可以用 AI 批量生成候选文本，但最终进入游戏的内容必须落到配置和 locale 源文件中。

### 2.5 画像和事件分离

一个背景板 NPC 画像可以绑定多个不同事件。画像负责“谁会出现”，事件负责“出现时演哪一幕”。

例如：

- `herb_vendor` 药材商
  - 城市集市验货争执
  - Avatar 买药时掌柜收起凡药
  - 妖族经过时摊主压低声音
  - 高境界修士问价时只展示玉盒灵材

画像不持有运行时状态，事件也不承诺同一个 NPC 会再次出现。

## 3. 非目标

一期明确不做以下内容：

1. 不做 NPC 二次出场。
2. 不做 NPC 对话对象。
3. 不做 NPC 关系、好感、仇怨。
4. 不做 NPC 长期记忆。
5. 不做 NPC 名册。
6. 不做城市或宗门内部 NPC 人口模拟。
7. 不做经济、治安、人口、宗门收入等数值影响。
8. 不把背景 NPC 加入 Avatar AI 可观察对象列表。
9. 不让背景 NPC 进入存档。
10. 不新增玩家任务、导航、POI 或可点击目标。

## 4. 事件类型

一期支持三种触发语义。

### 4.1 `region_tick`

地区自然发生的背景事件，不绑定具体 Avatar。

示例：

```text
城中药材商和采药人为一捆草药年份争执半日，药铺伙计请来掌柜验货，围观的人群才慢慢散去。
```

事件语义：

- `related_avatars=None`
- `related_sects` 可选
- `is_major=False`
- `is_story=False`
- `event_type="background_npc"`

### 4.2 `avatar_witness`

Avatar 在某地停留、经过或满足身份条件时见到的凡人片段。

示例：

```text
{avatar_name}经过药铺门前时，伙计把柜台擦了又擦，始终不敢催促。
```

事件语义：

- `related_avatars=[avatar.id]`
- `is_major=False`
- `is_story=False`
- `event_type="background_npc"`

### 4.3 `action_echo`

Avatar 完成某些行动后追加的凡人反馈，不改变行动结算。

示例：

```text
{avatar_name}离开后，医馆大夫把剩下的止血散送到粥棚，几个流民在廊下低声道谢。
```

适合优先接入的行动：

- `Buy`
- `Sell`
- `Govern`
- `HelpPeople`
- `PlunderPeople`
- `EatMortals`
- `DevourPeople`
- `SectMission`
- `MoveToRegion`

事件语义：

- `related_avatars=[avatar.id]`
- `is_major=False`
- `is_story=False`
- `event_type="background_npc"`

## 5. 配置总览

一期推荐三张配置表：

1. `static/game_configs/background_npc_profile.csv`
2. `static/game_configs/background_npc_event.csv`
3. `static/game_configs/background_npc_region_binding.csv`

其中：

- profile 表定义无名职业画像。
- event 表定义一个画像可触发的多个事件。
- region binding 表把地图 region 绑定到场景标签，避免事件硬写具体 region。

所有用户可见文本都应通过 `*_id` 指向 locale 条目。CSV 可以保留中文备注列用于维护，但运行时不应依赖备注列作为用户可见文案真源。

新增 locale 源文件建议：

```text
static/locales/<lang>/game_configs_modules/background_npc_profile.po
static/locales/<lang>/game_configs_modules/background_npc_event.po
```

日常开发默认 Phase 1，只维护 `zh-CN`。正式多语言补全时再按 `static/locales/registry.json` 补齐启用语言。

## 6. Profile 表

`background_npc_profile.csv` 定义背景板 NPC 画像。

建议字段：

```csv
id,profile_key,role_label_id,category,default_scene_tags,comment
1,herb_vendor,BACKGROUND_NPC_ROLE_HERB_VENDOR,city_market,city_market|medicine,药材商
2,storyteller,BACKGROUND_NPC_ROLE_STORYTELLER,city_market,city_market|rumor|teahouse,茶馆说书人
3,tide_guide,BACKGROUND_NPC_ROLE_TIDE_GUIDE,port,port|tide|sea_trade,潮汐引路人
4,sect_gate_child,BACKGROUND_NPC_ROLE_SECT_GATE_CHILD,sect_edge,sect_edge|pilgrimage,山门守童
```

字段说明：

1. `id`：数字 ID，仅用于配置引用。
2. `profile_key`：稳定 key，推荐业务代码、测试、工具优先使用。
3. `role_label_id`：职业称谓 i18n key。
4. `category`：画像粗分类，例如 `city_market`、`port`、`mountain_frontier`、`sect_edge`、`official_order`、`black_market`。
5. `default_scene_tags`：画像天然适配的场景标签，使用 `|` 分隔。
6. `comment`：维护备注，不作为运行时用户可见文本。

画像层只描述“这类人是谁”。不要在 profile 中写事件正文。

### 6.1 画像命名约定

`profile_key` 使用英文 snake_case，避免中文 key：

- `herb_vendor`
- `inn_keeper`
- `yamen_clerk`
- `dock_laborer`
- `mountain_hunter`
- `sect_errand_servant`

`role_label_id` 使用稳定英文 key：

- `BACKGROUND_NPC_ROLE_HERB_VENDOR`
- `BACKGROUND_NPC_ROLE_INN_KEEPER`
- `BACKGROUND_NPC_ROLE_YAMEN_CLERK`

对应 zh-CN `.po`：

```po
msgid "BACKGROUND_NPC_ROLE_HERB_VENDOR"
msgstr "药材商"
```

## 7. Event 表

`background_npc_event.csv` 定义具体事件。一个 `profile_key` 可以绑定多条事件。

建议字段：

```csv
id,event_key,profile_key,trigger_kind,region_types,required_tags,excluded_tags,map_ids,avatar_filters,action_keys,weight,cooldown_months,max_per_month,text_id,comment
1,herb_vendor_market_argument,herb_vendor,region_tick,city,city_market|medicine,, , , ,1.0,24,1,BACKGROUND_NPC_EVENT_HERB_VENDOR_MARKET_ARGUMENT,药材年份争执
2,herb_vendor_avatar_buy_echo,herb_vendor,action_echo,city,medicine,, , ,Buy,1.0,12,1,BACKGROUND_NPC_EVENT_HERB_VENDOR_AVATAR_BUY_ECHO,买药回声
3,market_reacts_to_yao,herb_vendor,avatar_witness,city,city_market,, ,race=yao, ,1.0,12,1,BACKGROUND_NPC_EVENT_MARKET_REACTS_TO_YAO,妖族经过市集
```

字段说明：

1. `id`：数字 ID。
2. `event_key`：稳定事件 key。
3. `profile_key`：引用 `background_npc_profile.csv`。
4. `trigger_kind`：`region_tick`、`avatar_witness`、`action_echo`。
5. `region_types`：粗筛 region 类型，使用 `|` 分隔；可选值按运行时 region type，例如 `city`、`sect`、`normal`、`cultivate`。
6. `required_tags`：必须匹配的场景标签，使用 `|` 分隔。
7. `excluded_tags`：排除标签，使用 `|` 分隔。
8. `map_ids`：限定地图，使用 `|` 分隔；空表示所有地图。
9. `avatar_filters`：Avatar 身份条件；空表示不限。
10. `action_keys`：`action_echo` 使用，允许多个行动 key，使用 `|` 分隔；其他触发类型为空。
11. `weight`：权重。
12. `cooldown_months`：同一 `event_key` 冷却月数。
13. `max_per_month`：同一事件每月最多出现次数，通常为 `1`。
14. `text_id`：事件正文 i18n key。
15. `comment`：维护备注。

### 7.1 文本 i18n

事件正文不直接写在主 CSV 的运行字段中，统一放到 locale `.po`。

示例：

```po
#. background_npc_event.csv: 药材年份争执
msgid "BACKGROUND_NPC_EVENT_HERB_VENDOR_MARKET_ARGUMENT"
msgstr "城中药材商和采药人为一捆草药年份争执半日，药铺伙计请来掌柜验货，围观的人群才慢慢散去。"

#. background_npc_event.csv: 买药回声
msgid "BACKGROUND_NPC_EVENT_HERB_VENDOR_AVATAR_BUY_ECHO"
msgstr "{avatar_name}挑选灵材时，药铺伙计把柜台擦了又擦，始终不敢催促。"
```

`msgid` 必须是稳定英文 key，不得直接使用中文。中文只放在 `msgstr`。

### 7.2 可用模板变量

一期建议只支持少量稳定变量：

1. `{avatar_name}`
2. `{region_name}`
3. `{sect_name}`
4. `{dynasty_title}`
5. `{npc_role}`

变量来源：

- `{avatar_name}`：当前 Avatar。
- `{region_name}`：触发 region 展示名，优先使用地图 `region_overrides` 后的名称。
- `{sect_name}`：region 或 Avatar 关联宗门名；无值时该事件不应入选，除非文本不使用此变量。
- `{dynasty_title}`：当前王朝称号；无王朝时该事件不应入选，除非文本不使用此变量。
- `{npc_role}`：`role_label_id` 本地化结果。

不建议一期允许任意 Python 表达式或复杂条件替换。

## 8. Region Binding 表

`background_npc_region_binding.csv` 用于把具体地图和 region 映射到场景标签。

推荐字段：

```csv
id,map_id,region_id,scene_tags,comment
1,classic,301,city_market|medicine|official_order,青云城
2,classic,304,port|river_trade|sea_trade,沧澜城
3,island_seas,305,port|sea_trade|shipyard,海岛港城
4,mountain_frontier,305,mountain_pass|mining|frontier,山岭边城
```

字段说明：

1. `id`：数字 ID。
2. `map_id`：地图 ID，必须对应 `static/game_configs/maps/<map_id>`。
3. `region_id`：region ID，必须存在于对应地图 `region_rows` 或 region 配置中。
4. `scene_tags`：该 region 具备的场景标签。
5. `comment`：维护备注。

这样事件不需要硬绑 `region_id`。同一事件可以在所有带 `medicine` 的城市出现，也可以用 `map_ids` 限定只在海岛或山岭地图出现。

### 8.1 默认标签

若某个 region 没有 binding 记录，可以从 region 类型推导基础标签：

- `city` -> `city`
- `sect` -> `sect|sect_edge`
- `normal` -> `wild`
- `cultivate` -> `cultivate`

但细分标签必须显式配置，例如：

- `port`
- `medicine`
- `black_market`
- `mountain_pass`
- `mining`
- `official_order`
- `teahouse`
- `pilgrimage`

## 9. Avatar Filter

`avatar_filters` 用于让不同身份的 Avatar 遇到不同事件。

一期建议使用简单 `;` 分隔的键值条件，不实现复杂表达式。

示例：

```text
race=yao
alignment=evil
sect=any
sect=none
official=any
official=none
realm_min=FOUNDATION_ESTABLISHMENT
realm_max=GOLDEN_CORE
```

多个条件表示全部满足：

```text
race=yao;alignment=evil
sect=any;realm_min=FOUNDATION_ESTABLISHMENT
```

建议支持字段：

1. `race`
2. `alignment`
3. `sect`
4. `official`
5. `realm_min`
6. `realm_max`

一期不建议支持 `or`、括号、比较表达式或脚本化条件。

## 10. 触发与限流

一期建议新增独立配置项，具体路径放在 `static/config.yml -> world.background_npc`，与现有 `random_minor_event_prob`、`fortune_probability` 等世界事件配置保持同层。

推荐配置：

```yaml
world:
  background_npc:
    enabled: true
    region_tick_prob: 0.25
    avatar_witness_prob: 0.03
    action_echo_prob: 0.15
    max_region_tick_per_month: 1
    max_avatar_witness_per_month: 2
    max_action_echo_per_month: 2
```

建议限流原则：

1. `region_tick` 每月最多 1 条。
2. `avatar_witness` 每月最多 2 条。
3. `action_echo` 每月最多 2 条。
4. 同一 `event_key` 遵守 `cooldown_months`。
5. 同一 Avatar 的 `avatar_witness` 不应过密，建议运行时额外按 `avatar_id + event_key` 记录月度冷却。

冷却状态可以是 runtime 内存态，不进存档。读档或重启后冷却清空可以接受，因为一期事件不影响状态。

## 11. 模拟器接入建议

建议新增：

```text
src/systems/background_npc/
  __init__.py
  loader.py
  models.py
  service.py
```

模拟器 phase 可以放在 `random_minor_events` 附近，语义上属于低成本小事件层。

候选接入：

```python
async def phase_background_npc_events(world, living_avatars) -> list[Event]:
    return BackgroundNpcService.try_create_monthly_events(world, living_avatars)
```

相位位置建议：

1. 在行动执行之后。
2. 在 `random_minor_events` 附近。
3. 在 `finalize_step()` 之前统一入库。

不要在 `src/server/main.py` 中扩散逻辑。

## 12. 与 Random Minor Event 的边界

现有 `random_minor_event` 面向 Avatar 小事，且当前会在线调用 LLM 生成文本。

背景板 NPC 系统与其边界如下：

1. `random_minor_event`：角色自身或角色间的微观事件。
2. `background_npc`：凡人背景、地区烟火、Avatar 被凡俗世界看见。

两者都生成普通小事件，但：

- `random_minor_event` 可以改变关系。
- `background_npc` 不改变任何状态。
- `random_minor_event` 的文本由 LLM 生成。
- `background_npc` 的文本来自预写 i18n 模板。

## 13. 与事件系统的关系

背景板 NPC 事件统一使用：

```python
Event(
    month_stamp=world.month_stamp,
    content=rendered_text,
    related_avatars=...,
    related_sects=...,
    is_major=False,
    is_story=False,
    event_type="background_npc",
)
```

显示策略：

1. `region_tick` 进入主事件流，但不进入 Avatar 个人事件栏。
2. `avatar_witness` 进入主事件流和对应 Avatar 个人事件栏。
3. `action_echo` 进入主事件流和对应 Avatar 个人事件栏。

不使用 `is_story=True`。背景板 NPC 事件不是 LLM 展开的小故事正文。

## 14. 内容写作规范

### 14.1 推荐风格

背景板 NPC 的价值是低保真凡俗视角。

推荐：

- 描述余波，不解释真相。
- 写误读、传闻、旁观、恐惧、敬畏、买卖、秩序。
- 让凡人体现修士行动的社会回声。
- 使用无名身份和群体称谓。

示例：

```text
茶馆说书人声称东海有仙府出世，听客喝彩，账房却只记下多卖了三壶茶。
```

### 14.2 避免写法

避免：

1. 给 NPC 起名。
2. 承诺 NPC 将来再次出现。
3. 让凡人准确解释高阶修仙真相。
4. 在事件中直接生成任务、秘境、机缘、POI。
5. 写出会暗示状态已经改变的结果，例如“城中米价从此下降”。
6. 写需要后续追踪的句子，例如“他暗暗记下了此事，来日必有回报”。

## 15. 首批内容包建议

一期可先做六个内容包，每包 8 到 12 条事件。

### 15.1 城市市井

画像：

- 药材商
- 药铺掌柜
- 客栈掌柜
- 茶馆说书人
- 巡街差役
- 医馆大夫
- 当铺朝奉
- 材料牙人

### 15.2 港口海岛

画像：

- 船老大
- 水手
- 渔民
- 海货商贩
- 潮汐引路人
- 采珠人
- 海图贩子
- 港口税吏

### 15.3 山岭边境

画像：

- 山口守卒
- 矿队管事
- 采矿苦工
- 走山猎户
- 峡河船夫
- 驿站马夫
- 采参人
- 矿洞幸存者

### 15.4 宗门山下

画像：

- 外门杂役
- 山门守童
- 药田农夫
- 灵兽园饲养人
- 炼丹房火工
- 藏经阁抄书人
- 山下佃户
- 求仙父母
- 采买人

### 15.5 官府朝廷

画像：

- 县令
- 太守
- 税吏
- 布告官
- 粮仓管事
- 师爷
- 更夫
- 驿传官
- 国师门客

### 15.6 黑市坊市

画像：

- 黑市掮客
- 坊市摊主
- 鉴货朝奉
- 寄售行管事
- 店铺护院
- 收旧货商
- 灵材牙人

## 16. 测试建议

一期实现时建议补以下测试：

1. loader 能读取 profile / event / region binding。
2. 一个 profile 可以绑定多条 event。
3. `region_types`、`required_tags`、`excluded_tags`、`map_ids` 过滤正确。
4. `avatar_filters` 对 race / alignment / sect / official / realm 生效。
5. `region_tick` 事件不带 `related_avatars`。
6. `avatar_witness` / `action_echo` 事件带 `related_avatars=[avatar.id]`。
7. 所有生成事件 `is_major=False`、`is_story=False`、`event_type="background_npc"`。
8. 限流和 cooldown 生效。
9. 文本通过 `text_id` 渲染，未翻译时有可控 fallback。
10. region binding 中的 `map_id + region_id` 能通过官方地图校验。

若改动官方地图绑定，至少运行：

```bash
python tools/map_presets/validate_presets.py
```

若新增 locale 源文件或条目，运行：

```bash
python tools/i18n/build_mo.py
pytest tests/test_backend_locales.py
```

## 17. 后续二期口子

一期完成后，二期可以从少量高频画像中挑选“可二次出场”的轻量 NPC，但二期不应反向污染一期模型。

可能方向：

1. 将少数 profile 升级为可持久化的 `named_mortal_npc`。
2. 扮演模式中允许和部分 NPC 对话。
3. 让对话 summary 以事件形式落地，但原始聊天记录不进长期事件流。
4. 为特定城市维护少量本地常驻 NPC。

这些都属于后续设计。一期只做无名、一次性、预写、无状态的凡人场景。
