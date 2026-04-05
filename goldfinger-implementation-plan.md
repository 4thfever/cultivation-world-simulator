# 外挂（Goldfinger）系统实施计划

## 1. 已确认的产品结论

本计划基于以下已经确认的方向：

1. 前端中文名称统一叫“外挂”。
2. 内部字段名、英文语义统一使用 `goldfinger`。
3. 自定义外挂走“自然语言生成”流程，整体参考当前功法 / 兵器 / 辅助装备的自定义链路。
4. 故事型外挂也允许同时带数值 `effects`，不与故事定位冲突。
5. `霉运逆转` 第一版为 `100%` 逆转，不做概率触发。
6. `系统 / 时间作弊 / 推演终端` 本次只在官方外挂中占位，不实现实际机制。

## 2. 目标

为角色增加一条独立于 `persona`、`technique`、`weapon`、`auxiliary` 的新轴：

- 中文展示：`外挂`
- 内部字段：`goldfinger`

系统目标：

1. `goldfinger` 成为 Avatar 独立栏位，而不是继续放在 `persona` 中。
2. `穿越者 / 重生者 / 气运之子 / 福缘深厚` 从 `persona` 迁移到 `goldfinger`。
3. 一个角色最多只能拥有 `1` 个外挂。
4. 支持初始化低概率随机分配。
5. 支持玩家手动修改外挂。
6. 支持玩家通过自然语言生成自定义外挂。
7. 自定义外挂仅支持 `effect` 型，不支持自定义机制逻辑。
8. 外挂信息进入角色详情、结构化信息、AI 上下文和故事系统。
9. 第一批机制型外挂只真正落地 `霉运逆转`。

## 3. 语义边界

后续系统统一按以下边界维护：

- `persona`：人格、性格、作风、行为倾向。
- `goldfinger`：主角模板、外挂、超规格命数、额外叙事视角。
- `technique / weapon / auxiliary`：角色拥有的功法与外在资源。

判断标准：

- “这个人是什么样的人”属于 `persona`
- “这个人身上绑了什么外挂”属于 `goldfinger`
- “这个人学了什么 / 拿了什么”属于装备与功法

## 4. 分类方案

`goldfinger` 分为三类：

### 4.1 `effect_only`

只提供数值，不引入专属运行时逻辑。

首发：

1. 气运之子
2. 福缘深厚

### 4.2 `story_driven`

有数值，也强影响故事视角与 prompt。

首发：

1. 穿越者
2. 重生者
3. 随身老爷爷

说明：

1. 这些外挂第一版不要求独立状态机。
2. 但允许附带小幅数值，例如 `extra_luck`、`extra_epiphany_probability`、`extra_breakthrough_success_rate` 等。

### 4.3 `mechanic_driven`

需要在系统逻辑中专门接入机制处理。

本次：

1. 霉运逆转：正式实现
2. 系统：只占位，不实现
3. 时间作弊：只占位，不实现
4. 推演终端：只占位，不实现

## 5. 首发外挂清单

本次官方外挂分两类：已实现与占位。

### 5.1 本次正式可用

1. 气运之子
2. 福缘深厚
3. 穿越者
4. 重生者
5. 随身老爷爷
6. 霉运逆转

### 5.2 本次仅占位

1. 系统
2. 时间作弊
3. 推演终端

说明：

1. 占位外挂可出现在官方列表中。
2. 但 `mechanism_type` 不接运行时逻辑，或通过 `enabled=false` / 空机制配置方式只做未来预留。

## 6. 数据模型

新增领域对象：

- `src/classes/goldfinger.py`

建议结构：

- `id: int`
- `key: str`
- `name: str`
- `desc: str`
- `rarity`
- `condition: str`
- `effects: dict[str, object]`
- `effect_desc: str`
- `mechanism_type: str`
- `display_text: str`
- `story_prompt: str`
- `exclusion_keys: list[str]`
- `mechanism_config: dict[str, object]`
- `enabled: bool = True`

