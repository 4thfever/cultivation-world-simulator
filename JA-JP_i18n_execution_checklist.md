# ja-JP i18n 执行顺序版清单

本文档用于把“新增日语 `ja-JP`”拆成一条可执行路径，尽量减少返工。

## 目标与约束

1. 本次任务目标：为仓库正式接入新语言 `ja-JP`。
2. 语言单一真相源：`static/locales/registry.json`。
3. 本次应视为“新增语言 / Phase 2 范围工作”，不要按仅维护 `zh-CN` 的 Phase 1 做法执行。
4. 前端、后端、模板、名字库、README、测试都属于 i18n 接入范围，不只是一套 UI 文案。

## 姓名策略

1. `ja-JP` 的姓名风格采用“中文风格的日语化呈现”。
2. 具体含义：
   `王` 仍然保持 `王`
   `李` 仍然保持 `李`
   不做“强行日式改姓”或“意译成日式常见姓氏”的处理。
3. 目标效果：
   读者感知为“日语界面中的中文修仙姓名”，而不是“把中文角色改造成日本本土姓名”。
4. 仍沿用当前系统对 `ja` 的无空格姓名拼接行为。

## 术语表状态

1. `docs/glossary.csv` 已新增 `ja_jp` 列。
2. 当前策略：
   - 高频核心术语已先确定日语写法
   - 宗门名、地名、专有名词优先保留汉字风格
   - 后续 `.po` / `.json` / `templates` 翻译应优先参照该表

## 推荐执行顺序

### [x] 第 1 步：建立任务边界

1. 明确本次是 `ja-JP` 新语言接入，不是单纯补几条翻译。
2. 确认本次会同时覆盖：
   - 前端 JSON
   - 后端 `.po`
   - `templates/*.txt`
   - `game_configs/given_name.csv`
   - `game_configs/last_name.csv`
   - README 多语言文档
   - locale 测试与构建

### [x] 第 2 步：先改语言注册表

1. 修改 `static/locales/registry.json`，新增 `ja-JP` 条目。
2. 推荐字段：

```json
{
  "code": "ja-JP",
  "label": "日本語",
  "html_lang": "ja",
  "enabled": true
}
```

3. 不要改动：
   - `default_locale`
   - `fallback_locale`
   - `schema_locale`
   - `source_of_truth`
4. 保持 `zh-CN` 仍是 source locale，`en-US` 仍是 fallback/schema locale。

### [x] 第 3 步：先复制完整骨架，再开始翻译

1. 新建前端目录：
   - `web/src/locales/ja-JP/`
2. 新建后端目录：
   - `static/locales/ja-JP/`
3. 建议以 `vi-VN` 或 `en-US` 作为完整骨架来源复制。
4. 复制时要确保以下后端子目录全部存在：
   - `modules/`
   - `game_configs_modules/`
   - `LC_MESSAGES/`
   - `templates/`
   - `game_configs/`
5. 复制完成后，不要立即手改 `LC_MESSAGES/*.po` 与 `*.mo`，它们后续统一构建。

### [x] 第 4 步：补齐前端 locale 文件结构

1. 检查 `web/src/locales/ja-JP/` 下文件名与其他语言完全一致。
2. 当前应包含：
   - `attributes.json`
   - `common.json`
   - `game_start.json`
   - `game.json`
   - `llm.json`
   - `loading.json`
   - `realms.json`
   - `save_load.json`
   - `splash.json`
   - `technique_grades.json`
   - `ui.json`
   - `world_info.json`
3. 这一阶段先保证“文件齐、key 齐”，文案质量可以下一步再细修。

### [x] 第 5 步：补齐后端 PO 文件结构

