# I18n 落地 TODO 拆分

本文件是 [i18n-rollout-plan.md](/e:/projects/cultivation-world-simulator/docs/specs/i18n-rollout-plan.md) 的执行版清单。

目标不是描述原则，而是把“先补哪些文件、后补哪些模块”拆成可落地的 TODO。

## 1. 总体执行顺序

建议严格按以下顺序推进：

1. 跑缺失报告，生成当前缺口基线。
2. 先补 `templates/`。
3. 再补近期新增功能的 `modules/*.po`。
4. 再补前端和后端运行时硬编码文案。
5. 再补 `game_configs_modules/*.po` 和 `game_configs/*.csv`。
6. 统一构建 `.mo`。
7. 跑 locale 测试。
8. 做人工验收。

## 2. 第 0 步：基线盘点

### 2.1 必做

- [ ] 运行 `python tools/i18n/generate_missing_report.py`
- [ ] 阅读生成的 `i18n_missing_report.md`
- [ ] 按语言整理缺口：
  - `zh-TW`
  - `en-US`
  - `vi-VN`
  - `ja-JP`
- [ ] 按类型整理缺口：
  - `templates`
  - `modules`
  - `game_configs_modules`
  - 前端硬编码
  - 后端硬编码

### 2.2 输出

- [ ] 记录“当前缺失最多的目录”
- [ ] 记录“当前缺失最多的功能链”
- [ ] 标记“新增但其他语言完全没有的文件”

## 3. 第 1 批：templates 全量补齐

这批优先级最高，因为缺 template 会直接影响 LLM 功能链可用性。

### 3.1 先补所有语言都缺的新模板

以 `zh-CN/templates` 为基线，逐个核对以下文件是否在所有启用语言目录存在：

- [ ] `roleplay_conversation_turn.txt`
- [ ] `roleplay_conversation_summary.txt`
- [ ] `relation_delta.txt`
- [ ] `random_minor_event_pair.txt`
- [ ] `random_minor_event_solo.txt`

### 3.2 逐语言补齐

#### `static/locales/en-US/templates/`

- [ ] 补齐与 `zh-CN` 缺失对比出来的全部新模板
- [ ] 检查旧文件是否仍使用过时 prompt 结构

#### `static/locales/zh-TW/templates/`

- [ ] 补齐与 `zh-CN` 缺失对比出来的全部新模板
- [ ] 统一繁体术语

#### `static/locales/vi-VN/templates/`

- [ ] 补齐与 `zh-CN` 缺失对比出来的全部新模板
- [ ] 检查修仙术语是否前后一致

#### `static/locales/ja-JP/templates/`

- [ ] 补齐与 `zh-CN` 缺失对比出来的全部新模板
- [ ] 检查敬语、称谓和角色关系表达是否稳定

### 3.3 重点链路验收

- [ ] `ai.txt`
- [ ] `single_choice.txt`
- [ ] `conversation.txt`
- [ ] `mutual_action.txt`
- [ ] `roleplay_conversation_turn.txt`
- [ ] `roleplay_conversation_summary.txt`

## 4. 第 2 批：近期新增功能链路补齐

这批优先补“最近加的功能”，因为最容易只在 `zh-CN` 完整。

### 4.1 roleplay 模式

重点目录：

- `static/locales/<lang>/modules/`
- `web/src/components/game/roleplay/`
- `web/src/components/game/panels/info/components/`
- `src/server/services/roleplay_service.py`
- `src/server/runtime/session.py`

TODO：

- [ ] 检查 roleplay 相关 request/status/error 文案是否全部进入 i18n
- [ ] 检查前端 dock / panel 的按钮、标题、副标题、空态文案
- [ ] 检查交互流里使用的标签和说明是否有硬编码 fallback
- [ ] 检查 conversation summary / choice prompt / action chain 提示是否可翻译

### 4.2 single choice

重点文件：

- `static/locales/<lang>/modules/single_choice.po`
- `static/locales/<lang>/templates/single_choice.txt`
- `src/systems/single_choice/**/*.py`

TODO：

- [ ] 核对 `single_choice.po` 在所有启用语言中的缺口
- [ ] 核对选项标题、说明、fallback 文案
- [ ] 检查 mutual action 接入后的 choice 文案是否全部进入 i18n

### 4.3 conversation / mutual action

重点文件：

- `static/locales/<lang>/modules/mutual_action.po`
- `static/locales/<lang>/templates/conversation.txt`
- `static/locales/<lang>/templates/mutual_action.txt`

TODO：

- [ ] 补齐对话相关系统文案
- [ ] 补齐互动动作反馈与响应标签
- [ ] 核对 relation / story / summary 相关 prompt 文案

### 4.4 事件与摘要

重点文件：

- `static/locales/<lang>/modules/event_content.po`
- `static/locales/<lang>/modules/formatted_strings.po`
- `static/locales/<lang>/modules/execution_results.po`

TODO：

- [ ] 检查事件栏常见文本是否已补齐
- [ ] 检查摘要文本、关系变化文本、执行结果文本
- [ ] 检查格式串占位符一致性

## 5. 第 3 批：前端硬编码清理

目标是让前端用户可见文案真正走 i18n，而不是靠中文/英文 fallback 撑着。

### 5.1 排查范围

- [ ] `web/src/components/**/*.vue`
- [ ] `web/src/stores/**/*.ts`
- [ ] `web/src/api/**/*.ts`
- [ ] `web/src/composables/**/*.ts`

