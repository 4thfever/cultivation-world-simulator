# 新增语言流程

本文档沉淀“如何为仓库新增一门语言”的推荐顺序，适合作为执行清单使用。

适用场景：

- 新增 `new_language_type`，例如 `vi-VN`
- 将一门实验语言提升为正式启用语言
- 检查当前仓库是否已经完成新增语言所需的工程接入

本文档只描述流程，不代表仓库当前已经启用新的语言。

## 0. 先确认当前阶段

仓库默认仍遵守 Phase 1 规则：

- 日常功能开发默认只改 `zh-CN`
- 不要求顺手补全其他语言
- 如果你现在是在“正式新增一门语言”，等同于一次明确的多语言扩展工作，而不是普通功能开发

相关规则来源：

- `.cursor/rules/i18n-phase1.mdc`
- `AGENTS.md`

## 1. 单一真相源：先改语言注册表

新增语言时，第一步永远是修改：

- `static/locales/registry.json`

需要补的核心字段：

```json
{
  "code": "vi-VN",
  "label": "Tiếng Việt",
  "html_lang": "vi",
  "enabled": true
}
```

字段说明：

- `code`: 语言目录名、运行时语言码、存档中的语言码
- `label`: 前端语言菜单显示名
- `html_lang`: 写入前端 `<html lang>` 的值
- `enabled`: 是否启用

注册表中另外三个全局字段也要理解：

- `default_locale`: 默认语言
- `fallback_locale`: 回退语言
- `schema_locale`: 前端 schema 参考语言

注意：

- 不要跳过这一步去直接复制目录或修改前端菜单。
- 不要在脚本、测试、前端运行时代码里重新手写 `zh-CN / zh-TW / en-US`。

## 2. 现在哪些逻辑已经自动识别语言

截至当前仓库状态，以下逻辑已经改成自动从注册表或目录读取语言，不需要在新增语言时再改运行时代码：

- Python 侧语言读取 helper：`src/i18n/locale_registry.py`
- 后端语言切换与默认语言：`src/classes/language.py`
- 后端 i18n 默认/回退语言：`src/i18n/__init__.py`
- 前端语言注册表：`web/src/locales/registry.ts`
- 前端 locale 自动加载：`web/src/locales/index.ts`
- 设置页 `<html lang>` 同步：`web/src/stores/setting.ts`
- 关键 locale 校验测试：
  - `tests/test_frontend_locales.py`
  - `tests/test_backend_locales.py`
  - `tests/test_i18n_modules.py`
  - `tests/test_csv_loading.py`

这意味着：

- 新增语言时，通常不需要再改“前端支持哪些语言”的代码分支。
- 以后主要工作会落在“资源骨架”和“翻译内容”。

## 3. 资源骨架清单

新增语言后，至少需要为该语言补齐以下目录：

- `web/src/locales/<locale>/`
- `static/locales/<locale>/modules/`
- `static/locales/<locale>/game_configs_modules/`
- `static/locales/<locale>/LC_MESSAGES/`
- `static/locales/<locale>/templates/`
- `static/locales/<locale>/game_configs/`

推荐做法：

1. 先复制现有完整语言目录结构
2. 再清理或替换目标语言内容
3. 最后运行构建和校验

不要这样做：

- 先只改语言菜单
- 先只创建一个前端 JSON 文件
- 先只加一个 `modules/ui.po`

因为这样通常会导致运行时能切换语言，但资源并不完整。

## 4. 各类资源分别要补什么

### 4.1 前端 JSON

路径：

- `web/src/locales/<locale>/*.json`

作用：

- 前端界面文案
- 菜单、加载页、游戏面板、LLM 配置页等

要求：

- 所有 locale 目录下 JSON 文件名保持一致
- 同名 JSON 的 key 结构保持一致

### 4.2 后端动态文案 PO

路径：

- `static/locales/<locale>/modules/*.po`

作用：

- Python 中 `t("...")` 的动态文本
- 动作描述、反馈文字、战斗文本、系统提示等

规则：

- 不要直接编辑 `LC_MESSAGES/messages.po`
- 请编辑拆分后的 `modules/*.po`
- `msgid` 必须是英文

### 4.3 CSV 配置翻译 PO

路径：

- `static/locales/<locale>/game_configs_modules/*.po`

作用：

- `static/game_configs/*.csv` 中 `name_id` / `desc_id` 等配置翻译

规则：

- 不要直接编辑 `LC_MESSAGES/game_configs.po`
- 请编辑拆分后的 `game_configs_modules/*.po`

### 4.4 模板文本

路径：

- `static/locales/<locale>/templates/*.txt`

作用：

- LLM 提示词模板
- 宗门思考、宗门决策、随机事件、故事生成等

注意：

- 如果模板缺失，部分逻辑会回退到源语言模板
- 系统能运行，不代表语言体验完整

