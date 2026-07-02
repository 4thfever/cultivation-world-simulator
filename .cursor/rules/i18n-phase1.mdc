---
description: Phase 1 日常功能开发时的多语言规则 (默认生效)
globs: *.py, *.vue, *.json, *.po
---

# 多语言开发：Phase 1 规则

我们采用了分阶段的多语言开发模式。目前处于 **Phase 1 (功能开发阶段)**。

1. **只写简体中文**：当添加新功能、新物品、新 UI 且涉及多语言时，**只允许**修改或新增 `zh-CN` 目录下的 `.json` 或 `.po` 文件。
2. **严禁越界**：除非当前任务被明确指定为“进入 Phase 2”“正式补全多语言”“新增语言接入”或同等级别的全链路 i18n 工作，否则**禁止修改任何非 `zh-CN` 语言目录**中的内容。
2.1 **显式例外**：如果当前任务被明确指定为“进入 Phase 2”“正式补全多语言”“新增语言接入”或同等级别的全链路 i18n 工作，则本规则的第 1、2 条可暂时失效；此时应按 `static/locales/registry.json` 中启用语言统一处理，新增语言（如 `fr-FR`）也属于允许范围。
3. **`msgid` 必须是非中文稳定键或英文源文**：`.po` 中的 `msgid` 不得直接使用中文文本；应使用英文源文，或使用类似 `feature_xxx_label`、`tribulation_inner_demon` 这种稳定 key。中文内容应只放在 `msgstr`。
4. **先改模块源文件，不改构建产物**：`static/locales/<lang>/modules/*.po` 与 `static/locales/<lang>/game_configs_modules/*.po` 是日常维护的源文件；`static/locales/<lang>/LC_MESSAGES/messages.po` 与 `static/locales/<lang>/LC_MESSAGES/game_configs.po` 是通过 `python tools/i18n/build_mo.py` 合并生成的构建产物。除非明确在修构建脚本，否则不要直接改 `LC_MESSAGES/*.po`，否则下次构建会被覆盖。
5. **改完源文件后重建**：修改拆分后的 `.po` 文件后，必须执行 `python tools/i18n/build_mo.py`，确保 `LC_MESSAGES/*.po` / `.mo` 与源文件一致。
6. **忽略测试失败**：由于只写了中文，`test_frontend_locales.py` 和 `test_backend_locales.py` 会因为缺少 key 而报错。**请直接忽略这些报错，绝对不要试图去补全其他语言来修复测试！** (这些会在 Phase 2 统一处理)。
7. **非中文目录不能出现中文副本回退**：即使 Phase 1 不要求补齐非 `zh-CN`，也禁止把 `en-US`、`vi-VN`、`ja-JP`、`fr-FR` 等非中文 locale 的模块文件写成中文副本。已有非中文条目若存在，必须保持目标语言；新增中文源词条可以缺失目标语言，但不能用中文 `msgstr` 假装已翻译。
8. **种族与妖族效果属于跨端 i18n 契约**：新增或修改 `static/game_configs/race.csv`、妖族 action、妖族 effect key、角色创建 race 选项时，必须同步考虑后端 `game_configs_modules/race.po` / `modules/race.po` / `modules/yao_actions.po` 与前端创建面板展示。不得在前端写死 `人族/狐族/狼族/鸟族/蛇族/龟族` 作为面向用户的 label。
9. **运行时生成文本与 UI 翻译分开处理**：`backstory`、`thinking`、目标等 LLM/运行时生成文本不会随 UI 语言自动翻译。新增生成文本约束或 prompt 片段时，应走 locale template 或翻译 key，不要在 Python 逻辑中硬编码中文自然语言作为最终用户可见内容。
10. **短槽位翻译要控制长度但不牺牲语义**：为法语、越南语等更容易变长的语言补全或调整翻译时，必须先判断 key 的 UI 容器。`title`、`label`、`tab`、`button`、`badge`、`status`、`*_short`、菜单项、状态栏入口、卡片标题、按钮主文案等短槽位应优先使用简洁自然的译法，避免把完整说明句塞进去；但不得为了变短而变成生硬缩写、错误术语或丢失关键动作。若既需要短标签又需要完整说明，应新增或使用 `*_short` / `*_desc` / `help` 分离，而不是让同一个长翻译兼任所有场景。例如法语里按钮可用 `Démarrer` 而不是 `Démarrer la partie`，状态栏可用 `Persos` / `Rangs` / `Diplomatie`，页面或帮助说明中再使用完整表达；游戏名、模块名、地图名等高频标题应在首屏、状态栏、弹窗 header 中优先采用可容纳的品牌短名或短标题。