字段说明：

1. `display_text`
   给玩家看的说明文本，用于详情和编辑面板。
2. `story_prompt`
   给 LLM 的专用提示，不直接展示给玩家。
3. `mechanism_type`
   建议取值：
   - `effect_only`
   - `story_driven`
   - `mechanic_driven`
4. `mechanism_config`
   用于机制外挂的附加参数。
5. `enabled`
   允许官方占位外挂先存在但暂不真正生效。

## 6.1 数据真源与职责边界

外挂系统后续统一遵守下面这条规则：

- 系统要依赖的数据，一律走结构化字段。
- `detailed info / expanded info / prompt text` 只做展示、补充语境、增强叙事，不承担业务判定职责。

具体约束：

1. `avatar.goldfinger`
   - 外挂唯一真源
   - 负责数值效果、故事入口判断、机制判断、前端展示、编辑、自定义、存档读写
2. `avatar.goldfinger_state`
   - 外挂运行时状态唯一真源
   - 负责任务进度、触发次数、冷却、阶段状态与后续机制扩展
3. `goldfinger.story_prompt`
   - 外挂给 AI 的专用提示真源
   - 由故事系统、小故事系统、奇遇系统等定向注入
4. `goldfinger.display_text / goldfinger.desc`
   - 用于玩家展示与模型补充理解
   - 不参与业务判定
5. `detailed info / expanded info / AI context`
   - 负责同步展开外挂信息，帮助 LLM 理解上下文
   - 不允许反向成为业务逻辑真源

判断标准：

1. 会被代码判断、编辑、保存、同步到前端的内容，必须放结构化字段
2. 只是帮助模型理解气氛、视角、文风的内容，可以放 `detailed info / prompt text`
3. 若两边都需要，则结构化字段做真源，再同步一份到 `detailed info / expanded info`

一句话规范：

- 外挂不是一段描述，而是一个系统对象；描述可以从对象生成，对象不能退化成描述。

## 7. 配表与加载

新增配表：

- `static/game_configs/goldfinger.csv`

建议列：

- `id`
- `name_id`
- `desc_id`
- `key`
- `name`
- `desc`
- `rarity`
- `enabled`
- `condition`
- `effects`
- `mechanism_type`
- `display_text`
- `story_prompt`
- `exclusion_keys`
- `mechanism_config`

`src/classes/goldfinger.py` 需要提供：

1. `Goldfinger` 数据类
2. `goldfingers_by_id`
3. `goldfingers_by_name`
4. `reload()`
5. 随机抽取函数
6. 条件 / 互斥检查逻辑

## 8. Avatar 模型改动

在 `Avatar` 上新增：

- `goldfinger: Goldfinger | None = None`
- `goldfinger_state: dict = field(default_factory=dict)`

涉及文件：

1. `src/classes/core/avatar/core.py`
2. `src/sim/save/avatar_save_mixin.py`
3. `src/sim/load/avatar_load_mixin.py`

说明：

1. `goldfinger` 表示角色当前外挂。
2. `goldfinger_state` 用于记录机制外挂运行时状态。
3. 第一版即便只有 `霉运逆转` 用到，也应当把状态字段预留好。

## 9. Persona 拆分计划

从 `persona.csv` 中移出以下条目：

1. `TRANSMIGRATOR`
2. `CHILD_OF_FORTUNE`
3. `REINCARNATOR`
4. `BLESSED_WITH_GOOD_FORTUNE`

同步需要处理：

1. 删除或迁移它们的 persona 定义。
2. 把所有直接检查这些 persona key 的条件逻辑改为检查 `avatar.goldfinger`。
3. 更新相关测试。

重点排查文件：

1. `static/game_configs/celestial_phenomenon.csv`
2. `src/systems/fortune.py`
3. `tests/test_luck_effects.py`
4. `tests/systems/test_fortune.py`