1. 检查 `static/locales/ja-JP/modules/` 文件是否齐全。
2. 当前应覆盖：
   - `action.po`
   - `action_combat.po`
   - `action_progression.po`
   - `action_world.po`
   - `alignment.po`
   - `auxiliary.po`
   - `avatar.po`
   - `battle.po`
   - `common.po`
   - `condition_translation.po`
   - `cultivation.po`
   - `custom_content_prompt.po`
   - `death_reasons.po`
   - `decision_description.po`
   - `default_values.po`
   - `direction_names.po`
   - `effect.po`
   - `elixir.po`
   - `essence_type.po`
   - `event_content.po`
   - `execution_results.po`
   - `feedback_labels.po`
   - `formatted_strings.po`
   - `fortune.po`
   - `gathering.po`
   - `gender.po`
   - `hidden_domain.po`
   - `item_exchange.po`
   - `item_verbs.po`
   - `labels.po`
   - `llm_prompt.po`
   - `map.po`
   - `misfortune.po`
   - `mutual_action.po`
   - `option_a.po`
   - `option_b.po`
   - `realm.po`
   - `relation.po`
   - `root_element.po`
   - `scene_setting.po`
   - `sect.po`
   - `animal.po`
   - `plant.po`
   - `material.po`
   - `elixir.po`
   - `weapon.po`
   - `technique.po`
   - `normal_region.po`
   - `hidden_domain.po`
   - `orthodoxy.po`
   - `root.po`
   - `auxiliary.po`
   - `manual_effects.po`
   - `celestial_phenomenon.po`
   - `dynasty.po`
   - `lode.po`
   - `persona.po`
   - `random_minor_event.po`
   - `sect_region.po`
   - `sect_random_event.po`
   - `separators.po`
   - `simulator.po`
   - `single_choice.po`
   - `stage.po`
   - `story_generation_text.po`
   - `story_styles.po`
   - `technique.po`
   - `normal_region.po`
   - `hidden_domain.po`
   - `orthodoxy.po`
   - `root.po`
   - `auxiliary.po`
   - `manual_effects.po`
   - `celestial_phenomenon.po`
   - `dynasty.po`
   - `lode.po`
   - `persona.po`
   - `random_minor_event.po`
   - `sect_region.po`
   - `tournament.po`
   - `ui.po`
   - `weapon.po`
   - `technique.po`
   - `normal_region.po`
   - `hidden_domain.po`
   - `orthodoxy.po`
   - `root.po`
   - `auxiliary.po`
   - `manual_effects.po`
   - `celestial_phenomenon.po`
   - `dynasty.po`
   - `lode.po`
   - `persona.po`
   - `random_minor_event.po`
   - `sect_region.po`
3. 检查 `static/locales/ja-JP/game_configs_modules/` 文件是否齐全。
4. 当前应覆盖：
   - `animal.po`
   - `auxiliary.po`
   - `celestial_phenomenon.po`
   - `city_region.po`
   - `cultivate_region.po`
   - `sect.po`
   - `animal.po`
   - `plant.po`
   - `material.po`
   - `elixir.po`
   - `weapon.po`
   - `technique.po`
   - `normal_region.po`
   - `hidden_domain.po`
   - `orthodoxy.po`
   - `root.po`
   - `auxiliary.po`
   - `manual_effects.po`
   - `celestial_phenomenon.po`
   - `dynasty.po`
   - `lode.po`
   - `persona.po`
   - `random_minor_event.po`
   - `sect_region.po`
   - `dynasty.po`
   - `elixir.po`
   - `hidden_domain.po`
   - `lode.po`
   - `manual_effects.po`
   - `celestial_phenomenon.po`
   - `dynasty.po`
   - `lode.po`
   - `persona.po`
   - `random_minor_event.po`
   - `sect_region.po`
   - `material.po`
   - `normal_region.po`
   - `orthodoxy.po`
   - `persona.po`
   - `plant.po`
   - `material.po`
   - `elixir.po`
   - `weapon.po`
   - `technique.po`
   - `normal_region.po`
   - `hidden_domain.po`
   - `orthodoxy.po`
   - `root.po`
   - `auxiliary.po`
   - `manual_effects.po`
   - `celestial_phenomenon.po`
   - `dynasty.po`
   - `lode.po`
   - `persona.po`
   - `random_minor_event.po`
   - `sect_region.po`
   - `random_minor_event.po`
   - `root.po`
   - `sect.po`
   - `animal.po`
   - `plant.po`
   - `material.po`
   - `elixir.po`
   - `weapon.po`
   - `technique.po`
   - `normal_region.po`
   - `hidden_domain.po`
   - `orthodoxy.po`
   - `root.po`
   - `auxiliary.po`
   - `manual_effects.po`
   - `celestial_phenomenon.po`
   - `dynasty.po`
   - `lode.po`
   - `persona.po`
   - `random_minor_event.po`
   - `sect_region.po`
   - `sect_region.po`
   - `technique.po`
   - `normal_region.po`
   - `hidden_domain.po`
   - `orthodoxy.po`
   - `root.po`
   - `auxiliary.po`
   - `manual_effects.po`
   - `celestial_phenomenon.po`
   - `dynasty.po`
   - `lode.po`
   - `persona.po`
   - `random_minor_event.po`
   - `sect_region.po`
   - `weapon.po`
   - `technique.po`
   - `normal_region.po`
   - `hidden_domain.po`
   - `orthodoxy.po`
   - `root.po`
   - `auxiliary.po`
   - `manual_effects.po`
   - `celestial_phenomenon.po`
   - `dynasty.po`
   - `lode.po`
   - `persona.po`
   - `random_minor_event.po`
   - `sect_region.po`
   - `world_info.po`
