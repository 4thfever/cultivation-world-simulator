# Locale Hardcode Follow-up

本文档用于记录仓库中“剩余硬编码 locale 字符串”的后续清理清单。

目标不是把所有 `zh-CN / zh-TW / en-US` 字面量机械删除，而是分清：

- 哪些属于正常配置或示例，应该保留
- 哪些是测试中的显式样本，可以暂时保留
- 哪些仍然属于技术债，后续应该继续抽象

## 结论概览

当前剩余硬编码 locale 字符串大致分为三类：

1. **应保留**
   - 语言注册表本身
   - 文档示例
   - README 里的语言资源路径
   - 某些明确验证“中文 vs 英文差异”的测试样本
2. **建议继续抽象**
   - 仍在工具脚本中直接写死 `en-US / zh-CN / zh-TW` 作为优先级或 fallback 的逻辑
   - 仍在测试中把“默认语言 / 回退语言”写死，而不是从注册表读取
3. **低优先级**
   - 注释、docstring、教程文本里的旧三语言表述

## A. 应保留的硬编码

### A1. 语言注册表本身

文件：

- `tools/i18n/locales.json`

原因：

- 这是语言列表的单一真相源
- 这里出现 `zh-CN / zh-TW / en-US` 是数据，不是逻辑硬编码

结论：

- **保留**

### A2. 注册表 helper 的默认回退值

文件：

- `tools/i18n/locale_registry.py`

当前情况：

- `get_default_locale()` 和 `get_fallback_locale()` 内部还带有字符串形式的兜底值

原因：

- 当 `locales.json` 缺字段或结构异常时，需要最小安全回退
- 这是容错，不是业务逻辑分支

结论：

- **保留**

建议：

- 可以在注释中明确这是“registry 损坏时的保底值”

### A3. README 资源路径

文件：

- `docs/readme/EN_README.md`
- `docs/readme/ZH-TW_README.md`

原因：

- 这里引用的是语言专属静态资源目录
- 它们不是 i18n 运行时逻辑

结论：

- **保留**

### A4. 文档中的语言示例

文件：

- `docs/i18n-guide.md`
- `docs/frontend-i18n.md`
- `docs/testing.md`
- `docs/i18n-add-locale.md`
- `AGENTS.md`
- `.cursor/rules/i18n-phase1.mdc`
- `.cursor/skills/i18n-development/SKILL.md`
- `.cursor/skills/fill-i18n-phase2/SKILL.md`

原因：

- 这些多为说明性示例、历史背景或当前流程说明
- 不是运行时逻辑

结论：

- **暂时保留**

建议：

- 以后若进入真正的多语言常态阶段，再做一轮文档统一改写

## B. 建议继续抽象的技术债

### B1. `align_po_files.py` 仍写死三语言优先级

文件：

- `tools/i18n/align_po_files.py`

问题点：

- `zh_cn_file = msgid_data[msgid].get('zh-CN', {}).get('file')`
- `en_us_file = loc_data.get('en-US', {}).get('file')`
- `meta_source = loc_data or item['data'].get('en-US') or item['data'].get('zh-CN') or item['data'].get('zh-TW') or {}`

为什么还算技术债：

- 这里不只是示例，而是真正决定 metadata/fallback 来源的逻辑
- 新增第四种语言后，这个脚本仍然在按“英语优先，中文/繁中兜底”的固定链路工作

建议重构：

1. 引入 `get_source_locale()`、`get_fallback_locale()`
2. 再用 `get_locale_codes(enabled_only=False)` 生成优先级链
3. 把 metadata 选择策略改成“当前 locale -> fallback_locale -> source_locale -> 其余 locale”

优先级：

- **高**

### B2. `align_po_files_preview.py` 同样写死三语言优先级

文件：

- `tools/i18n/align_po_files_preview.py`

问题点：

- 注释和逻辑都默认只有 `en-US / zh-CN / zh-TW`
- `zh_cn_file = msgid_data[msgid].get('zh-CN', {}).get('file')`
- `en_us_file = loc_data.get('en-US', {}).get('file')`

建议重构：

- 与 `align_po_files.py` 保持同一套动态优先级策略

优先级：

- **高**

### B3. `translate_name.py` 是英语专用脚本，未抽象成“新增语言策略”

文件：

- `tools/i18n/translate_name.py`

问题点：

- 直接固定输入目录 `zh-CN`
- 直接固定输出目录 `en-US`
- 逻辑是“中文转拼音”，只适合英文姓名文件生成

结论：

- 这不是 bug，但它仍然是**语言特化脚本**

建议处理方式二选一：

1. 明确保留为英语专用脚本，并重命名为更明确的名称，如 `translate_name_en.py`
2. 或抽象成带参数的脚本，例如：
   - `--source-locale`
   - `--target-locale`
   - `--strategy pinyin`

优先级：

- **中高**

## C. 建议继续抽象的测试