兼容策略：

1. 当前项目处于开发阶段，不为旧 `persona_ids` 做高成本双轨兼容。
2. 旧档如果自然跳过这些 persona，可接受。
3. 若可零成本顺带容错，则保留。

## 10. 初始化规则

在 `src/sim/avatar_init.py` 中新增外挂分配流程。

建议规则：

1. 每个角色最多一个外挂。
2. 总体概率极低。
3. 稀有度越高权重越低。
4. 默认只在角色初始化时生成。

建议先在 `avatar_init.py` 中用常量实现：

- `GOLDFINGER_PROBABILITY`
- `GOLDFINGER_RARITY_WEIGHTS`
- `GOLDFINGER_MAX_COUNT = 1`

初始化顺序建议：

1. 创建 Avatar 基础数据
2. 分配 personas
3. 分配 goldfinger
4. `recalc_effects()`

原因：

1. 外挂会影响数值。
2. 外挂也要参与后续 backstory、奇遇、小故事 prompt。

## 11. 效果系统接入

在 `src/classes/effect/mixin.py` 的 `_get_raw_effect_breakdown()` 中新增外挂来源：

- `Goldfinger [{name}]`

建议顺序：

1. sect / orthodoxy
2. technique
3. root
4. official rank
5. personas
6. goldfinger
7. weapon
8. auxiliary

这样外挂的 `effects` 会自动参与：

1. `avatar.effects`
2. `current_effects`
3. luck 派生
4. HP / 寿元重算

## 12. 结构化信息与详情展示

外挂需要进入：

1. 普通 info
2. detailed info
3. structured info
4. expanded info
5. AI context

涉及文件：

1. `src/classes/core/avatar/info_presenter.py`

建议字段：

- 文本 info 中增加 `Goldfinger`
- 结构化 info 中增加 `goldfinger`

展示内容建议包含：

1. 名称
2. 描述
3. 稀有度
4. `effect_desc`
5. `display_text`
6. 若为机制类，则显示一个状态摘要

## 13. 前端展示方案

涉及文件：

1. `web/src/types/core.ts`
2. `web/src/types/api.ts`
3. `web/src/components/game/panels/info/AvatarDetail.vue`

实现要求：

1. 中文文案统一为“外挂”。
2. 内部字段保持 `goldfinger`。
3. “外挂”位置放在功法 / 武器 / 辅助装备区域下方。
4. 样式尽量复用 `EntityRow` 与现有单槽资源展示。
5. 需要 `edit` 按钮。

## 14. 玩家手动修改

沿用当前 `avatar_adjustment` 体系。

后端涉及：

1. `src/server/services/avatar_adjustment.py`
2. `src/server/main.py`

改造点：

1. `VALID_AVATAR_ADJUSTMENT_CATEGORIES` 增加 `goldfinger`
2. `build_avatar_adjust_options()` 增加 `goldfingers`
3. `apply_avatar_adjustment()` 支持单槽替换 `goldfinger`

前端涉及：

1. `web/src/types/api.ts`
2. `web/src/api/modules/avatar.ts`
3. `web/src/components/game/panels/info/components/AvatarAdjustPanel.vue`

行为要求：

1. 支持选择官方外挂
2. 支持选择自定义外挂
3. 支持清空外挂

## 15. 自定义外挂

### 15.1 产品规则

自定义外挂采用自然语言生成，整体参考当前功法 / 兵器 / 辅助装备的自定义流程。

限制规则：

1. 自定义外挂只允许 `effect` 型。
2. 不允许玩家自定义 `mechanic_driven`。
3. 不允许动态表达式。
4. 不允许脚本化效果。
5. 数值可适当偏强，但不能破坏世界基本秩序。

### 15.2 建议实现方式

新增服务：

- `src/server/services/custom_goldfinger_service.py`

原因：