5. 这一阶段同样先保证“文件齐、msgid 齐”。

### [x] 第 6 步：补齐模板目录

1. 检查 `static/locales/ja-JP/templates/` 文件是否完整。
2. 当前至少应覆盖：
   - `ai.txt`
   - `auction_need.txt`
   - `backstory.txt`
   - `conversation.txt`
   - `custom_content.txt`
   - `long_term_objective.txt`
   - `mutual_action.txt`
   - `nickname.txt`
   - `relation_update.txt`
   - `sect_decider.txt`
   - `sect_random_event.txt`
   - `sect_thinker.txt`
   - `single_choice.txt`
   - `story_dual.txt`
   - `story_gathering.txt`
   - `story_single.txt`
   - `world_lore_item.txt`
   - `world_lore_map.txt`
   - `world_lore_sect.txt`
3. 额外检查“随机事件模板”命名是否与现有语言存在差异。
4. 如发现 `zh-CN` 与 `en-US` / `vi-VN` 模板文件名不一致，不要想当然，需按实际消费代码逐个对齐。

### [x] 第 7 步：补齐名字库与本地化 CSV

1. 检查以下文件是否存在：
   - `static/locales/ja-JP/game_configs/given_name.csv`
   - `static/locales/ja-JP/game_configs/last_name.csv`
2. 姓名策略按“中文风格的日语化姓名”处理：
   - 保留中文修仙姓名风味
   - 不替换成日本常见姓氏
   - 不做意译或日式改写
3. 如果需要人工整理名字库，优先保证：
   - 可读
   - 符合修仙世界观
   - 和 UI 语言切换后观感一致
4. 该步骤完成后，重点关注姓名生成与王朝生成链路是否还能正常工作。

### [x] 第 8 步：先做“结构完整性”自检

1. 先运行缺失报告，确认有没有漏目录、漏模块、漏 key：

```bash
python tools/i18n/generate_missing_report.py
```

2. 优先处理报告中的“文件缺失 / key 缺失 / msgid 缺失”。
3. 这一轮不要急着追求翻译润色，先把结构打通。

### 第 9 步：翻译前端 JSON

当前进度：
1. 已完成高频模块日文化：
   - `common.json`
   - `game_start.json`
   - `loading.json`
   - `save_load.json`
   - `ui.json`
   - `attributes.json`
   - `realms.json`
   - `splash.json`
   - `technique_grades.json`
   - `llm.json`
   - `world_info.json`
   - `game.json`
2. 当前前端主界面已基本摆脱英文 / 越南语基线。

1. 按模块翻译 `web/src/locales/ja-JP/*.json`。
2. 建议顺序：
   - `common.json`
   - `ui.json`
   - `loading.json`
   - `save_load.json`
   - `game_start.json`
   - `game.json`
   - 其余模块
3. 特别注意：
   - 枚举值
   - 面板标题
   - tooltip
   - 占位符
   - 含 `{count}` / `{name}` / `{years}` 这类参数的句子
4. 不要改 key 结构，只改 value。

### 第 10 步：翻译后端 PO

当前进度：
1. 已开始翻译 `modules/common.po` 的高频系统提示。
2. 已开始翻译 `modules/ui.po`。
3. 已补主要模块的关键高频条目：
   - `event_content.po`
   - `avatar.po`
   - `sect.po`
   - `animal.po`
   - `plant.po`
   - `material.po`
   - `elixir.po`
   - `weapon.po`
   - `technique.po`
   - `normal_region.po`
   - `hidden_domain.po`
   - `orthodoxy.po`
   - `root.po`
   - `auxiliary.po`
   - `manual_effects.po`
   - `celestial_phenomenon.po`
   - `dynasty.po`
   - `lode.po`
   - `persona.po`
   - `random_minor_event.po`
   - `sect_region.po`
   - `action.po`
   - `action_combat.po`
   - `action_progression.po`
   - `action_world.po`
   - `battle.po`
4. 已补事件体验层的关键条目：
   - `fortune.po`
   - `gathering.po`
   - `relation.po`
   - `mutual_action.po`
   - `story_generation_text.po`
   - `story_styles.po`
5. 已补系统层 / 展示层关键条目：
   - `effect.po`
   - `labels.po`
   - `formatted_strings.po`
   - `feedback_labels.po`
   - `execution_results.po`
6. 已补公共基础模块的关键条目：
   - `misfortune.po`
   - `death_reasons.po`
   - `condition_translation.po`
   - `decision_description.po`
   - `default_values.po`
   - `common.po`（继续补充）