### 4.5 姓名 CSV

路径：

- `static/locales/<locale>/game_configs/last_name.csv`
- `static/locales/<locale>/game_configs/given_name.csv`

作用：

- 本地化姓名生成

注意：

- `tools/i18n/translate_name.py` 目前是 `zh-CN -> en-US` 的专用脚本
- 它不适合作为任意新语言的通用脚手架
- 新语言通常需要手工准备姓名资源，或单独设计脚本

## 5. 新增语言时的推荐顺序

建议严格按这个顺序做：

1. 更新 `static/locales/registry.json`
2. 复制 `web/src/locales/<source_locale>/` 为 `web/src/locales/<new_locale>/`
3. 复制 `static/locales/<source_locale>/` 为 `static/locales/<new_locale>/`
4. 检查并补齐 `templates/`
5. 检查并补齐 `game_configs/given_name.csv`、`last_name.csv`
6. 运行 `python tools/i18n/build_mo.py`
7. 运行 locale 校验测试
8. 再进入真正的翻译和术语统一工作

如果你只是要做“工程接入 + 骨架跑通”，做到第 7 步通常就够了。

## 6. 推荐参考语言

新增语言时建议先选一个参考源：

- `source_of_truth` 语言：适合做结构对齐与缺失检测
- `schema_locale`：适合做前端类型基准
- `fallback_locale`：适合做回退策略与最小可用文本

实践上通常：

- 结构和 key 对齐以 `source_of_truth` 为准
- 前端 schema 以 `schema_locale` 为准
- 运行时缺失翻译回退以 `fallback_locale` 为准

## 7. 术语表与命名风格

如果这门语言准备长期维护，建议同步更新：

- `docs/glossary.csv`

原因：

- 宗门名、境界名、功法名、地名、属性名需要统一
- 只在 `.po` 里边翻边定术语，后期容易前后不一致

推荐做法：

- 为术语表增加目标语言列
- 先确定高频核心词
- 再开始大规模翻译

## 8. 容易漏掉的点

### 8.1 姓名拼接规则

仓库现在根据语言的 `html_lang` 判断姓名是否采用空格拼接。

含义是：

- 中文、日文、韩文默认更偏向无空格
- 其他语言默认更偏向空格

如果新语言的姓名规则特殊，不适合这个默认策略，需要额外调整。

### 8.2 LLM 模板不完整

很多时候新增语言最容易漏的是：

- `static/locales/<locale>/templates/*.txt`

少了这些文件，游戏不一定报错，但相关生成内容可能退回源语言。

### 8.3 只补了前端，没补后端

常见误区：

- 前端菜单能切换
- 但后端 `t()`、CSV 配置翻译、故事模板仍是旧语言

这会形成“UI 是新语言，游戏内容还是旧语言”的半完成状态。

### 8.4 只补了 PO，没重新构建 MO

修改 `.po` 后必须执行：

```bash
python tools/i18n/build_mo.py
```

否则运行时不会生效。

## 9. 验证命令

至少建议执行：

```bash
python tools/i18n/build_mo.py
python tools/i18n/generate_missing_report.py
pytest tests/test_frontend_locales.py tests/test_backend_locales.py tests/test_i18n_modules.py
pytest tests/test_csv_loading.py tests/test_language.py
cd web && npm run type-check
```

如果本次改动涉及前端显示或设置页，建议再补：

```bash
cd web && npm run test:run -- src/__tests__/stores/setting.test.ts src/__tests__/components/SystemMenu.test.ts
```

## 10. 最小可交付和完整交付

### 最小可交付

满足以下条件即可认为“语言接入完成”：

- 注册表已添加语言
- 前后端能识别该语言
- 资源骨架完整
- 关键校验通过
- 至少存在基本回退策略

### 完整交付

满足以下条件可认为“语言真正可用”：

- 前端 JSON 翻译完整
- 后端 PO 翻译完整
- CSV 配置翻译完整
- 模板翻译完整
- 姓名资源完整
- 术语表已建立
- 已做一轮游戏内体验检查

## 11. 新增语言完成后的自检问题

提交前建议问自己：

- 我是否先改了 `static/locales/registry.json`？
- 我是否补齐了前端和后端的整套目录？
- 我是否遗漏了 `templates/`？
- 我是否处理了姓名资源？
- 我是否重新构建了 `.mo`？
- 我是否运行了 locale 相关测试？
- 我是否把术语表同步到目标语言？

## 12. 当前边界

本文档沉淀的是“新增语言的执行知识”，不负责：

- 自动生成所有翻译
- 自动决定术语风格
- 自动为任意语言生成姓名

如果未来新增脚手架脚本，请优先复用：

- `tools/i18n/locale_registry.py`

并继续保持：

- 语言列表只在 `static/locales/registry.json` 中维护一次