1. 可复用 `custom_content_service.py` 的模板化生成思路。
2. 但 `goldfinger` 字段结构不同，不适合强塞进现有三类物品逻辑。

建议生成结果包含：

1. `name`
2. `desc`
3. `display_text`
4. `effects`
5. `effect_desc`
6. `story_prompt`
7. `mechanism_type = effect_only`
8. `is_custom = True`

### 15.3 Prompt 约束

生成 prompt 要强调：

1. 这是“外挂”，不是装备，也不是功法。
2. 文案风格应有主角模板感。
3. 数值允许比普通内容略强。
4. 但只能使用合法 `effects`。
5. 不要产出任务系统、时间回溯次数、脚本命令等机制内容。

### 15.4 前端交互

沿用当前自定义入口风格：

1. 玩家输入自然语言
2. 后端生成 draft
3. 前端展示预览
4. 玩家确认保存
5. 保存后自动装备到当前角色

提示词文案要明确加入：

1. “外挂的数值可以给大一点”
2. “但只能做数值型外挂”

## 16. 自定义外挂注册与存档

在 `src/classes/custom_content.py` 中新增一类自定义注册：

1. `custom_goldfingers_by_id`
2. `allocate_id("goldfinger")`
3. `register_goldfinger()`
4. `to_save_dict()` / `load_from_dict()` 增加 `goldfingers`

角色存档改造：

### 16.1 `src/sim/save/avatar_save_mixin.py`

新增：

1. `goldfinger_id`
2. `goldfinger_state`

### 16.2 `src/sim/load/avatar_load_mixin.py`

恢复：

1. `goldfinger`
2. `goldfinger_state`

## 17. 故事系统接入

### 17.1 总体原则

外挂不只展示在详情里，还要进入 AI 叙事上下文。

第一版不要求所有系统都深度改造，但要保证：

1. LLM 能明确知道角色拥有什么外挂
2. `story_prompt` 会进入故事生成 prompt
3. 奇遇、小故事、霉运优先围绕外挂展开

### 17.2 角色上下文接入

在 `src/classes/core/avatar/info_presenter.py` 的结构化和扩展信息中加入：

1. `goldfinger.name`
2. `goldfinger.desc`
3. `goldfinger.display_text`
4. `goldfinger.story_prompt`
5. `goldfinger.mechanism_type`

这样现有：

1. `StoryTeller._build_avatar_infos`
2. `random_minor_event_service`
3. 其他使用 `avatar.get_expanded_info()` 的地方

都能自动感知外挂。

### 17.3 模板增强

优先修改：

1. `static/locales/zh-CN/templates/story_single.txt`
2. `static/locales/zh-CN/templates/story_dual.txt`
3. `static/locales/zh-CN/templates/random_minor_event_solo.txt`
4. `static/locales/zh-CN/templates/random_minor_event_pair.txt`

新增要求：

1. 若角色拥有外挂，应把外挂视为重要叙事线索。
2. 若存在 `story_prompt`，优先围绕该提示组织故事。
3. 不要机械重复外挂名称，而要体现在视角、判断、误判、回忆、机缘来源或处世方式中。

### 17.4 优先接入的系统入口

本次优先改：

1. `src/systems/fortune.py`
2. `src/systems/random_minor_event_service.py`

建议方式：

1. 保留原有业务逻辑
2. 在已有 `prompt=` 的基础上追加外挂 `story_prompt`
3. 若外挂为 `story_driven`，再追加一句“本次故事重点围绕该外挂展开”

### 17.5 默认故事倾向

建议官方外挂预设如下叙事方向：

1. 穿越者
   - 现代经验
   - 错位感
   - 用现代思维解释修仙问题
   - 结果不一定成功
2. 重生者
   - 前世记忆
   - 试图避坑
   - 对旧结局的执念
   - 结果不一定如愿
3. 随身老爷爷
   - 有前辈指导、争执、提点、误导、保留信息