7. 其余 `.po` 仍有不少英文基线，后续继续补全。
8. 本轮已新增补全高英文占比模块：
   - `scene_setting.po`
   - `custom_content_prompt.po`
   - `auxiliary.po`
   - `tournament.po`
   - `map.po`
9. 本轮继续补了术语 / 物品 / 提示相关模块：
   - `llm_prompt.po`
   - `root_element.po`
   - `weapon.po`
   - `technique.po`
   - `normal_region.po`
   - `hidden_domain.po`
   - `orthodoxy.po`
   - `root.po`
   - `auxiliary.po`
   - `manual_effects.po`
   - `celestial_phenomenon.po`
   - `dynasty.po`
   - `lode.po`
   - `persona.po`
   - `random_minor_event.po`
   - `sect_region.po`
   - `technique.po`
   - `normal_region.po`
   - `hidden_domain.po`
   - `orthodoxy.po`
   - `root.po`
   - `auxiliary.po`
   - `manual_effects.po`
   - `celestial_phenomenon.po`
   - `dynasty.po`
   - `lode.po`
   - `persona.po`
   - `random_minor_event.po`
   - `sect_region.po`
   - `item_exchange.po`

1. 先翻译 `modules/*.po` 的核心模块：
   - `common.po`
   - `ui.po`
   - `action*.po`
   - `avatar.po`
   - `event_content.po`
   - `execution_results.po`
   - `sect.po`
   - `animal.po`
   - `plant.po`
   - `material.po`
   - `elixir.po`
   - `weapon.po`
   - `technique.po`
   - `normal_region.po`
   - `hidden_domain.po`
   - `orthodoxy.po`
   - `root.po`
   - `auxiliary.po`
   - `manual_effects.po`
   - `celestial_phenomenon.po`
   - `dynasty.po`
   - `lode.po`
   - `persona.po`
   - `random_minor_event.po`
   - `sect_region.po`
   - `gathering.po`
   - `fortune.po`
2. 再翻译 `game_configs_modules/*.po`。
3. 当前已开始补充：
   - `world_info.po`
   - `city_region.po`
   - `cultivate_region.po`
   - `sect.po`
   - `animal.po`
   - `plant.po`
   - `material.po`
   - `elixir.po`
   - `weapon.po`
   - `technique.po`
   - `normal_region.po`
   - `hidden_domain.po`
   - `orthodoxy.po`
   - `root.po`
   - `auxiliary.po`
   - `manual_effects.po`
   - `celestial_phenomenon.po`
   - `dynasty.po`
   - `lode.po`
   - `persona.po`
   - `random_minor_event.po`
   - `sect_region.po`
3. 保持规则：
   - `msgid` 不动
   - `msgstr` 填日语
   - 不直接编辑 `LC_MESSAGES/messages.po`
4. 若某些条目决定保留中文固有名词，可在日语句子中保留原汉字名称。

### 第 11 步：翻译模板文本

当前进度：
1. 已完成：
   - `custom_content.txt`
   - `sect_decider.txt`
   - `sect_thinker.txt`
2. 其余模板仍待继续日文化。
3. 本轮已新增：
   - `story_single.txt`
   - `story_dual.txt`
   - `story_gathering.txt`
   - `world_lore_item.txt`
   - `world_lore_map.txt`
   - `world_lore_sect.txt`
4. 后续继续补充的高频模板：
   - `ai.txt`
   - `conversation.txt`
   - `nickname.txt`
   - `backstory.txt`
   - `long_term_objective.txt`
   - `mutual_action.txt`
   - `relation_update.txt`
   - `random_minor_event.txt`
   - `single_choice.txt`

1. 重点翻译 `templates/*.txt`。
2. 建议优先级：
   - `custom_content.txt`
   - `sect_decider.txt`
   - `sect_thinker.txt`
   - `story_single.txt`
   - `story_dual.txt`
   - `story_gathering.txt`
   - `conversation.txt`
   - `nickname.txt`
3. 模板里若包含世界观术语，优先与 PO / JSON 里的日语术语保持一致。
4. 对 LLM 模板，语义一致性比逐字直译更重要，但变量占位符必须保持不变。

### [x] 第 12 步：构建合并产物

1. 完成 `.po` 修改后运行：

```bash
python tools/i18n/build_mo.py
```

2. 该步骤会生成或更新：
   - `static/locales/ja-JP/LC_MESSAGES/messages.po`
   - `static/locales/ja-JP/LC_MESSAGES/messages.mo`
   - `static/locales/ja-JP/LC_MESSAGES/game_configs.po`
   - `static/locales/ja-JP/LC_MESSAGES/game_configs.mo`