这些测试不是运行时问题，但它们仍然对某些具体 locale 有隐式假设。随着语言体系继续扩展，最好逐步整理。

### C1. `tests/test_i18n_modules.py`

问题：

- 仍固定使用 `zh-CN` 验证 `messages.po`
- 翻译断言也直接断中文文本

建议：

- 结构性检查改用 `get_source_locale()`
- 内容性断言如果明确在验证中文源语言，可保留，但注释应写清楚“这是 source locale 样本，不是三语言写死”

优先级：

- **中**

### C2. `tests/test_i18n_dynamic.py`

问题：

- 直接测试 `zh-CN` 与 `en-US` 的日期格式和世界信息差异

判断：

- 这类测试本质上是在验证“中文样式”和“英语样式”的差异，不完全属于坏硬编码

建议：

- 保留测试意图
- 但可以改成：
  - `source_locale` 负责中文样式断言
  - `fallback_locale` 负责英文样式断言

优先级：

- **中**

### C3. `tests/test_effect_desc_i18n.py`

问题：

- 明确使用 `zh-CN` / `en-US`

判断：

- 这是双语表现对照测试，合理

建议：

- 可保持不动
- 若以后 `fallback_locale` 不再是英语，再改为 registry helper

优先级：

- **低到中**

### C4. `tests/test_settings_service.py`

问题：

- 直接断言默认 locale 是 `zh-CN`
- 直接使用 `en-US` 作为新的 `content_locale`

建议：

- 默认值改成 `get_default_locale()`
- 回退语言样本改成 `get_fallback_locale()`

优先级：

- **中高**

### C5. `tests/test_server_binding.py`

问题：

- OmegaConf 示例数据中把 `system.language` 写成 `zh-CN`

判断：

- 这些测试的重点是 host/port 绑定，不是语言行为
- 这里的 locale 值属于无关样本数据

建议：

- 抽成 `default_locale = get_default_locale()`
- 避免将无关样本也写死成中文

优先级：

- **中**

## D. 前端测试中的 locale 字面量

文件分布：

- `web/src/__tests__/stores/setting.test.ts`
- `web/src/__tests__/stores/socket.test.ts`
- `web/src/__tests__/stores/socketMessageRouter.test.ts`
- `web/src/__tests__/components/SystemMenu.test.ts`
- `web/src/__tests__/components/SplashLayer.test.ts`
- `web/src/__tests__/components/LoadingOverlay.test.ts`
- `web/src/__tests__/components/panels/SaveLoadPanel.test.ts`
- `web/src/__tests__/components/game/panels/system/LLMConfigPanel.test.ts`
- `web/src/__tests__/components/game/panels/SectRelationsModal.test.ts`
- `web/src/__tests__/components/game/panels/info/AvatarDetail.test.ts`
- `web/src/__tests__/components/game/panels/info/SectDetail.test.ts`
- `web/src/__tests__/components/game/panels/info/InfoPanelContainer.test.ts`
- `web/src/__tests__/components/game/panels/info/RegionDetail.test.ts`
- `web/src/__tests__/components/game/AnimatedAvatar.test.ts`

判断：

- 多数属于组件级 i18n mock 数据
- 它们不是生产逻辑硬编码
- 但存在重复写 `zh-CN` / `en-US` 的现象

建议：

1. 新建前端测试辅助，如 `src/__tests__/helpers/i18n.ts`
2. 从 `@/locales/registry` 读取：
   - `defaultLocale`
   - `fallbackLocale`
3. 统一生成最小 i18n mock

收益：

- 减少测试样板代码
- 如果默认/回退语言改动，前端单测不需要全量替换字符串

优先级：

- **中**

## E. 注释与说明性残留

以下文件中的 locale 字符串目前主要存在于注释、docstring、教程说明中：

- `src/i18n/__init__.py`
- `src/utils/config.py`
- `web/src/locales/index.ts`

判断：

- 不影响行为
- 但说明文字仍然偏“三语言历史背景”

建议：

- 下次碰到这些文件时顺手改成更通用表述
- 不需要专门开一个改动 PR

优先级：

- **低**

## F. 推荐下一轮执行顺序

如果继续清理，建议按这个顺序做：

1. `tools/i18n/align_po_files.py`
2. `tools/i18n/align_po_files_preview.py`
3. `tests/test_settings_service.py`
4. `tests/test_server_binding.py`
5. `tests/test_i18n_modules.py`
6. 前端测试辅助抽象
7. 注释与文档统一表述

## G. 不建议继续追求“零字面量”

以下情况没必要强行抽掉：

- `locales.json` 中的真实语言数据
- 文档示例里的 `zh-CN / en-US`
- 明确验证中文和英文行为差异的测试样本
- README 中按语言区分的静态资源路径

原则：

- **优先清理行为逻辑中的硬编码**
- **其次清理无关测试数据中的硬编码**
- **最后才是注释和文档示例**