4. 气运之子
   - 机缘主动靠近
   - 冥冥之中的顺势
5. 福缘深厚
   - 逢凶化吉
   - 小处见大运
6. 霉运逆转
   - 先险后吉
   - 原本的不幸变成转机

## 18. 机制型外挂：霉运逆转

### 18.1 目标

将 `霉运逆转` 作为本次唯一正式落地的机制外挂样板。

规则：

1. 只要会触发 `misfortune`，且角色外挂为 `霉运逆转`
2. 就 `100%` 将本次霉运改写为幸运转机

### 18.2 建议实现位置

新增运行时服务：

- `src/classes/goldfinger_runtime_service.py`

提供类似接口：

- `resolve_misfortune_override(avatar, record) -> transformed_result | None`

### 18.3 接入点

在 `src/systems/fortune.py` 的 `try_trigger_misfortune()` 中优先检查：

1. 当前 avatar 是否有 `BAD_LUCK_REVERSAL`
2. 若有，则不执行原霉运结算
3. 直接进入“逆转后”的结果逻辑

### 18.4 第一版建议映射

不用做通用 DSL，直接硬编码：

1. `loss_spirit_stone -> 获得灵石`
2. `injury -> 因险得悟 / 小幅修为收益 / 避开大祸`
3. `backlash -> 反而稳住根基 / 获得小幅正向修为结果`

### 18.5 事件与故事要求

1. 基础事件要明确体现“原本为祸，结果转吉”。
2. 若生成故事事件，故事里要突出逆转过程。
3. `goldfinger_state` 记录：
   - `trigger_count`
   - `last_trigger_month`
   - `last_trigger_kind`

## 19. 占位外挂策略

对 `系统 / 时间作弊 / 推演终端`：

1. 本次仅加入 `goldfinger.csv`
2. 可以在编辑面板和详情中看见
3. 不接运行时逻辑
4. `enabled` 可设为 `false` 或机制配置为空
5. 不为其补故事专属实现，只保留基础展示字段与未来扩展位

## 20. 测试计划

### 20.1 数据加载测试

新增测试覆盖：

1. `goldfinger.csv` 成功加载
2. 稀有度、条件、互斥、`display_text`、`story_prompt` 正常

### 20.2 效果计算测试

1. 挂外正确进入 `get_effect_breakdown()`
2. 数值类外挂参与 `luck` 派生
3. `current_effects` 展示包含外挂来源

### 20.3 初始化测试

1. `avatar_init` 可低概率生成外挂
2. 每个角色最多一个外挂
3. 条件与互斥规则生效

### 20.4 API 与编辑测试

参考已有：

- `tests/test_api_avatar_adjustment.py`

新增验证：

1. `avatar_adjust_options` 包含 `goldfingers`
2. `update_avatar_adjustment` 支持 `goldfinger`
3. 支持清空外挂

### 20.5 自定义外挂测试

新增验证：

1. 自然语言生成 draft 成功
2. 只允许合法 `effects`
3. 不允许机制型字段进入保存结果

### 20.6 存档测试

参考已有：

- `tests/test_save_load_custom_content.py`

新增验证：

1. 官方外挂 round-trip
2. 自定义外挂 round-trip
3. `goldfinger_state` round-trip

### 20.7 故事系统测试

1. fortune prompt 包含外挂上下文
2. random minor event prompt 包含外挂上下文
3. `story_driven` 外挂会把 `story_prompt` 注入故事生成

### 20.8 机制测试

1. `霉运逆转` 遇到 `misfortune` 时必定改写结果
2. 不再执行原始霉运扣减逻辑
3. 状态计数正确递增

## 21. 建议实施顺序

为了降低风险，建议按下面顺序开发：

### 阶段 A：模型与展示