3. 不要人工维护这些构建产物的内容。

### [x] 第 13 步：跑 locale 核心测试

1. 先跑最关键的两个：

```bash
pytest tests/test_frontend_locales.py tests/test_backend_locales.py
```

2. 如果失败，优先修：
   - JSON key 不一致
   - PO msgid 集不一致
   - 缺目录 / 缺文件
   - 合并产物缺失

### [x] 第 14 步：补跑 i18n 扩展测试

1. 建议继续运行：

```bash
pytest tests/test_i18n_modules.py tests/test_i18n_dynamic.py tests/test_language.py tests/test_effect_desc_i18n.py tests/test_save_load_language.py tests/test_csv_loading.py tests/test_custom_content_prompt_reference.py tests/tools/test_prompt_template_format.py tests/test_locale_registry_migration.py
```

2. 如果只想分批跑，可按下面顺序：
   - 语言注册与切换
   - 模板解析与回退
   - CSV 加载
   - 动态翻译与效果描述
   - 存档读档语言恢复

### 第 15 步：补跑前端测试与类型检查

当前状态：
1. `npm run type-check` 已通过。
2. `npm run test` 已尝试两次，但在当前环境下超时，需后续单独排查或在更宽松超时下运行。

1. 运行：

```bash
cd web && npm run type-check
cd web && npm run test
```

2. 重点观察：
   - locale schema 相关报错
   - 语言菜单
   - 设置 store
   - `html lang` 行为

### 第 16 步：补 README 与文档

1. 新增：
   - `docs/readme/JA-JP_README.md`
2. 内容来源以根目录 `README.md` 为准，翻译为日语。
3. 当前 `docs/readme/JA-JP_README.md` 已从占位英文版切换为正式日语版。
4. 如果有“支持语言列表”或“历史上默认三语言”的文档描述，顺手更新：
   - `docs/i18n-guide.md`
   - `docs/i18n-add-locale.md`
   - `docs/frontend-i18n.md`
5. 如果 README 依赖多语言截图资源，再决定是否补 `assets/ja-JP/` 相关内容。

### 第 17 步：手动 smoke test

1. 在前端设置中确认能看到 `日本語` 选项。
2. 切换后确认页面 `html lang` 为 `ja`。
3. 确认 UI 能正常显示日语文案。
4. 新开局后确认 `content_locale` 为 `ja-JP`。
5. 检查姓名显示：
   - 不加空格
   - 保留中文风格姓名
   - 不被意外日式改姓
6. 检查这些重点页面或功能：
   - 系统菜单
   - 角色详情
   - 区域详情
   - 宗门详情
   - 事件日志
   - 存档 / 读档
   - LLM 相关功能入口
7. 模板缺失时，确认能正确回退到 `en-US` 或 `zh-CN`，且不会直接崩溃。

### 第 18 步：收尾清理

1. 如果生成了 `i18n_missing_report.md`，在完成后删除。
2. 检查不要误提交：
   - 临时报告
   - 调试输出
   - 无意义的生成垃圾
3. 当前已完成一次日语残留清扫，已修复：
   - `option_a.po`
   - `option_b.po`
   - `mutual_action.po`
   - `misfortune.po`
   - `action_combat.po`
   - `common.po`
   - `effect.po`
   - `simulator.po`
   - `single_choice.po`
   - `game_configs_modules/persona.po`
4. 复扫时优先区分：
   - 真正未翻译的 `msgstr`
   - 技术上保留的占位符、协议字段、产品名
5. 最后确认改动集中在：
   - `static/locales/registry.json`
   - `web/src/locales/ja-JP/`
   - `static/locales/ja-JP/`
   - `docs/readme/JA-JP_README.md`
   - 必要的文档更新

## 推荐验收标准

1. `ja-JP` 出现在前端语言菜单中，且可正常切换。
2. 前端 locale 测试通过。
3. 后端 locale 测试通过。
4. 名字库加载正常，姓名保持中文修仙风格。
5. 模板解析可用，缺失时能按注册表回退。
6. 构建产物 `.mo` / `LC_MESSAGES/*.po` 正常生成。
7. README 日语版本可交付。

## 最容易遗漏的事项

1. 忘了先改 `static/locales/registry.json`。
2. 前端 JSON 文件名少一个。
3. `templates/` 少一两个模板文件。
4. `given_name.csv` / `last_name.csv` 漏掉。
5. 手动改了 `LC_MESSAGES/messages.po`。
6. README 多语言文档没补。
7. 把姓名“翻译成日式姓氏”而偏离既定策略。