### 5.2 重点模块

- [ ] `RoleplayDock`
- [ ] `RoleplayPanel`
- [ ] `EventPanel`
- [ ] `SystemMenu`
- [ ] 各类 overlay / modal / panel 空态

### 5.3 重点问题类型

- [ ] 中文写死
- [ ] 英文写死
- [ ] store 默认错误文案
- [ ] API 异常 fallback
- [ ] 空态 / loading / disabled 提示
- [ ] 标题和按钮文案未走 key

## 6. 第 4 批：后端硬编码清理

### 6.1 排查范围

- [ ] `src/server/**/*.py`
- [ ] `src/systems/**/*.py`
- [ ] `src/classes/**/*.py`

### 6.2 重点问题类型

- [ ] `HTTPException.detail`
- [ ] 用户可见错误消息
- [ ] 状态提示
- [ ] fallback 默认标题
- [ ] 直接返回前端的描述文本

### 6.3 重点模块

- [ ] roleplay service
- [ ] public v1 query/command
- [ ] single choice engine
- [ ] mutual action / conversation
- [ ] event / relation / story service

## 7. 第 5 批：配置型文本补齐

这批工作量大，但对“世界内容也有多语言”很关键。

### 7.1 `game_configs_modules`

逐类检查：

- [ ] `animal.po`
- [ ] `auxiliary.po`
- [ ] `celestial_phenomenon.po`
- [ ] `city_region.po`
- [ ] `cultivate_region.po`
- [ ] `dynasty.po`
- [ ] `elixir.po`
- [ ] `hidden_domain.po`
- [ ] `lode.po`
- [ ] `manual_effects.po`
- [ ] `material.po`
- [ ] `normal_region.po`
- [ ] `orthodoxy.po`
- [ ] `persona.po`
- [ ] `plant.po`
- [ ] `random_minor_event.po`
- [ ] `root.po`
- [ ] `sect_region.po`
- [ ] `sect.po`
- [ ] `technique.po`
- [ ] `weapon.po`
- [ ] `world_info.po`

### 7.2 `game_configs/*.csv`

- [ ] `given_name.csv`
- [ ] `last_name.csv`

说明：

1. 如果 csv 真源新增字段或内容，先提取，再补翻译。
2. 不要只改 `.po` 而忘了 csv 侧变更链路。

## 8. 第 6 批：构建与测试

### 8.1 构建

- [ ] 如涉及 CSV，运行 `python tools/i18n/extract_csv.py`
- [ ] 运行 `python tools/i18n/build_mo.py`

### 8.2 必跑测试

- [ ] `pytest tests/test_frontend_locales.py`
- [ ] `pytest tests/test_backend_locales.py`

### 8.3 建议跑测试

- [ ] `pytest tests/test_i18n_dynamic.py`
- [ ] `pytest tests/test_i18n_integrity.py`
- [ ] `pytest tests/test_i18n_modules.py`
- [ ] `pytest tests/test_i18n_realm_display.py`
- [ ] `pytest tests/test_runtime_i18n_guards.py`
- [ ] `pytest tests/test_locale_registry_migration.py`
- [ ] `pytest tests/test_effect_desc_i18n.py`

### 8.4 收尾

- [ ] 删除 `i18n_missing_report.md`
- [ ] 确认 `LC_MESSAGES/*.po` / `.mo` 与源文件同步

## 9. 第 7 批：人工验收清单

每个启用语言至少走一轮：

### 9.1 基础 UI

- [ ] 启动游戏
- [ ] 切换语言
- [ ] 检查系统菜单语言入口，保留 `Language` 英文提示
- [ ] 检查主界面基础按钮和常用面板

### 9.2 世界与角色

- [ ] 打开 avatar detail
- [ ] 查看右侧事件栏
- [ ] 检查地图、地区、宗门、物品、境界等常见文本

### 9.3 roleplay 链路

- [ ] 执行一次文本决策
- [ ] 执行一次 choice
- [ ] 执行一次 conversation
- [ ] 检查 interaction stream 的文本是否语言一致
- [ ] 检查右侧事件栏与摘要是否语言一致

### 9.4 存读档

- [ ] 存档
- [ ] 读档
- [ ] 确认语言设置和展示一致

## 10. 推荐的最小落地顺序

如果你不想一次性全仓推进，建议先做这个最小版本：

### 第一阶段

- [ ] 补齐所有 `templates`
- [ ] 补 roleplay / single choice / conversation 相关 `modules/*.po`
- [ ] 清理这条链上的前后端硬编码
- [ ] 跑 locale 测试

### 第二阶段

- [ ] 补配置型文本 `game_configs_modules/*.po`
- [ ] 补姓名与 csv 提取链路
- [ ] 做完整人工 walkthrough

## 11. 建议执行方式

推荐按“语言横切”还是“模块纵切”，取决于你的目标：

### 11.1 如果目标是尽快让一个外语版本可用

先按语言横切：

- [ ] 先补 `en-US`
- [ ] 再补 `zh-TW`
- [ ] 再补 `ja-JP`
- [ ] 最后补 `vi-VN`

### 11.2 如果目标是尽快把新功能链全语言补齐

先按模块纵切：

- [ ] roleplay
- [ ] single choice
- [ ] conversation
- [ ] event / relation / story
- [ ] config content

对当前仓库，我更推荐先按模块纵切，因为最近新增功能链的缺口最集中。