1. 新增 `goldfinger.py`
2. 新增 `goldfinger.csv`
3. Avatar 增加字段
4. effects 汇总接入
5. info / structured info / expanded info 接入
6. 前端详情展示“外挂”

### 阶段 B：手动编辑与初始化

1. `avatar_adjustment` 接入 `goldfinger`
2. 前端编辑面板接入
3. `avatar_init` 随机分配外挂

### 阶段 C：自定义外挂与存档

1. `custom_goldfinger_service.py`
2. 前端自然语言生成入口
3. 自定义注册表接入
4. 存档读写接入

### 阶段 D：故事接入

1. 扩展 `expanded_info`
2. 修改故事模板
3. 修改 fortune / random minor event prompt 注入

### 阶段 E：机制样板

1. 新增 `goldfinger_runtime_service.py`
2. 正式落地 `霉运逆转`
3. 增加机制测试

## 22. 预期改动文件

### 后端

1. `src/classes/goldfinger.py`
2. `src/classes/goldfinger_runtime_service.py`
3. `src/classes/core/avatar/core.py`
4. `src/classes/core/avatar/info_presenter.py`
5. `src/classes/effect/mixin.py`
6. `src/classes/custom_content.py`
7. `src/sim/avatar_init.py`
8. `src/sim/save/avatar_save_mixin.py`
9. `src/sim/load/avatar_load_mixin.py`
10. `src/server/services/avatar_adjustment.py`
11. `src/server/services/custom_goldfinger_service.py`
12. `src/server/main.py`
13. `src/systems/fortune.py`
14. `src/systems/random_minor_event_service.py`

### 配置与数据

1. `static/game_configs/goldfinger.csv`
2. `static/game_configs/persona.csv`
3. `static/game_configs/celestial_phenomenon.csv`

### Prompt 与本地化

1. `static/locales/zh-CN/templates/story_single.txt`
2. `static/locales/zh-CN/templates/story_dual.txt`
3. `static/locales/zh-CN/templates/random_minor_event_solo.txt`
4. `static/locales/zh-CN/templates/random_minor_event_pair.txt`
5. 对应 `modules/*.po` 与合并产物

### 前端

1. `web/src/types/core.ts`
2. `web/src/types/api.ts`
3. `web/src/api/modules/avatar.ts`
4. `web/src/components/game/panels/info/AvatarDetail.vue`
5. `web/src/components/game/panels/info/components/AvatarAdjustPanel.vue`

### 测试

1. `tests/test_api_avatar_adjustment.py`
2. `tests/test_avatar_init.py`
3. `tests/test_save_load_custom_content.py`
4. `tests/test_luck_effects.py`
5. `tests/systems/test_fortune.py`
6. 新增 goldfinger 专项测试文件

## 23. 开发中的硬约束

实现时必须遵守：

1. 新增可加载模块后，更新对应导入与注册链路。
2. 存档仍只保存 JSON 基础类型与 ID，不直接保存复杂对象引用。
3. 前端 DTO、mapper、类型定义要同步更新，不能让 `any` 扩散。
4. 当前默认仍遵守 i18n Phase 1：日常开发优先只改 `zh-CN`，除非任务被明确升级为多语言补全。
5. 自定义外挂只允许 `effect`，不允许变相引入机制脚本。
6. 机制外挂第一版不要做通用 DSL，以清晰代码路径优先。

## 24. 结论

本次实现的正确落地方向不是“把外挂做成 trait 的扩展版”，而是：

1. 以 `goldfinger` 为新的独立栏位
2. 复用现有 `effect + detail + avatar_adjustment + custom_content + story prompt` 体系
3. 先用数据类和故事增强覆盖大部分外挂
4. 只对 `霉运逆转` 做一个真正的机制样板
5. 把 `系统 / 时间作弊 / 推演终端` 先放进官方表中占位，留待后续版本扩展

按这个顺序推进，能在不撕裂当前架构的情况下，把外挂系统稳稳接到现有代码设计里。
